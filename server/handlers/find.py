import json
import subprocess

from server.policy import gating


def find_code(
    gritql: str = None,
    patternName: str = None,
    language: str = None,
    includeGlobs: list[str] = None,
    excludeGlobs: list[str] = None,
    paths: list[str] = None,
    maxFiles: int = None,
    maxMatchesPerFile: int = None,
):
    """
    Find matches in the workspace (no writes).
    """
    if not gritql and not patternName:
        return {"error": "Either gritql or patternName is required."}

    # Policy enforcement
    if language and not gating.is_allowed_language(language):
        return {"error": f"Language is not allowed: {language}"}

    pattern = gritql if gritql else patternName
    cmd = ["grit", "apply", pattern, "--dry-run", "--jsonl"]

    if language:
        cmd.extend(["--language", language])
    if includeGlobs:
        cmd.extend(["--include", ",".join(includeGlobs)])
    if excludeGlobs:
        cmd.extend(["--exclude", ",".join(excludeGlobs)])
    
    # Add -- to prevent parameter injection
    if paths:
        cmd.append("--")
        cmd.extend(paths)

    process = subprocess.run(cmd, capture_output=True, text=True)
    if process.returncode != 0:
        return {"error": process.stderr}

    # Parse the JSONL output
    matches = []
    for line in process.stdout.strip().split("\n"):
        if line:
            matches.append(json.loads(line))

    return {"matches": matches}
