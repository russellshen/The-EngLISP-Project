# Copyright (c) 2026 Russell Shen. All rights reserved.
#
# This source code is licensed under the Creative Commons Attribution-NonCommercial-NoDerivatives 
# 4.0 International (CC BY-NC-ND 4.0) license. 
#
# Commercial use, proprietary use, or use in closed-source or revenue-generating projects 
# is strictly prohibited under this license.

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from web import database, server

client = TestClient(server.app)

@pytest.fixture(autouse=True)
def run_around_tests():
    # Setup fresh database
    database.db_init()
    # Clean up test user
    email = "stripe_test@example.com"
    conn = database.get_db_connection()
    conn.execute("DELETE FROM users WHERE email = ?", (email,))
    conn.commit()
    conn.close()
    yield

def test_stripe_disabled_by_default():
    # 1. Register a user
    email = "stripe_test@example.com"
    hashed = database.hash_password("password123")
    user = database.create_user(email, hashed)
    database.verify_user_by_token(user["verification_token"])
    
    # Generate API key headers
    headers = {"X-API-Key": user["api_key"]}
    
    # 2. Query /api/auth/me -> should say stripe_enabled = False
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["stripe_enabled"] is False
    
    # 3. Call subscribe route directly -> should succeed since Stripe is disabled
    sub_response = client.post("/api/auth/subscribe", headers=headers, json={"duration_seconds": 60})
    assert sub_response.status_code == 200
    sub_data = sub_response.json()
    assert sub_data["tier"] == "paid"
    
    # 4. Call checkout route -> should fail with 400
    checkout_response = client.post("/api/auth/stripe-checkout", headers=headers)
    assert checkout_response.status_code == 400
    assert "disabled" in checkout_response.json()["detail"]

@patch("web.server.STRIPE_SECRET_KEY", "sk_test_mock_12345")
@patch("web.server.STRIPE_WEBHOOK_SECRET", "whsec_mock_12345")
@patch("web.server.stripe")
def test_stripe_enabled_checkout_session(mock_stripe):
    # 1. Register user
    email = "stripe_test@example.com"
    hashed = database.hash_password("password123")
    user = database.create_user(email, hashed)
    database.verify_user_by_token(user["verification_token"])
    headers = {"X-API-Key": user["api_key"]}
    
    # 2. Query /api/auth/me -> should say stripe_enabled = True
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["stripe_enabled"] is True
    
    # 3. Call subscribe route directly -> should fail because Stripe is enabled
    sub_response = client.post("/api/auth/subscribe", headers=headers, json={"duration_seconds": 60})
    assert sub_response.status_code == 400
    assert "Direct subscription upgrades are disabled" in sub_response.json()["detail"]
    
    # Mock Customer create & Checkout Session create
    mock_customer = MagicMock()
    mock_customer.id = "cus_mock123"
    mock_stripe.Customer.create.return_value = mock_customer
    
    mock_session = MagicMock()
    mock_session.url = "https://checkout.stripe.com/pay/mock_session"
    mock_stripe.checkout.Session.create.return_value = mock_session
    
    # 4. Call checkout route -> should succeed and create a Stripe customer & session
    checkout_response = client.post("/api/auth/stripe-checkout", headers=headers)
    assert checkout_response.status_code == 200
    checkout_data = checkout_response.json()
    assert checkout_data["success"] is True
    assert checkout_data["checkout_url"] == "https://checkout.stripe.com/pay/mock_session"
    
    # Check that stripe customer ID was stored in user record
    updated_user = database.get_user_by_email(email)
    assert updated_user["stripe_customer_id"] == "cus_mock123"

@patch("web.server.STRIPE_SECRET_KEY", "sk_test_mock_12345")
@patch("web.server.STRIPE_WEBHOOK_SECRET", "whsec_mock_12345")
@patch("web.server.stripe")
def test_stripe_webhook_handling(mock_stripe):
    # 1. Register user
    email = "stripe_test@example.com"
    hashed = database.hash_password("password123")
    user = database.create_user(email, hashed)
    database.verify_user_by_token(user["verification_token"])
    
    # Associate a Stripe customer ID manually for verification
    database.assign_stripe_customer_to_user(email, "cus_mock123")
    
    # Mock retrieve subscription & Webhook validation
    mock_sub = MagicMock()
    # Expire in 1000 seconds
    future_timestamp = int(datetime.now(timezone.utc).timestamp()) + 1000
    mock_sub.current_period_end = future_timestamp
    mock_stripe.Subscription.retrieve.return_value = mock_sub
    
    # Construct mock event for completed checkout session
    mock_event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "customer": "cus_mock123",
                "subscription": "sub_mock123"
            }
        }
    }
    mock_stripe.Webhook.construct_event.return_value = mock_event
    
    # 2. Call Webhook -> completed checkout session
    webhook_response = client.post(
        "/api/stripe/webhook",
        headers={"stripe-signature": "mock_sig"},
        content="raw_payload"
    )
    assert webhook_response.status_code == 200
    assert webhook_response.json()["status"] == "success"
    
    # User should now be a paid subscriber
    updated_user = database.get_user_by_email(email)
    assert updated_user["tier"] == "paid"
    assert updated_user["status"] == "active"
    assert updated_user["stripe_subscription_id"] == "sub_mock123"
    assert updated_user["subscription_expires_at"] is not None
    
    # 3. Webhook -> subscription deleted event
    mock_event_deleted = {
        "type": "customer.subscription.deleted",
        "data": {
            "object": {
                "id": "sub_mock123",
                "status": "canceled"
            }
        }
    }
    mock_stripe.Webhook.construct_event.return_value = mock_event_deleted
    
    webhook_response2 = client.post(
        "/api/stripe/webhook",
        headers={"stripe-signature": "mock_sig"},
        content="raw_payload"
    )
    assert webhook_response2.status_code == 200
    assert webhook_response2.json()["status"] == "success"
    
    # User should now be downgraded back to free
    downgraded_user = database.get_user_by_email(email)
    assert downgraded_user["tier"] == "free"
    assert downgraded_user["status"] == "expired"
    assert downgraded_user["subscription_expires_at"] is None
