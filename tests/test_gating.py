import os

from server.policy import gating


def test_is_allowed_language():
    """
    Tests the is_allowed_language function.
    """
    os.environ["GRIT_MCP_LANGS"] = "python,js"
    assert gating.is_allowed_language("python") is True
    assert gating.is_allowed_language("js") is True
    assert gating.is_allowed_language("php") is False
    del os.environ["GRIT_MCP_LANGS"]



