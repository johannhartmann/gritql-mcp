import json
import subprocess

from server.policy import gating


def apply_code(
    gritql: str = None,
    patternName: str = None,
    language: str = None,
    includeGlobs: list[str] = None,
    excludeGlobs: list[str] = None,
    paths: list[str] = None,
):
    """
    Apply a rewrite directly to code.
    """
    if not gritql and not patternName:
        return {"error": "Either gritql or patternName is required."}

    # Policy enforcement
    if language and not gating.is_allowed_language(language):
        return {"error": f"Language is not allowed: {language}"}

    pattern = gritql if gritql else patternName
    cmd = ["grit", "apply", pattern, "--jsonl"]

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

    # Process the JSONL output to summarize the results
    total_changes = 0
    changed_files = set()
    for line in process.stdout.strip().split("\n"):
        if not line:
            continue
        match = json.loads(line)
        total_changes += 1
        file_path = match.get("path")
        if file_path:
            changed_files.add(file_path)

    return {
        "filesChanged": len(changed_files),
        "totalChanges": total_changes,
        "changedFiles": list(changed_files),
    }
