"""
EngLISP Admin Team Account Manager
----------------------------------
Use this script to easily provision or revoke a dedicated Paid Tier API account
on the live EngLISP server (Render) for your project teammates.

Usage:
  python manage_team_account.py provision teammate@project.org
  python manage_team_account.py revoke teammate@project.org
"""

import sys
import requests

API_BASE = "https://api.englisp.com"

# Admin credentials configured on Render
ADMIN_EMAIL = "admin@englisp.com"
ADMIN_PASSWORD = "want_2_be_an_evangeLISP@russell_shen_7"

def get_admin_api_key():
    print(f"[*] Authenticating with {API_BASE} as {ADMIN_EMAIL}...")
    res = requests.post(
        f"{API_BASE}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    if res.status_code != 200:
        print(f"[ERROR] Failed to authenticate admin: {res.text}")
        print("Note: If Render is still deploying, wait 1-2 minutes and retry.")
        sys.exit(1)
    
    data = res.json()
    return data["api_key"]

def provision_user(email: str, quota_limit: int = 10000):
    admin_key = get_admin_api_key()
    print(f"[*] Provisioning Paid Tier account for: {email} (Quota: {quota_limit})...")
    
    res = requests.post(
        f"{API_BASE}/api/admin/provision-user",
        headers={"X-API-Key": admin_key},
        json={
            "email": email,
            "tier": "paid",
            "quota_limit": quota_limit
        }
    )
    if res.status_code != 200:
        print(f"[ERROR] Failed to provision user: {res.text}")
        sys.exit(1)
        
    data = res.json()
    print("\n" + "=" * 65)
    print("SUCCESSFULLY PROVISIONED TEAMMATE ACCOUNT")
    print("=" * 65)
    print(f"Email:       {data['email']}")
    print(f"Tier:        {data['tier'].upper()} (Full 100k+ Dictionaries Unlocked)")
    print(f"Quota:       {data['quota_limit']} queries")
    print(f"API Key:     {data['api_key']}")
    print("=" * 65)
    print("\nGive this API Key to your teammates to paste into their client script.")

def revoke_user(email: str):
    admin_key = get_admin_api_key()
    print(f"[*] Revoking account and access for: {email}...")
    
    res = requests.delete(
        f"{API_BASE}/api/admin/users/{email}",
        headers={"X-API-Key": admin_key}
    )
    if res.status_code != 200:
        print(f"[ERROR] Failed to revoke user: {res.text}")
        sys.exit(1)
        
    print(f"\n[SUCCESS] Account {email} has been permanently deleted from Render.")

def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python manage_team_account.py provision <email> [quota]")
        print("  python manage_team_account.py revoke <email>")
        print("\nExamples:")
        print("  python manage_team_account.py provision teammates@mlproject.org 10000")
        print("  python manage_team_account.py revoke teammates@mlproject.org")
        sys.exit(1)
        
    action = sys.argv[1].lower()
    email = sys.argv[2]
    
    if action == "provision":
        quota = int(sys.argv[3]) if len(sys.argv) > 3 else 10000
        provision_user(email, quota)
    elif action == "revoke":
        revoke_user(email)
    else:
        print(f"Unknown action: {action}. Use 'provision' or 'revoke'.")

if __name__ == "__main__":
    main()
