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
import sqlite3
import hashlib
import secrets
from datetime import datetime
from typing import Optional

DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "users.db"))
# Ensure parent directory exists for DB path
db_dir = os.path.dirname(os.path.abspath(DB_PATH))
if db_dir:
    os.makedirs(db_dir, exist_ok=True)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def db_init():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT,
            api_key TEXT UNIQUE NOT NULL,
            tier TEXT DEFAULT 'free',
            quota_limit INTEGER DEFAULT 100,
            quota_used INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            subscription_expires_at TEXT,
            status TEXT DEFAULT 'none',
            is_verified INTEGER DEFAULT 0,
            verification_token TEXT,
            reset_token TEXT,
            reset_token_expires_at TEXT
        )
    """)
    
    # Migrations for existing database
    cursor.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]
    if "subscription_expires_at" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN subscription_expires_at TEXT")
    if "status" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN status TEXT DEFAULT 'none'")
    if "is_verified" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN is_verified INTEGER DEFAULT 0")
    if "verification_token" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN verification_token TEXT")
    if "reset_token" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN reset_token TEXT")
    if "reset_token_expires_at" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN reset_token_expires_at TEXT")
    if "stripe_customer_id" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN stripe_customer_id TEXT")
    if "stripe_subscription_id" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN stripe_subscription_id TEXT")
        
    conn.commit()
    
    # Bootstrap default admin account if not exists
    cursor.execute("SELECT * FROM users WHERE email = ?", ("admin@englisp.com",))
    if not cursor.fetchone():
        admin_password = os.environ.get("ADMIN_PASSWORD")
        if not admin_password:
            import sys
            if "pytest" in sys.modules:
                admin_password = "adminpassword123"
            else:
                import secrets
                admin_password = "admin_" + secrets.token_urlsafe(16)
                print(f"\n[SECURITY WARNING] ADMIN_PASSWORD environment variable not set. Generated temporary secure admin password: {admin_password}\n")
        admin_pass_hash = hash_password(admin_password)
        admin_key = generate_api_key()
        created_at = datetime.utcnow().isoformat()
        cursor.execute(
            "INSERT INTO users (email, password_hash, api_key, tier, quota_limit, status, created_at, is_verified) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("admin@englisp.com", admin_pass_hash, admin_key, "admin", 999999, "active", created_at, 1)
        )
        conn.commit()
        
    conn.close()

def hash_password(password: str) -> str:
    """Hashes a password using PBKDF2 with SHA-256 and a static salt."""
    salt = b"englisp_salt_12345"
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000).hex()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies that a plain password matches the stored hash."""
    return hash_password(plain_password) == hashed_password

