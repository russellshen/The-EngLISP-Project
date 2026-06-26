# Copyright (c) 2026 Russell Shen. All rights reserved.
#
# This source code is licensed under the Creative Commons Attribution-NonCommercial-NoDerivatives 
# 4.0 International (CC BY-NC-ND 4.0) license. 
#
# Commercial use, proprietary use, or use in closed-source or revenue-generating projects 
# is strictly prohibited under this license.
#
# For commercial licensing inquiries, please contact:
# Russell Shen (russellshen7@gmail.com)
#
# Licensing terms, scope, and compensation are subject to separate negotiation.
#
# Reference the footer section of any of the 4 .md files (README.md, SPECIFICATION.md,
# USE_CASES.md, LEXICAL_STRATEGIES.md) in the project's root directory for full licensing details.
#
# I am the sole original creator of the EngLISP project (around August 2025), and did not rely on
# the resources of any academic institution or private individual to develop it.

import os
import time
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, Header, Query, Request, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from englisp import parser, canonicalizer, minimizer
from englisp.loader import CURRENT_USER_TIER
from englisp.interpreter import WorldModel, evaluate
from web import database

from fastapi.middleware.cors import CORSMiddleware

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi.responses import JSONResponse

def anonymous_only_limit_key(request: Request) -> Optional[str]:
    x_api_key = request.headers.get("X-API-Key")
    api_key = request.query_params.get("api_key")
    if x_api_key or api_key:
        return None
    return get_remote_address(request)

limiter = Limiter(key_func=anonymous_only_limit_key)

app = FastAPI(
    title="EngLISP Bridge Server",
    description="A bidirectional bridge between natural language and computation with identity management.",
    version="1.1.0"
)

app.state.limiter = limiter

def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    endpoint_path = request.url.path
    if "/api/auth/" in endpoint_path:
        detail = "Too many requests. Please try again later."
    else:
        detail = "Sandbox rate limit exceeded (Max 5 requests per minute without an account). Please register for a free account to get 100 queries/month."
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": detail}
    )

app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

def check_sexpr_depth(s: str, max_depth: int = 50) -> bool:
    """Checks if the nesting depth of parentheses in the string exceeds max_depth."""
    depth = 0
    for char in s:
        if char == '(':
            depth += 1
            if depth > max_depth:
                return False
        elif char == ')':
            depth -= 1
    return True

# Instantiate global world state for S-expression interpreter
world_model = WorldModel()

# Initialize SQLite database on startup
@app.on_event("startup")
def startup_event():
    database.db_init()

# Authentication Dependency
def get_auth_user(
    request: Request,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    api_key: Optional[str] = Query(None)
) -> Optional[dict]:
    """
    Dependency that extracts the API Key from headers or query parameters.
    If no API key is provided, rate-limits the user as an anonymous sandbox visitor.
    If a key is provided, validates it and checks the usage quota.
    """
    from fastapi.params import Param
    if isinstance(x_api_key, Param):
        x_api_key = None
    if isinstance(api_key, Param):
        api_key = None
        
    key = x_api_key or api_key
    if not key:
        CURRENT_USER_TIER.set("free")
        return None # Anonymous Sandbox user
        
    user = database.get_user_by_api_key(key)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key."
        )
        
    # Check subscription expiration
    if user["tier"] == "paid" and user["subscription_expires_at"]:
        now = datetime.utcnow().isoformat()
        if now > user["subscription_expires_at"]:
            # Auto downgrade
            user = database.downgrade_user_subscription(user["email"])
            
    CURRENT_USER_TIER.set(user["tier"])
        
    if user["quota_used"] >= user["quota_limit"]:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"API Quota exceeded ({user['quota_used']}/{user['quota_limit']}). Please upgrade your account."
        )
        
    return user

# Request and Response schemas
class ParseRequest(BaseModel):
    text: str = Field(
        ...,
        max_length=300,
        description="Natural language sentence to parse. Maximum 300 characters.",
        examples=["The dog chased the cat."]
    )
    lang: Optional[str] = Field(
        None,
        description="Optional language override ('en' for English, 'fr' for French). Defaults to auto-detection.",
        examples=["en"]
    )

class MinimaLISTRequest(BaseModel):
    minimalist: str = Field(
        ...,
        max_length=1000,
        description="MinimaLIST S-expression string to generate from. Maximum 1000 characters.",
        examples=["(chased (dog the) (cat the))"]
    )
    lang: Optional[str] = Field(
        None,
        description="Target generation language ('en' for English, 'fr' for French). Defaults to 'en'.",
        examples=["fr"]
    )

