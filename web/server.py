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
import secrets
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends, Header, Query, Request, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from englisp import parser, canonicalizer, minimizer
from englisp.loader import CURRENT_USER_TIER
from englisp.interpreter import WorldModel, evaluate, evaluate_query_with_bindings
from web import database
import stripe
from datetime import timezone

STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")
STRIPE_PRICE_ID = os.environ.get("STRIPE_PRICE_ID", "price_12345_mock")

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY

def send_account_email(to_email: str, subject: str, text_content: str) -> bool:
    """Dispatches account emails using SMTP if configured, otherwise logs to a file."""
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = os.environ.get("SMTP_PORT", "587")
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASSWORD")
    
    if smtp_host and smtp_user and smtp_pass:
        try:
            smtp_from = os.environ.get("SMTP_FROM_EMAIL", "no-reply@yourdomain.com")
            msg = MIMEText(text_content)
            msg['Subject'] = subject
            msg['From'] = smtp_from
            msg['To'] = to_email
            
            with smtplib.SMTP(smtp_host, int(smtp_port)) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"SMTP Error sending email: {e}")
            # Fall back to local file logging if SMTP fails
            pass
            
    # Local file logging fallback for portable development
    try:
        log_dir = os.path.join(os.path.dirname(__file__), "logs", "emails")
        os.makedirs(log_dir, exist_ok=True)
        filename = f"{to_email.replace('@', '_at_')}_{int(time.time())}.txt"
        filepath = os.path.join(log_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"To: {to_email}\n")
            f.write(f"Subject: {subject}\n")
            f.write(f"Date: {datetime.utcnow().isoformat()}\n")
            f.write("-" * 40 + "\n")
            f.write(text_content)
        # Also print to stdout so it shows up in server logs
        print(f"\n=== [EMAIL DISPATCHED] ===\nTo: {to_email}\nSubject: {subject}\nContent:\n{text_content}\n==========================\n")
        return True
    except Exception as e:
        print(f"Failed to log email to file: {e}")
        return False

from fastapi.middleware.cors import CORSMiddleware

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi.responses import JSONResponse

def anonymous_only_limit_key(request: Request) -> Optional[str]:
    # Bypass rate limits for local development testing
    client_host = request.client.host if request.client else ""
    if client_host in ("127.0.0.1", "localhost", "::1"):
        return None
        
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

origins_env = os.environ.get("ALLOWED_ORIGINS", "*")
origins = [o.strip() for o in origins_env.split(",") if o.strip()] if origins_env != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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

# Instantiate dedicated adventure world model for Text-Adventure minigame
adventure_world_model = WorldModel()

def init_adventure_game():
    adventure_world_model.clear()
    adventure_world_model.add_fact("in", ["hero", "start_room"])
    adventure_world_model.add_fact("is_a", ["wooden_chest", "chest"])
    adventure_world_model.add_fact("is_a", ["metal_gate", "gate"])
    adventure_world_model.add_fact("locked", ["metal_gate"])
    adventure_world_model.add_fact("closed", ["wooden_chest"])
    
    # 1. Opening the chest gives key
    # (=> (open hero wooden_chest) (has hero key))
    adventure_world_model.add_rule(
        ["open", "hero", "wooden_chest"],
        ["has", "hero", "key"]
    )
    # 2. Unlocking gate: has key + unlock -> unlocked
    # (=> (and (has hero key) (unlock hero metal_gate)) (unlocked metal_gate))
    adventure_world_model.add_rule(
        ["and", ["has", "hero", "key"], ["unlock", "hero", "metal_gate"]],
        ["unlocked", "metal_gate"]
    )
    # 3. Escaping: unlocked + exit -> escaped
    # (=> (and (unlocked metal_gate) (exit hero start_room)) (escaped hero))
    adventure_world_model.add_rule(
        ["and", ["unlocked", "metal_gate"], ["exit", "hero", "start_room"]],
        ["escaped", "hero"]
    )

init_adventure_game()

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
            
    if user["tier"] == "admin":
        CURRENT_USER_TIER.set("paid")
    else:
        CURRENT_USER_TIER.set(user["tier"])
        
    if user["quota_used"] >= user["quota_limit"] and user["tier"] != "admin":
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

class ChangePasswordRequest(BaseModel):
    old_password: str = Field(
        ...,
        max_length=100,
        description="The user's current password."
    )
    new_password: str = Field(
        ...,
        max_length=100,
        description="The user's new password (minimum 6 characters)."
    )

