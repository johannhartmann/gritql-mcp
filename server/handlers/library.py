import json
import subprocess


def search_patterns(query: str, language: str, source: str, limit: int):
    """
    Search local library for patterns/workflows.
    """
    # Call grit patterns list
    patterns_cmd = ["grit", "patterns", "list", "--json"]
    if language:
        patterns_cmd.extend(["--language", language])
    if source != "all":
        patterns_cmd.extend(["--source", source])

    patterns_process = subprocess.run(patterns_cmd, capture_output=True, text=True)
    if patterns_process.returncode != 0:
        # Handle error
        return {"error": patterns_process.stderr}

    patterns = json.loads(patterns_process.stdout)

    # Call grit list
    list_cmd = ["grit", "list", "--json"]
    if language:
        list_cmd.extend(["--language", language])
    if source != "all":
        list_cmd.extend(["--source", source])

    list_process = subprocess.run(list_cmd, capture_output=True, text=True)
    if list_process.returncode != 0:
        # Handle error
        return {"error": list_process.stderr}

    applyables = json.loads(list_process.stdout)

    # Combine and filter results
    all_items = patterns + applyables

    # A real implementation would filter by query here

    return {"items": all_items[:limit]}


def describe_pattern(name: str):
    """
    Return canonical metadata for a single pattern.
    """
    cmd = ["grit", "patterns", "describe", "--", name, "--json"]
    process = subprocess.run(cmd, capture_output=True, text=True)
    if process.returncode != 0:
        return {"error": process.stderr}

    return json.loads(process.stdout)
