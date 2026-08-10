# test_google_auth.py
# Quick standalone test — just confirms Google login works before we
# wire it into Leo's actual tools.

from core.google_auth import get_google_credentials

creds = get_google_credentials()
print("Google login successful!" if creds and creds.valid else "Something went wrong.")