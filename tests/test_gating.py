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


def test_is_allowed_path(monkeypatch):
    """
    Tests the is_allowed_path function.
    """
    # Test with environment variable
    monkeypatch.setenv("GRIT_MCP_ALLOWED_PATHS", "/app/src,/app/lib")
    assert gating.is_allowed_path("/app/src/main.py") is True
    assert gating.is_allowed_path("/app/lib/utils.js") is True
    assert gating.is_allowed_path("/app/other/file.txt") is False

    # Test without environment variable (defaults to cwd)
    monkeypatch.delenv("GRIT_MCP_ALLOWED_PATHS")
    cwd = os.getcwd()
    assert gating.is_allowed_path(os.path.join(cwd, "some_file.txt")) is True
    assert gating.is_allowed_path("/some/other/path/file.txt") is False
