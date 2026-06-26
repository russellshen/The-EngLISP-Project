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

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from englisp.loader import CURRENT_USER_TIER, LEXICON
from web import database, server

def test_context_aware_gating():
    # 1. Free tier: "apple" should NOT be in LEXICON
    CURRENT_USER_TIER.set("free")
    assert "apple" not in LEXICON
    
    # 2. Paid tier: "apple" SHOULD be in LEXICON (if the full database is present)
    CURRENT_USER_TIER.set("paid")
    import os
    resources_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "englisp", "resources")
    full_db_exists = os.path.exists(os.path.join(resources_dir, "en_lexicon_a.lson"))
    
    if full_db_exists:
        assert "apple" in LEXICON
    else:
        # Fallback verification in CI when the private dictionary partitions are absent
        assert "apple" not in LEXICON
        assert "dog" in LEXICON

def test_database_subscription_lifecycle():
    # Initialize DB (creates database and runs migrations)
    database.db_init()
    
    email = "test_sub@example.com"
    # Ensure clean state
    user = database.get_user_by_email(email)
    if user:
        conn = database.get_db_connection()
        conn.execute("DELETE FROM users WHERE email = ?", (email,))
        conn.commit()
        conn.close()
        
    # Create user (default tier should be 'free')
    user = database.create_user(email)
    assert user["tier"] == "free"
    assert user["status"] == "none"
    assert user["subscription_expires_at"] is None
    
    # Subscribe user for 10 seconds
    updated = database.subscribe_user(email, 10)
    assert updated["tier"] == "paid"
    assert updated["status"] == "active"
    assert updated["subscription_expires_at"] is not None
    
    # Verify we can parse expiration timestamp
    exp = datetime.fromisoformat(updated["subscription_expires_at"])
    assert exp > datetime.utcnow()
    
    # Downgrade user manually
    downgraded = database.downgrade_user_subscription(email)
    assert downgraded["tier"] == "free"
    assert downgraded["status"] == "expired"
    assert downgraded["subscription_expires_at"] is None

def test_automatic_expiration_gating():
    database.db_init()
    email = "expire_test@example.com"
    
    # Clean state
    conn = database.get_db_connection()
    conn.execute("DELETE FROM users WHERE email = ?", (email,))
    conn.commit()
    conn.close()
    
    user = database.create_user(email)
    
    # Subscribe for 5 seconds
    user = database.subscribe_user(email, 5)
    
    # Query me endpoint using get_auth_user dependency
    class DummyRequest:
        class DummyClient:
            host = "127.0.0.1"
        client = DummyClient()
        
    req_obj = DummyRequest()
    
    # Authenticate (currently paid)
    authed_user = server.get_auth_user(req_obj, api_key=user["api_key"])
    assert authed_user["tier"] == "paid"
    assert CURRENT_USER_TIER.get() == "paid"
    
    # Mock datetime to simulate time passing (6 seconds later, past expiration)
    future_time = (datetime.utcnow() + timedelta(seconds=6)).isoformat()
    with patch("web.server.datetime") as mock_datetime:
        mock_datetime.utcnow.return_value = datetime.fromisoformat(future_time)
        mock_datetime.fromisoformat = datetime.fromisoformat
        
        # Call get_auth_user again. It should detect expiration, downgrade, and update context!
        authed_user2 = server.get_auth_user(req_obj, api_key=user["api_key"])
        assert authed_user2["tier"] == "free"
        assert authed_user2["status"] == "expired"
        assert CURRENT_USER_TIER.get() == "free"