class ForgotPasswordRequest(BaseModel):
    email: str = Field(
        ...,
        max_length=100,
        description="The email address to send the recovery passcode to."
    )

class ResetPasswordRequest(BaseModel):
    email: str = Field(
        ...,
        max_length=100,
        description="The user's email address."
    )
    passcode: str = Field(
        ...,
        max_length=10,
        description="The 6-digit recovery passcode."
    )
    new_password: str = Field(
        ...,
        max_length=100,
        description="The new password (minimum 6 characters)."
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
        
    verification_token = secrets.token_hex(32)
    hashed = database.hash_password(password)
    user = database.create_user(email, hashed, verification_token)
    if not user:
        raise HTTPException(status_code=500, detail="Failed to create account.")
        
    # Send verification email
    verify_url = f"{request.base_url}api/auth/verify-email?token={verification_token}"
    email_text = f"Welcome to EngLISP!\n\nPlease verify your email address by clicking the link below:\n\n{verify_url}\n\nRegards,\nThe EngLISP Team"
    send_account_email(user["email"], "Verify Your EngLISP Account", email_text)
    
    return {
        "success": True,
        "message": "Account registered successfully. Please verify your email to log in.",
        "email": user["email"],
        "tier": user["tier"]
    }

@app.get("/api/auth/verify-email", response_class=HTMLResponse)
def api_verify_email(token: str = Query(...)):
    user = database.verify_user_by_token(token)
    if not user:
        return """
        <html>
            <head>
                <title>Email Verification Failed</title>
                <style>
                    body { font-family: sans-serif; text-align: center; padding: 50px; background-color: #0f0a1e; color: #fff; }
                    .card { background: rgba(255,255,255,0.05); padding: 40px; border-radius: 12px; display: inline-block; border: 1px solid rgba(255,255,255,0.1); }
                    h1 { color: #f87171; }
                </style>
            </head>
            <body>
                <div class="card">
                    <h1>Verification Failed</h1>
                    <p>Invalid or expired email verification token.</p>
                </div>
            </body>
        </html>
        """
    return """
    <html>
        <head>
            <title>Email Verified Successfully</title>
            <style>
                body { font-family: sans-serif; text-align: center; padding: 50px; background-color: #0f0a1e; color: #fff; }
                .card { background: rgba(255,255,255,0.05); padding: 40px; border-radius: 12px; display: inline-block; border: 1px solid rgba(255,255,255,0.1); }
                h1 { color: #22d3ee; }
            </style>
        </head>
        <body>
            <div class="card">
                <h1>Verification Successful!</h1>
                <p>Your email has been successfully verified. You can now close this window and log in on the dashboard.</p>
            </div>
        </body>
    </html>
    """

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
        
    if not user.get("is_verified", 0):
        raise HTTPException(status_code=403, detail="Please verify your email address to log in.")
        
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
    stripe_enabled = bool(STRIPE_SECRET_KEY)
    if not user:
        return {
            "authenticated": False,
            "tier": "anonymous_sandbox",
            "quota_limit": 5,
            "quota_used": 0,
            "stripe_enabled": stripe_enabled,
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
        "status": user.get("status"),
        "stripe_enabled": stripe_enabled
    }

@app.post("/api/auth/subscribe")
@limiter.limit("10/minute", key_func=get_remote_address)
def api_subscribe(req: SubscribeRequest, request: Request, user: Optional[dict] = Depends(get_auth_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required to subscribe.")
    
    if STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=400,
            detail="Direct subscription upgrades are disabled. Please use the checkout session redirection endpoint (/api/auth/stripe-checkout) to subscribe."
        )
        
    if req.duration_seconds <= 0:
        updated_user = database.downgrade_user_subscription(user["email"])
        msg = "Subscription cancelled successfully."
    else:
        updated_user = database.subscribe_user(user["email"], req.duration_seconds)
        msg = "Subscription activated successfully."
        
    if not updated_user:
        raise HTTPException(status_code=500, detail="Failed to update subscription.")
    return {
        "success": True,
        "message": msg,
        "tier": updated_user["tier"],
        "quota_limit": updated_user["quota_limit"],
        "subscription_expires_at": updated_user["subscription_expires_at"],
        "status": updated_user["status"]
    }

@app.post("/api/auth/stripe-checkout")
@limiter.limit("5/minute", key_func=get_remote_address)
def api_stripe_checkout(request: Request, user: Optional[dict] = Depends(get_auth_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required to upgrade.")
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=400, detail="Stripe integration is disabled on this server.")
        
    try:
        customer_id = user.get("stripe_customer_id")
        if not customer_id:
            customer = stripe.Customer.create(
                email=user["email"],
                metadata={"user_id": user["id"]}
            )
            customer_id = customer.id
            database.assign_stripe_customer_to_user(user["email"], customer_id)
            
        referrer = request.headers.get("referer")
        origin = referrer if referrer else str(request.base_url)
        
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': STRIPE_PRICE_ID,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=origin + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=origin,
        )
        return {"success": True, "checkout_url": session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/stripe/webhook")
async def stripe_webhook(request: Request):
    if not STRIPE_SECRET_KEY or not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=400, detail="Stripe webhooks are disabled.")
        
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
        
    event_type = event["type"]
    if event_type == "checkout.session.completed":
        session = event["data"]["object"]
        customer_id = session.get("customer")
        subscription_id = session.get("subscription")
        
        try:
            sub = stripe.Subscription.retrieve(subscription_id)
            expires_at = datetime.fromtimestamp(sub.current_period_end, tz=timezone.utc).replace(tzinfo=None).isoformat()
        except Exception:
            expires_at = (datetime.utcnow() + timedelta(days=30)).isoformat()
            
        database.activate_user_subscription_by_stripe(customer_id, subscription_id, expires_at)
        
    elif event_type in ("customer.subscription.deleted", "customer.subscription.updated"):
        subscription = event["data"]["object"]
        status_str = subscription.get("status")
        sub_id = subscription.get("id")
        
        if status_str in ("canceled", "unpaid", "incomplete_expired"):
            database.cancel_user_subscription_by_stripe(sub_id)
        elif event_type == "customer.subscription.updated":
            expires_at = datetime.fromtimestamp(subscription.get("current_period_end"), tz=timezone.utc).replace(tzinfo=None).isoformat()
            conn = database.get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET subscription_expires_at = ? WHERE stripe_subscription_id = ?",
                (expires_at, sub_id)
            )
            conn.commit()
            conn.close()
            
    return {"status": "success"}

@app.post("/api/auth/change-password")
@limiter.limit("10/minute", key_func=get_remote_address)
def api_change_password(req: ChangePasswordRequest, request: Request, user: Optional[dict] = Depends(get_auth_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required to change password.")
    if not user["password_hash"]:
        raise HTTPException(status_code=400, detail="OAuth/API-only accounts cannot change passwords.")
    
    if not database.verify_password(req.old_password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Incorrect old password.")
        
    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters.")
        
    new_hash = database.hash_password(req.new_password)
    success = database.update_user_password(user["email"], new_hash)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update password.")
        
    return {"success": True, "message": "Password updated successfully."}

@app.post("/api/auth/forgot-password")
@limiter.limit("5/minute", key_func=get_remote_address)
def api_forgot_password(req: ForgotPasswordRequest, request: Request):
    email = req.email.strip()
    user = database.get_user_by_email(email)
    if not user:
        return {"success": True, "message": "If the email is registered, a recovery passcode has been sent."}
        
    passcode = "".join(secrets.choice("0123456789") for _ in range(6))
    expires_at = (datetime.utcnow() + timedelta(minutes=15)).isoformat()
    database.set_user_reset_token(email, passcode, expires_at)
    
    email_text = f"Hello,\n\nYou have requested a password recovery passcode for your EngLISP account.\n\nYour temporary recovery passcode is:\n\n{passcode}\n\nThis code will expire in 15 minutes.\n\nRegards,\nThe EngLISP Team"
    send_account_email(user["email"], "EngLISP Password Recovery Code", email_text)
    
    return {"success": True, "message": "If the email is registered, a recovery passcode has been sent."}

@app.post("/api/auth/reset-password")
@limiter.limit("5/minute", key_func=get_remote_address)
def api_reset_password(req: ResetPasswordRequest, request: Request):
    email = req.email.strip()
    passcode = req.passcode.strip()
    new_password = req.new_password
    
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters.")
        
    hashed = database.hash_password(new_password)
    success = database.reset_user_password_by_token(email, passcode, hashed)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid passcode or passcode has expired.")
        
    return {"success": True, "message": "Password reset successfully. You can now log in."}

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

        # Compile S-expression to Database queries (SQL / Cypher)
        from englisp.db_compiler import compile_to_sql, compile_to_cypher
        compiled_sql = compile_to_sql(minimalist_sexpr)
        compiled_cypher = compile_to_cypher(minimalist_sexpr)

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
                "compiled_sql": compiled_sql,
                "compiled_cypher": compiled_cypher,
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

        # Compile S-expression to Database queries (SQL / Cypher)
        from englisp.db_compiler import compile_to_sql, compile_to_cypher
        compiled_sql = compile_to_sql(min_sexpr)
        compiled_cypher = compile_to_cypher(min_sexpr)

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
                "compiled_sql": compiled_sql,
                "compiled_cypher": compiled_cypher,
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

        # Compile S-expression to Database queries (SQL / Cypher)
        from englisp.db_compiler import compile_to_sql, compile_to_cypher
        compiled_sql = compile_to_sql(minimalist_sexpr)
        compiled_cypher = compile_to_cypher(minimalist_sexpr)

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
                "compiled_sql": compiled_sql,
                "compiled_cypher": compiled_cypher,
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

@app.post("/api/adventure/command")
@limiter.limit("15/minute")
def adventure_command(req: ParseRequest, request: Request):
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Command cannot be empty.")
    try:
        lang = parser.detect_language(text)
        xbar_node = parser.parse(text, lang=lang)
        englisp_sexpr = canonicalizer.xbar_to_sexpr(xbar_node, lang=lang)
        minimalist_sexpr = minimizer.minimize_sexpr(englisp_sexpr)
    except Exception as e:
        return {
            "success": False,
            "message": "I didn't understand that command. Try using clear sentences like 'The hero opens the wooden_chest' or 'The hero takes the key'."
        }

    if not isinstance(minimalist_sexpr, list) or len(minimalist_sexpr) == 0:
        return {
            "success": False,
            "message": "Invalid command structure."
        }
    
    op = minimalist_sexpr[0]
    if op in ("and", "or", "not", "assert", "tell", "=>"):
        return {
            "success": False,
            "message": "System commands are not allowed in the adventure game."
        }
    
    # Normalize operator to base forms
    if op == "opens":
        op = "open"
    elif op == "unlocks":
        op = "unlock"
    elif op in ("exits", "exist"):
        op = "exit"
        
    from englisp.interpreter import simplify_argument
    args = [simplify_argument(x) for x in minimalist_sexpr[1:]]
    
    # Perform action
    adventure_world_model.add_fact(op, args)
    
    # Query logic bindings
    chest_opened = len(evaluate_query_with_bindings(["open", "hero", "wooden_chest"], adventure_world_model, [{}])) > 0
    has_key = len(evaluate_query_with_bindings(["has", "hero", "key"], adventure_world_model, [{}])) > 0
    gate_unlocked = len(evaluate_query_with_bindings(["unlocked", "metal_gate"], adventure_world_model, [{}])) > 0
    escaped = len(evaluate_query_with_bindings(["escaped", "hero"], adventure_world_model, [{}])) > 0

    message = ""
    if op == "open" and len(args) > 1 and args[1] == "wooden_chest":
        message = "You open the wooden chest. Inside, you find a golden key! You take it."
    elif op == "unlock" and len(args) > 1 and args[1] == "metal_gate":
        if has_key:
            message = "You insert the golden key into the heavy iron lock of the metal gate. With a loud click, the gate unlocks!"
        else:
            adventure_world_model.remove_fact(op, args)
            message = "The metal gate is locked. You need a key to unlock it."
    elif op == "exit" and len(args) > 1 and args[1] == "start_room":
        if gate_unlocked:
            message = "You push open the heavy metal gate and step out of the room into the bright sunshine. You have escaped!"
        else:
            adventure_world_model.remove_fact(op, args)
            message = "The metal gate is locked and blocks the exit. You cannot leave yet."
    else:
        message = f"You perform: {op}({', '.join(args)}). But nothing happens."

    return {
        "success": True,
        "command_parsed": canonicalizer.sexpr_to_string(minimalist_sexpr),
        "message": message,
        "state": {
            "chest_opened": chest_opened,
            "has_key": has_key,
            "gate_unlocked": gate_unlocked,
            "escaped": escaped
        }
    }

@app.post("/api/adventure/reset")
def adventure_reset():
    init_adventure_game()
    return {
        "success": True,
        "message": "You find yourself trapped inside a dark stone room. In the corner lies a closed wooden chest. Ahead is a locked metal gate blocking the exit.",
        "state": {
            "chest_opened": False,
            "has_key": False,
            "gate_unlocked": False,
            "escaped": False
        }
    }

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
