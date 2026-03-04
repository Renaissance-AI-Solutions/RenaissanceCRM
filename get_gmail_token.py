#!/usr/bin/env python3
"""One-time script to get a Gmail OAuth refresh token for the CRM.

Run this on your LOCAL machine (not the server):
    pip install google-auth-oauthlib
    python get_gmail_token.py

You'll need:
- client_id and client_secret from Google Cloud Console
  (OAuth 2.0 credentials, Desktop app type)

After running, paste the printed values into CRM Settings -> General -> Gmail Integration.
"""

import json
import sys

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print("ERROR: Run: pip install google-auth-oauthlib")
    sys.exit(1)

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

client_id = input("Enter your Google OAuth Client ID: ").strip()
client_secret = input("Enter your Google OAuth Client Secret: ").strip()

if not client_id or not client_secret:
    print("ERROR: Client ID and secret are required")
    sys.exit(1)

client_config = {
    "installed": {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
}

flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
creds = flow.run_local_server(port=0)

print("\n" + "=" * 60)
print("SUCCESS! Paste these values into CRM Settings -> Gmail Integration:")
print("=" * 60)
print(f"Client ID:     {client_id}")
print(f"Client Secret: {client_secret}")
print(f"Refresh Token: {creds.refresh_token}")
print("=" * 60)
print("\nDone! You can close this window.")
