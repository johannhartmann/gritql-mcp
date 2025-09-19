import json


def parse_grit_json(output: str):
    """
    Parses JSON output from a Grit CLI command.
    """
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return {"error": "Failed to parse JSON output from Grit CLI."}


def parse_grit_list(output: str):
    """
    Parses the output of `grit list` or `grit patterns list`.
    """
    # For now, we assume JSON output.
    return parse_grit_json(output)


def parse_grit_describe(output: str):
    """
    Parses the output of `grit patterns describe`.
    """
    # For now, we assume JSON output.
    return parse_grit_json(output)
