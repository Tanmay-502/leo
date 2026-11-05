"""The old live Groq smoke test is intentionally not run by pytest."""

import pytest


@pytest.mark.skip(reason="Live paid/provider smoke test; run manually when configured.")
def test_groq_live_smoke():
    pass
