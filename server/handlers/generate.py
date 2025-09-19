from server.mcp_instance import mcp


@mcp.tool("gritql.generate")
def generate_gritql(
    problem: str, intent: str, language: str, constraints: list[str] = None
):
    """
    Deterministically synthesize GritQL from a problem statement.
    """
    gritql = ""
    rationale = "Generated based on simple keyword matching."
    assumptions = []

    # Simple example of rule-based generation
    if "find all functions" in problem:
        gritql = "`function_definition`"
        assumptions.append("Assuming 'functions' refers to function definitions.")
    elif "remove console.log" in problem:
        gritql = "`console.log($args)` => ``"
        assumptions.append("Assuming this is for JavaScript/TypeScript.")
    else:
        gritql = f"`{problem}`"
        rationale = (
            "Could not determine a specific pattern, using the problem statement as a"
            " raw pattern."
        )
        assumptions.append("This is a simple pass-through and may not be valid GritQL.")

    return {
        "gritql": gritql,
        "rationale": rationale,
        "assumptions": assumptions,
    }
