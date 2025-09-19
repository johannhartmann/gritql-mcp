import json
import subprocess

from server.handlers import library
from server.handlers import generate


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
    result = library.search_patterns.fn(
        query="console", language="js", source="all", limit=10
    )

    assert "items" in result
    result_items = json.loads(result["items"])
    assert result_items[0]["name"] == "console-log"
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

    result = library.search_patterns.fn(
        query="console", language="js", source="all", limit=10
    )

    assert "error" in result
    assert result["error"] == "grit command not found"


def test_generate_gritql_find_all_functions():
    result = generate.generate_gritql.fn(
        problem="find all functions", intent="find", language="python", constraints=[]
    )
    assert result["gritql"] == "`function_definition`"
    assert "find all function definitions" in result["rationale"]


def test_generate_gritql_find_named_function():
    result = generate.generate_gritql.fn(
        problem="find all functions named my_function",
        intent="find",
        language="python",
        constraints=[],
    )
    assert result["gritql"] == "`function_definition(name='my_function')`"
    assert "find function definitions with the name 'my_function'" in result["rationale"]


def test_generate_gritql_remove_console_log():
    result = generate.generate_gritql.fn(
        problem="remove console.log", intent="remove", language="javascript", constraints=[]
    )
    assert result["gritql"] == "`console.log($args)` => ``"
    assert "remove `console.log` statements" in result["rationale"]


def test_generate_gritql_find_all_classes():
    result = generate.generate_gritql.fn(
        problem="find all classes", intent="find", language="python", constraints=[]
    )
    assert result["gritql"] == "`class_definition`"
    assert "find all class definitions" in result["rationale"]


def test_generate_gritql_find_all_imports():
    result = generate.generate_gritql.fn(
        problem="find all imports", intent="find", language="python", constraints=[]
    )
    assert result["gritql"] == "`import_statement`"
    assert "find all import statements" in result["rationale"]


def test_generate_gritql_default_case():
    result = generate.generate_gritql.fn(
        problem="do something random", intent="do", language="python", constraints=[]
    )
    assert result["gritql"] == "`do something random`"
    assert "Could not determine a specific pattern" in result["rationale"]