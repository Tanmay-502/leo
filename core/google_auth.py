# core/google_auth.py
# Handles logging Leo into your Google account so it can actually read/write
# your Calendar and Gmail. First run opens a browser for you to click "Allow" —
# after that, the login gets cached in token.json so it just works silently.

import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Scopes = what permissions we're asking for. Keep this list as small as
# possible — only ask for what Leo actually needs.
SCOPES = [
    "https://www.googleapis.com/auth/calendar",        # read/write calendar events
    "https://www.googleapis.com/auth/gmail.readonly",  # read emails
    "https://www.googleapis.com/auth/gmail.send",       # send emails
]

CREDENTIALS_FILE = "credentials.json"  # downloaded from Google Cloud Console
TOKEN_FILE = "token.json"              # auto-created after first login


def get_google_credentials():
    """
    Returns valid Google credentials, logging in via browser if needed.
    Reused by both the Calendar and Gmail tools.
    """
    creds = None

    # If we've logged in before, token.json already has our saved login
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # If there's no valid saved login, log in fresh (or refresh an expired one)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save this login for next time so we don't have to repeat the browser flow
        with open(TOKEN_FILE, "w") as token_file:
            token_file.write(creds.to_json())

    return creds