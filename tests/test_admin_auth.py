# Copyright (c) 2026 Russell Shen. All rights reserved.
#
# This source code is licensed under the Creative Commons Attribution-NonCommercial-NoDerivatives 
# 4.0 International (CC BY-NC-ND 4.0) license. 

import os
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from web import database
from web.server import app, get_auth_user

class MockClient:
    def __init__(self, host: str):
        self.host = host

class MockRequest:
    def __init__(self, host: str = "127.0.0.1"):
        self.client = MockClient(host)
        self.headers = {}
        self.query_params = {}

@pytest.fixture(autouse=True)
def setup_test_db():
    # Set up a test database file
    db_path = os.path.join(os.path.dirname(database.__file__), "users.db")
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except PermissionError:
            pass
    database.db_init()
    yield
    # Clean up test database
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except PermissionError:
            pass

def test_admin_bootstrapping():
    # Verify admin user exists on startup
    admin = database.get_user_by_email("admin@englisp.com")
    assert admin is not None
    assert admin["tier"] == "admin"
    assert admin["quota_limit"] == 999999
    assert admin["status"] == "active"
    assert database.verify_password("adminpassword123", admin["password_hash"])

def test_admin_quota_bypass():
    req = MockRequest()
    admin = database.get_user_by_email("admin@englisp.com")
    
    # Increment quota beyond limit
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET quota_used = 1000000 WHERE email = ?", ("admin@englisp.com",))
    conn.commit()
    conn.close()
    
    resolved_user = get_auth_user(req, x_api_key=admin["api_key"])
    assert resolved_user is not None
    assert resolved_user["email"] == "admin@englisp.com"

def test_password_update_logic():
    # Test updating password hash in database
    new_hash = database.hash_password("newpassword123")
    success = database.update_user_password("admin@englisp.com", new_hash)
    assert success is True
    
    admin = database.get_user_by_email("admin@englisp.com")
    assert database.verify_password("newpassword123", admin["password_hash"])
    assert not database.verify_password("adminpassword123", admin["password_hash"])

def test_change_password_endpoint():
    client = TestClient(app)
    
    # Get admin API key
    admin = database.get_user_by_email("admin@englisp.com")
    api_key = admin["api_key"]
    
    # 1. Correct old password changes password successfully
    response = client.post(
        "/api/auth/change-password",
        headers={"X-API-Key": api_key},
        json={"old_password": "adminpassword123", "new_password": "newsecurepassword123"}
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    # Verify password was updated
    admin_updated = database.get_user_by_email("admin@englisp.com")
    assert database.verify_password("newsecurepassword123", admin_updated["password_hash"])
    
    # 2. Incorrect old password raises error
    response_fail = client.post(
        "/api/auth/change-password",
        headers={"X-API-Key": api_key},
        json={"old_password": "wrongpassword", "new_password": "yetanotherpassword123"}
    )
    assert response_fail.status_code == 400
    assert "Incorrect old password" in response_fail.json()["detail"]
    
    # 3. Short new password raises error
    response_short = client.post(
        "/api/auth/change-password",
        headers={"X-API-Key": api_key},
        json={"old_password": "newsecurepassword123", "new_password": "123"}
    )
    assert response_short.status_code == 400
    assert "New password must be at least 6 characters" in response_short.json()["detail"]
