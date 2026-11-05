# core/google_auth.py
# Handles logging Leo into your Google account so it can actually read/write
# your Calendar and Gmail. First run opens a browser for you to click "Allow" —
# after that, the login gets cached in token.json so it just works silently.

from pathlib import Path
from core.config import settings

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:  # Optional until Google integrations are used.
    Request = Credentials = InstalledAppFlow = None

# Scopes = what permissions we're asking for. Keep this list as small as
# possible — only ask for what Leo actually needs.
SCOPES = [
    "https://www.googleapis.com/auth/calendar",        # read/write calendar events
    "https://www.googleapis.com/auth/gmail.readonly",  # read emails
    "https://www.googleapis.com/auth/gmail.send",       # send emails
]

CREDENTIALS_FILE = settings.google_credentials_path
TOKEN_FILE = settings.google_token_path


def get_google_credentials():
    """
    Returns valid Google credentials, logging in via browser if needed.
    Reused by both the Calendar and Gmail tools.
    """
    if Credentials is None:
        raise RuntimeError(
            "Google integration dependencies are not installed. "
            "Run pip install -r requirements.txt."
        )
    creds = None

    # If we've logged in before, token.json already has our saved login
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    # If there's no valid saved login, log in fresh (or refresh an expired one)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not Path(CREDENTIALS_FILE).exists():
                raise FileNotFoundError(
                    f"Google credentials not found at {CREDENTIALS_FILE}. "
                    "Download OAuth desktop credentials and set LEO_GOOGLE_CREDENTIALS."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)

        # Save this login for next time so we don't have to repeat the browser flow
        TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(TOKEN_FILE, "w", encoding="utf-8") as token_file:
            token_file.write(creds.to_json())

    return creds