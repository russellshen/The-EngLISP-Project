# Copyright (c) 2026 Russell Shen. All rights reserved.
#
# This source code is licensed under the Creative Commons Attribution-NonCommercial-NoDerivatives 
# 4.0 International (CC BY-NC-ND 4.0) license. 

import os
import pytest
from fastapi.testclient import TestClient
from web import database
from web.server import app

@pytest.fixture(autouse=True)
def setup_test_db():
    db_path = os.path.join(os.path.dirname(database.__file__), "users.db")
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except PermissionError:
            pass
    database.db_init()
    yield
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except PermissionError:
            pass

def test_email_verification_lifecycle():
    client = TestClient(app)
    
    # 1. Register a user (should trigger verification email)
    reg_response = client.post(
        "/api/auth/register",
        json={"email": "newuser@example.com", "password": "password123"}
    )
    assert reg_response.status_code == 200
    assert "Please verify your email" in reg_response.json()["message"]
    
    # Verify database entry has is_verified = 0 and verification_token set
    user = database.get_user_by_email("newuser@example.com")
    assert user is not None
    assert user["is_verified"] == 0
    assert user["verification_token"] is not None
    token = user["verification_token"]
    
    # 2. Attempt login before verifying (should raise 403)
    login_fail = client.post(
        "/api/auth/login",
        json={"email": "newuser@example.com", "password": "password123"}
    )
    assert login_fail.status_code == 403
    assert "Please verify your email address" in login_fail.json()["detail"]
    
    # 3. Verify email with wrong token (should fail)
    verify_fail = client.get("/api/auth/verify-email?token=wrongtoken")
    assert verify_fail.status_code == 200
    assert "Verification Failed" in verify_fail.text
    
    # 4. Verify email with correct token (should succeed)
    verify_ok = client.get(f"/api/auth/verify-email?token={token}")
    assert verify_ok.status_code == 200
    assert "Verification Successful" in verify_ok.text
    
    # Check db is updated
    user_verified = database.get_user_by_email("newuser@example.com")
    assert user_verified["is_verified"] == 1
    assert user_verified["verification_token"] is None
    
    # 5. Log in after verification (should succeed)
    login_ok = client.post(
        "/api/auth/login",
        json={"email": "newuser@example.com", "password": "password123"}
    )
    assert login_ok.status_code == 200
    assert login_ok.json()["success"] is True
    assert "api_key" in login_ok.json()

def test_password_recovery_passcode_lifecycle():
    client = TestClient(app)
    
    # Register and verify user
    client.post("/api/auth/register", json={"email": "forgotuser@example.com", "password": "password123"})
    user = database.get_user_by_email("forgotuser@example.com")
    database.verify_user_by_token(user["verification_token"])
    
    # 1. Trigger forgot password
    forgot_res = client.post("/api/auth/forgot-password", json={"email": "forgotuser@example.com"})
    assert forgot_res.status_code == 200
    assert "recovery passcode has been sent" in forgot_res.json()["message"]
    
    # Fetch passcode from database
    user_with_token = database.get_user_by_email("forgotuser@example.com")
    assert user_with_token["reset_token"] is not None
    passcode = user_with_token["reset_token"]
    
    # 2. Reset password with wrong passcode (should fail)
    reset_fail = client.post(
        "/api/auth/reset-password",
        json={"email": "forgotuser@example.com", "passcode": "000000", "new_password": "newpassword123"}
    )
    assert reset_fail.status_code == 400
    assert "Invalid passcode" in reset_fail.json()["detail"]
    
    # 3. Reset password with correct passcode (should succeed)
    reset_ok = client.post(
        "/api/auth/reset-password",
        json={"email": "forgotuser@example.com", "passcode": passcode, "new_password": "newsecurepassword123"}
    )
    assert reset_ok.status_code == 200
    assert "Password reset successfully" in reset_ok.json()["message"]
    
    # Check database token reset
    user_reset = database.get_user_by_email("forgotuser@example.com")
    assert user_reset["reset_token"] is None
    assert database.verify_password("newsecurepassword123", user_reset["password_hash"])
    
    # 4. Attempt login with new password (should succeed)
    login_new = client.post(
        "/api/auth/login",
        json={"email": "forgotuser@example.com", "password": "newsecurepassword123"}
    )
    assert login_new.status_code == 200
