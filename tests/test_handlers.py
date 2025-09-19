import json
import subprocess

from server.handlers import library


def test_search_patterns_success(mocker):
    """
    Tests the search_patterns function on a successful run.
    """
    # Mock the subprocess.run call
    mock_process = mocker.Mock()
    mock_process.returncode = 0
    mock_process.stdout = json.dumps(
        [
            {
                "type": "pattern",
                "name": "console-log",
                "description": "Finds console.log statements.",
            }
        ]
    )
    mocker.patch("subprocess.run", return_value=mock_process)

    result = library.search_patterns(
        query="console", language="js", source="all", limit=10
    )

    assert "items" in result
    assert len(result["items"]) > 0
    assert result["items"][0]["name"] == "console-log"
    # We expect two calls: one for patterns list, one for list
    assert subprocess.run.call_count == 2


def test_search_patterns_error(mocker):
    """
    Tests the search_patterns function when the grit command fails.
    """
    # Mock the subprocess.run call to simulate an error
    mock_process = mocker.Mock()
    mock_process.returncode = 1
    mock_process.stderr = "grit command not found"
    mocker.patch("subprocess.run", return_value=mock_process)

    result = library.search_patterns(
        query="console", language="js", source="all", limit=10
    )

    assert "error" in result
    assert result["error"] == "grit command not found"