class EngLISPRequest(BaseModel):
    englisp: str = Field(
        ...,
        max_length=1000,
        description="EngLISP S-expression string to generate from or compile. Maximum 1000 characters.",
        examples=["(chased (dog the) (cat the))"]
    )
    lang: Optional[str] = Field(
        None,
        description="Target generation language ('en' for English, 'fr' for French). Defaults to 'en'.",
        examples=["en"]
    )

class InterpretRequest(BaseModel):
    expr: str = Field(
        ...,
        max_length=1000,
        description="EngLISP assertion or query S-expression. Maximum 1000 characters.",
        examples=["(chased dog cat)"]
    )

class CompileRequest(BaseModel):
    expr: str = Field(
        ...,
        max_length=1000,
        description="EngLISP S-expression to compile to target dialect. Maximum 1000 characters.",
        examples=["(chased (dog the) (cat the))"]
    )
    target: str = Field(
        "common-lisp",
        description="Target compilation dialect ('common-lisp', 'scheme', 'clojure', 'sql', 'cypher', or 'mongodb').",
        examples=["sql"]
    )

class AuthRequest(BaseModel):
    email: str = Field(
        ...,
        max_length=100,
        description="User email address for account registration/login.",
        examples=["user@example.com"]
    )
    password: str = Field(
        ...,
        max_length=100,
        description="User password (minimum 6 characters).",
        examples=["password123"]
    )

class SubscribeRequest(BaseModel):
    duration_seconds: int = Field(
        2592000,
        description="Subscription duration in seconds (default 30 days = 2592000).",
        examples=[60]
    )

# --- Authentication & User Endpoints ---

@app.post("/api/auth/register")
@limiter.limit("10/minute", key_func=get_remote_address)
def api_register(req: AuthRequest, request: Request):
    email = req.email.strip()
    password = req.password
    
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid email address.")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")
        
    existing = database.get_user_by_email(email)
    if existing:
        raise HTTPException(status_code=400, detail="Email is already registered.")
        
    hashed = database.hash_password(password)
    user = database.create_user(email, hashed)
    if not user:
        raise HTTPException(status_code=500, detail="Failed to create account.")
        
    return {
        "success": True,
        "message": "Account registered successfully.",
        "api_key": user["api_key"],
        "email": user["email"],
        "tier": user["tier"],
        "quota_limit": user["quota_limit"],
        "quota_used": user["quota_used"]
    }

@app.post("/api/auth/login")
@limiter.limit("10/minute", key_func=get_remote_address)
def api_login(req: AuthRequest, request: Request):
    email = req.email.strip()
    password = req.password
    
    user = database.get_user_by_email(email)
    if not user or not user["password_hash"]:
        raise HTTPException(status_code=400, detail="Invalid email or password.")
        
    if not database.verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Invalid email or password.")
        
    return {
        "success": True,
        "message": "Logged in successfully.",
        "api_key": user["api_key"],
        "email": user["email"],
        "tier": user["tier"],
        "quota_limit": user["quota_limit"],
        "quota_used": user["quota_used"]
    }

@app.get("/api/auth/me")
@limiter.limit("10/minute", key_func=get_remote_address)
def api_me(request: Request, user: Optional[dict] = Depends(get_auth_user)):
    if not user:
        return {
            "authenticated": False,
            "tier": "anonymous_sandbox",
            "quota_limit": 5,
            "quota_used": 0,
            "message": "Browsing under Anonymous Sandbox rate limits."
        }
    return {
        "authenticated": True,
        "email": user["email"],
        "tier": user["tier"],
        "quota_limit": user["quota_limit"],
        "quota_used": user["quota_used"],
        "api_key": user["api_key"],
        "subscription_expires_at": user.get("subscription_expires_at"),
        "status": user.get("status")
    }

