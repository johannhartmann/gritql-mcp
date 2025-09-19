import json
import subprocess

from server.policy import gating


def dry_run_code(
    gritql: str = None,
    patternName: str = None,
    language: str = None,
    includeGlobs: list[str] = None,
    excludeGlobs: list[str] = None,
    paths: list[str] = None,
):
    """
    Summarize the impact of a rewrite without diffs.
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

    # Process the JSONL output to summarize the results
    total_matches = 0
    files = {}
    for line in process.stdout.strip().split("\n"):
        if not line:
            continue
        match = json.loads(line)
        total_matches += 1
        file_path = match.get("path")
        if file_path:
            if file_path not in files:
                files[file_path] = {"path": file_path, "matches": 0}
            files[file_path]["matches"] += 1

    return {
        "totalMatches": total_matches,
        "totalFiles": len(files),
        "files": list(files.values()),
    }