def update_user_password(email: str, new_password_hash: str) -> bool:
    """Updates a user's password hash in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE users SET password_hash = ? WHERE email = ?",
            (new_password_hash, email.lower().strip())
        )
        conn.commit()
        return cursor.rowcount > 0
    except Exception:
        return False
    finally:
        conn.close()

def generate_api_key() -> str:
    """Generates a secure, random API key prefixed with 'englisp_live_'."""
    return "englisp_live_" + secrets.token_urlsafe(32)

def create_user(email: str, password_hash: str = None, verification_token: str = None) -> Optional[dict]:
    """Creates a new user with a generated API key and optional verification token."""
    api_key = generate_api_key()
    created_at = datetime.utcnow().isoformat()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (email, password_hash, api_key, created_at, verification_token, is_verified) VALUES (?, ?, ?, ?, ?, 0)",
            (email.lower().strip(), password_hash, api_key, created_at, verification_token)
        )
        conn.commit()
        user_id = cursor.lastrowid
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def get_user_by_email(email: str) -> Optional[dict]:
    """Retrieves a user record by email address."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email.lower().strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_by_api_key(api_key: str) -> Optional[dict]:
    """Retrieves a user record by their API key."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE api_key = ?", (api_key.strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def increment_user_quota(user_id: int, amount: int = 1):
    """Increments the quota count for a user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET quota_used = quota_used + ? WHERE id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def update_user_tier(email: str, tier: str, quota_limit: int):
    """Updates a user's tier and monthly quota limit."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET tier = ?, quota_limit = ? WHERE email = ?", (tier, quota_limit, email.lower().strip()))
    conn.commit()
    conn.close()

def subscribe_user(email: str, duration_seconds: int) -> Optional[dict]:
    """Sets a user to paid tier and calculates expiration timestamp."""
    from datetime import datetime, timedelta
    conn = get_db_connection()
    cursor = conn.cursor()
    expires_at = (datetime.utcnow() + timedelta(seconds=duration_seconds)).isoformat()
    try:
        cursor.execute(
            "UPDATE users SET tier = 'paid', status = 'active', quota_limit = 10000, subscription_expires_at = ? WHERE email = ?",
            (expires_at, email.lower().strip())
        )
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email.lower().strip(),))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def downgrade_user_subscription(email: str) -> Optional[dict]:
    """Downgrades a user back to free tier when subscription expires."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE users SET tier = 'free', status = 'expired', quota_limit = 100, subscription_expires_at = NULL WHERE email = ?",
            (email.lower().strip(),)
        )
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email.lower().strip(),))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def verify_user_by_token(token: str) -> Optional[dict]:
    """Marks a user as verified based on their verification token."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM users WHERE verification_token = ?", (token,))
        row = cursor.fetchone()
        if not row:
            return None
        user = dict(row)
        cursor.execute(
            "UPDATE users SET is_verified = 1, verification_token = NULL WHERE id = ?",
            (user["id"],)
        )
        conn.commit()
        user["is_verified"] = 1
        user["verification_token"] = None
        return user
    except Exception:
        return None
    finally:
        conn.close()

def set_user_reset_token(email: str, token: str, expires_at: str) -> bool:
    """Sets a temporary reset token (passcode) and expiration for a user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE users SET reset_token = ?, reset_token_expires_at = ? WHERE email = ?",
            (token, expires_at, email.lower().strip())
        )
        conn.commit()
        return cursor.rowcount > 0
    except Exception:
        return False
    finally:
        conn.close()

def reset_user_password_by_token(email: str, token: str, new_password_hash: str) -> bool:
    """Resets a user's password if the reset token matches and is not expired."""
    from datetime import datetime
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT * FROM users WHERE email = ? AND reset_token = ?",
            (email.lower().strip(), token)
        )
        row = cursor.fetchone()
        if not row:
            return False
        user = dict(row)
        if user["reset_token_expires_at"]:
            now = datetime.utcnow().isoformat()
            if now > user["reset_token_expires_at"]:
                return False
        
        cursor.execute(
            "UPDATE users SET password_hash = ?, reset_token = NULL, reset_token_expires_at = NULL WHERE id = ?",
            (new_password_hash, user["id"])
        )
        conn.commit()
        return cursor.rowcount > 0
    except Exception:
        return False
    finally:
        conn.close()

def assign_stripe_customer_to_user(email: str, customer_id: str) -> bool:
    """Stores the Stripe Customer ID for a user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE users SET stripe_customer_id = ? WHERE email = ?",
            (customer_id, email.lower().strip())
        )
        conn.commit()
        return cursor.rowcount > 0
    except Exception:
        return False
    finally:
        conn.close()

def activate_user_subscription_by_stripe(customer_id: str, subscription_id: str, expires_at: str) -> Optional[dict]:
    """Activates paid tier for a user matching Stripe Customer ID, and stores subscription details."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE users SET tier = 'paid', status = 'active', quota_limit = 10000, stripe_subscription_id = ?, subscription_expires_at = ? WHERE stripe_customer_id = ?",
            (subscription_id, expires_at, customer_id)
        )
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE stripe_customer_id = ?", (customer_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    except Exception:
        return None
    finally:
        conn.close()

def cancel_user_subscription_by_stripe(subscription_id: str) -> Optional[dict]:
    """Downgrades user back to free tier matching Stripe Subscription ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE users SET tier = 'free', status = 'expired', quota_limit = 100, subscription_expires_at = NULL WHERE stripe_subscription_id = ?",
            (subscription_id,)
        )
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE stripe_subscription_id = ?", (subscription_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    except Exception:
        return None
    finally:
        conn.close()
