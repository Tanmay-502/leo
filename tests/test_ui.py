from core.ui import COLORS, LABELS, UiEvent


def test_ui_exposes_real_assistant_states():
    expected = {"idle", "listening", "transcribing", "thinking", "speaking", "error"}
    assert expected <= COLORS.keys()
    assert expected <= LABELS.keys()
    assert UiEvent("state", ("thinking", "Thinking…")).kind == "state"