@app.post("/api/auth/subscribe")
@limiter.limit("10/minute", key_func=get_remote_address)
def api_subscribe(req: SubscribeRequest, request: Request, user: Optional[dict] = Depends(get_auth_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required to subscribe.")
    updated_user = database.subscribe_user(user["email"], req.duration_seconds)
    if not updated_user:
        raise HTTPException(status_code=500, detail="Failed to activate subscription.")
    return {
        "success": True,
        "message": "Subscription activated successfully.",
        "tier": updated_user["tier"],
        "quota_limit": updated_user["quota_limit"],
        "subscription_expires_at": updated_user["subscription_expires_at"],
        "status": updated_user["status"]
    }

# --- Core EngLISP Pipeline API Endpoints ---

@app.post("/api/parse")
@limiter.limit("5/minute")
def api_parse(req: ParseRequest, request: Request, user: Optional[dict] = Depends(get_auth_user)):
    CURRENT_USER_TIER.set(user["tier"] if user else "free")
    try:
        text = req.text.strip()
        if not text:
            raise HTTPException(status_code=400, detail="Text cannot be empty.")
        
        # Stage 1 -> Stage 2 (NL to X-bar Tree)
        lang = req.lang
        if not lang or lang == "auto":
            lang = parser.detect_language(text)
            
        xbar_node = parser.parse(text, lang=lang)
        xbar_json = xbar_node.to_dict()
        xbar_text = xbar_node.pretty_print()

        # Stage 2 -> Stage 3 (X-bar to rotated S-expression)
        englisp_sexpr = canonicalizer.xbar_to_sexpr(xbar_node, lang=lang)
        englisp_str = canonicalizer.sexpr_to_string(englisp_sexpr)

        # Stage 3 -> Stage 4 (EngLISP to MinimaLIST)
        minimalist_sexpr = minimizer.minimize_sexpr(englisp_sexpr)
        minimalist_str = canonicalizer.sexpr_to_string(minimalist_sexpr)

        # Auto-assert to world model if it's a valid relational fact (verb or property first)
        from englisp.interpreter import simplify_argument
        if isinstance(minimalist_sexpr, list) and len(minimalist_sexpr) > 0:
            pred = minimalist_sexpr[0]
            if isinstance(pred, str) and pred not in ("and", "or", "not", "assert", "tell"):
                args = [simplify_argument(x) for x in minimalist_sexpr[1:]]
                world_model.add_fact(pred, args)

        # Increment authenticated user quota
        if user:
            database.increment_user_quota(user["id"])

        return {
            "success": True,
            "pipeline": {
                "stage1_nl": text,
                "stage2_xbar_json": xbar_json,
                "stage2_xbar_text": xbar_text,
                "stage3_englisp": englisp_str,
                "stage4_minimalist": minimalist_str,
                "detected_lang": lang
            }
        }
    except parser.EngLISPParseError as e:
        return {
            "success": False,
            "error_type": "parse_diagnostics",
            "message": str(e),
            "diagnostics": e.diagnostics
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/generate-from-minimalist")
@limiter.limit("5/minute")
def api_generate_from_minimalist(req: MinimaLISTRequest, request: Request, user: Optional[dict] = Depends(get_auth_user)):
    CURRENT_USER_TIER.set(user["tier"] if user else "free")
    min_str = req.minimalist.strip()
    if not min_str:
        raise HTTPException(status_code=400, detail="MinimaLIST S-expression cannot be empty.")
    if not check_sexpr_depth(min_str):
        raise HTTPException(status_code=400, detail="S-expression nesting depth exceeds limit of 50.")
    try:
        lang = req.lang
        if not lang or lang == "auto":
            lang = "en"

        min_sexpr = canonicalizer.parse_sexpr(min_str)
        englisp_sexpr = minimizer.expand_sexpr(min_sexpr)
        englisp_str = canonicalizer.sexpr_to_string(englisp_sexpr)

        xbar_node = canonicalizer.sexpr_to_xbar(englisp_sexpr, lang=lang)
        xbar_json = xbar_node.to_dict()
        xbar_text = xbar_node.pretty_print()
        generated_nl = parser.generate(xbar_node, lang=lang)

        if user:
            database.increment_user_quota(user["id"])

        return {
            "success": True,
            "pipeline": {
                "stage4_minimalist": min_str,
                "stage3_englisp": englisp_str,
                "stage2_xbar_json": xbar_json,
                "stage2_xbar_text": xbar_text,
                "stage1_nl": generated_nl,
                "detected_lang": lang
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/generate-from-englisp")
@limiter.limit("5/minute")
def api_generate_from_englisp(req: EngLISPRequest, request: Request, user: Optional[dict] = Depends(get_auth_user)):
    CURRENT_USER_TIER.set(user["tier"] if user else "free")
    el_str = req.englisp.strip()
    if not el_str:
        raise HTTPException(status_code=400, detail="EngLISP S-expression cannot be empty.")
    if not check_sexpr_depth(el_str):
        raise HTTPException(status_code=400, detail="S-expression nesting depth exceeds limit of 50.")
    try:
        lang = req.lang
        if not lang or lang == "auto":
            lang = "en"

        el_sexpr = canonicalizer.parse_sexpr(el_str)
        xbar_node = canonicalizer.sexpr_to_xbar(el_sexpr, lang=lang)
        xbar_json = xbar_node.to_dict()
        xbar_text = xbar_node.pretty_print()
        generated_nl = parser.generate(xbar_node, lang=lang)

        minimalist_sexpr = minimizer.minimize_sexpr(el_sexpr)
        minimalist_str = canonicalizer.sexpr_to_string(minimalist_sexpr)

        if user:
            database.increment_user_quota(user["id"])

        return {
            "success": True,
            "pipeline": {
                "stage3_englisp": el_str,
                "stage2_xbar_json": xbar_json,
                "stage2_xbar_text": xbar_text,
                "stage1_nl": generated_nl,
                "stage4_minimalist": minimalist_str,
                "detected_lang": lang
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/world")
@limiter.limit("5/minute")
def get_world(request: Request, user: Optional[dict] = Depends(get_auth_user)):
    # Simple state display does not decrement quota but checks general auth
    return {"facts": [list(f) for f in world_model.get_all_facts()]}

@app.get("/api/world/export")
@limiter.limit("5/minute")
def export_world_rdf(request: Request, user: Optional[dict] = Depends(get_auth_user)):
    from fastapi import Response
    facts = world_model.get_all_facts()
    
    lines = []
    lines.append("@prefix : <http://englisp.org/schema#> .")
    lines.append("@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .")
    lines.append("")
    
    for idx, fact in enumerate(facts):
        pred = fact[0]
        args = fact[1:]
        
        def fmt_res(val):
            val_str = str(val).strip()
            if val_str.isalnum():
                return f":{val_str}"
            escaped = val_str.replace('"', '\\"')
            return f'"{escaped}"'
            
        if len(args) == 1:
            subj = fmt_res(args[0])
            lines.append(f"{subj} a :{pred} .")
        elif len(args) == 2:
            subj = fmt_res(args[0])
            obj = fmt_res(args[1])
            lines.append(f"{subj} :{pred} {obj} .")
        else:
            rel_uri = f":relation_{idx}"
            lines.append(f"{rel_uri} a :Relation ;")
            lines.append(f"    :type :{pred} ;")
            for i, arg in enumerate(args):
                val = fmt_res(arg)
                lines.append(f"    :arg{i} {val} ;")
            if lines:
                lines[-1] = lines[-1].rstrip(" ;") + " ."
                
    turtle_content = "\n".join(lines)
    return Response(content=turtle_content, media_type="text/turtle")

@app.post("/api/interpret")
@limiter.limit("5/minute")
def interpret_sexpr(req: InterpretRequest, request: Request, user: Optional[dict] = Depends(get_auth_user)):
    CURRENT_USER_TIER.set(user["tier"] if user else "free")
    expr_str = req.expr.strip()
    if not expr_str:
        raise HTTPException(status_code=400, detail="Expression cannot be empty.")
    if not check_sexpr_depth(expr_str):
        raise HTTPException(status_code=400, detail="S-expression nesting depth exceeds limit of 50.")
    try:
        expr = canonicalizer.parse_sexpr(expr_str)
        result = evaluate(expr, world_model)
        
        if user:
            database.increment_user_quota(user["id"])
            
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/world/reset")
@limiter.limit("5/minute")
def reset_world(request: Request, user: Optional[dict] = Depends(get_auth_user)):
    world_model.clear()
    if user:
        database.increment_user_quota(user["id"])
    return {"success": True, "message": "World model reset successfully."}

@app.post("/api/compile")
@limiter.limit("5/minute")
def compile_endpoint(req: CompileRequest, request: Request, user: Optional[dict] = Depends(get_auth_user)):
    CURRENT_USER_TIER.set(user["tier"] if user else "free")
    expr_str = req.expr.strip()
    if not expr_str:
        raise HTTPException(status_code=400, detail="Expression cannot be empty.")
    if not check_sexpr_depth(expr_str):
        raise HTTPException(status_code=400, detail="S-expression nesting depth exceeds limit of 50.")
    try:
        wrapped = f"({expr_str})"
        expressions = canonicalizer.parse_sexpr(wrapped)
        
        from englisp.compiler import compile_program
        compiled_code = compile_program(expressions, target=req.target)
        
        if user:
            database.increment_user_quota(user["id"])
            
        return {"success": True, "code": compiled_code}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Setup static files directory path
static_dir = os.path.join(os.path.dirname(__file__), "static")

# Serve index.html at root "/"
@app.get("/")
def serve_index():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "EngLISP Dashboard frontend files missing. Please build web/static/index.html"}

# Mount other static files under "/"
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir), name="static")
