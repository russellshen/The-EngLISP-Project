# Copyright (c) 2026 Russell Shen. All rights reserved.
#
# This source code is licensed under the Creative Commons Attribution-NonCommercial-NoDerivatives 
# 4.0 International (CC BY-NC-ND 4.0) license. 

import pytest
from pydantic import ValidationError
from fastapi import HTTPException

from web.server import (
    ParseRequest,
    MinimaLISTRequest,
    EngLISPRequest,
    InterpretRequest,
    CompileRequest,
    AuthRequest,
    SubscribeRequest,
    check_sexpr_depth,
    api_generate_from_minimalist,
    api_generate_from_englisp,
    interpret_sexpr,
    compile_endpoint
)

def test_sexpr_depth_checker():
    # 1. Valid nesting depth (under 50)
    valid_expr = "(" * 10 + "apple" + ")" * 10
    assert check_sexpr_depth(valid_expr) is True

    # 2. Exceeds limit (51 nesting levels)
    invalid_expr = "(" * 51 + "apple" + ")" * 51
    assert check_sexpr_depth(invalid_expr) is False

def test_pydantic_length_constraints():
    # 1. ParseRequest text limit (max 300)
    ParseRequest(text="a" * 300) # Should pass
    with pytest.raises(ValidationError):
        ParseRequest(text="a" * 301)

    # 2. S-expression input limits (max 1000)
    MinimaLISTRequest(minimalist="a" * 1000) # Should pass
    with pytest.raises(ValidationError):
        MinimaLISTRequest(minimalist="a" * 1001)

    EngLISPRequest(englisp="a" * 1000) # Should pass
    with pytest.raises(ValidationError):
        EngLISPRequest(englisp="a" * 1001)

    InterpretRequest(expr="a" * 1000) # Should pass
    with pytest.raises(ValidationError):
        InterpretRequest(expr="a" * 1001)

    CompileRequest(expr="a" * 1000) # Should pass
    with pytest.raises(ValidationError):
        CompileRequest(expr="a" * 1001)

    # 3. AuthRequest limits (max 100)
    AuthRequest(email="a" * 100, password="p" * 100) # Should pass
    with pytest.raises(ValidationError):
        AuthRequest(email="a" * 101, password="password")
    with pytest.raises(ValidationError):
        AuthRequest(email="user@example.com", password="p" * 101)

def test_endpoint_depth_exceptions():
    from fastapi.testclient import TestClient
    from web.server import app
    client = TestClient(app)
    
    deep_expr = "(" * 51 + "test" + ")" * 51
    
    # 1. generate-from-minimalist
    response = client.post("/api/generate-from-minimalist", json={"minimalist": deep_expr})
    assert response.status_code == 400
    assert "depth" in response.json()["detail"]
    
    # 2. generate-from-englisp
    response = client.post("/api/generate-from-englisp", json={"englisp": deep_expr})
    assert response.status_code == 400
    assert "depth" in response.json()["detail"]
    
    # 3. interpret
    response = client.post("/api/interpret", json={"expr": deep_expr})
    assert response.status_code == 400
    assert "depth" in response.json()["detail"]
    
    # 4. compile
    response = client.post("/api/compile", json={"expr": deep_expr, "target": "common-lisp"})
    assert response.status_code == 400
    assert "depth" in response.json()["detail"]
