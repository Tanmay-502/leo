"""Safe checks for Google authentication setup; no network login is performed."""

import pytest

from core import google_auth


def test_missing_google_dependencies_is_actionable(monkeypatch):
    monkeypatch.setattr(google_auth, "Credentials", None)
    with pytest.raises(RuntimeError, match="dependencies"):
        google_auth.get_google_credentials()
