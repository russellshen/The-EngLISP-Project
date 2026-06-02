# Copyright (c) 2026 Russell Shen. All rights reserved.
#
# This source code is licensed under the Creative Commons Attribution-NonCommercial-NoDerivatives 
# 4.0 International (CC BY-NC-ND 4.0) license. 

import os
import pytest
from fastapi import HTTPException
from web import database
from web.server import get_auth_user

class MockClient:
    def __init__(self, host: str):
        self.host = host

class MockRequest:
    def __init__(self, host: str = "127.0.0.1"):
        self.client = MockClient(host)

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

def test_database_operations():
    # 1. Test hash and verify password
    password = "supersecretpassword"
    hashed = database.hash_password(password)
    assert database.verify_password(password, hashed) is True
    assert database.verify_password("wrongpassword", hashed) is False

    # 2. Test user creation
    user = database.create_user("test@englisp.com", hashed)
    assert user is not None
    assert user["email"] == "test@englisp.com"
    assert user["quota_limit"] == 100
    assert user["quota_used"] == 0
    assert user["tier"] == "free"
    assert user["api_key"].startswith("englisp_live_")

    # 3. Prevent duplicate creation
    dup = database.create_user("test@englisp.com", hashed)
    assert dup is None

    # 4. Get user by email
    found_email = database.get_user_by_email("test@englisp.com")
    assert found_email is not None
    assert found_email["api_key"] == user["api_key"]

    # 5. Get user by API Key
    found_key = database.get_user_by_api_key(user["api_key"])
    assert found_key is not None
    assert found_key["email"] == "test@englisp.com"

    # 6. Increment quota
    database.increment_user_quota(user["id"], 5)
    updated = database.get_user_by_email("test@englisp.com")
    assert updated["quota_used"] == 5

    # 7. Update tier
    database.update_user_tier("test@englisp.com", "paid", 5000)
    updated_tier = database.get_user_by_email("test@englisp.com")
    assert updated_tier["tier"] == "paid"
    assert updated_tier["quota_limit"] == 5000

def test_auth_dependency():
    # Clear active timestamp list for isolated rate-limiting checks
    from web.server import ANONYMOUS_REQUEST_TIMESTAMPS
    ANONYMOUS_REQUEST_TIMESTAMPS.clear()

    # Create a user
    hashed = database.hash_password("password123")
    user = database.create_user("user@englisp.com", hashed)
    api_key = user["api_key"]

    req = MockRequest(host="192.168.1.100")

    # 1. Valid API key in header
    resolved_user = get_auth_user(req, x_api_key=api_key)
    assert resolved_user is not None
    assert resolved_user["email"] == "user@englisp.com"

    # 2. Valid API key in query parameter
    resolved_user_query = get_auth_user(req, api_key=api_key)
    assert resolved_user_query is not None
    assert resolved_user_query["email"] == "user@englisp.com"

    # 3. Invalid API key raises 401
    with pytest.raises(HTTPException) as excinfo:
        get_auth_user(req, x_api_key="invalid_key")
    assert excinfo.value.status_code == 401
    assert excinfo.value.detail == "Invalid API Key."

    # 4. Anonymous user under Sandbox limits
    # Should resolve to None (anonymous sandbox) without error
    resolved_anon = get_auth_user(req)
    assert resolved_anon is None

    # 5. Anonymous user exceeding sandbox limit (5 requests / min)
    # We already made 1 anonymous request in check 4. Let's make 5 more.
    # The 5th subsequent request should raise a 429.
    for i in range(4):
        get_auth_user(req) # 2nd, 3rd, 4th, 5th requests
    with pytest.raises(HTTPException) as excinfo_429:
        get_auth_user(req) # 6th request
    assert excinfo_429.value.status_code == 429
    assert "Sandbox rate limit exceeded" in excinfo_429.value.detail

    # 6. User exceeding quota limits raises 402
    # Create user with limit 1
    user_q = database.create_user("quota@englisp.com", hashed)
    database.update_user_tier("quota@englisp.com", "free", 1)
    
    # 1st request succeeds
    resolved_q = get_auth_user(req, x_api_key=user_q["api_key"])
    assert resolved_q is not None
    
    # Increment quota
    database.increment_user_quota(user_q["id"], 1)
    
    # 2nd request raises 402
    with pytest.raises(HTTPException) as excinfo_402:
        get_auth_user(req, x_api_key=user_q["api_key"])
    assert excinfo_402.value.status_code == 402
    assert "API Quota exceeded" in excinfo_402.value.detail
