import re
from server.mcp_instance import mcp


@mcp.tool("gritql.generate")
def generate_gritql(
    problem: str, intent: str, language: str, constraints: list[str] = None
):
    """
    Deterministically synthesize GritQL from a problem statement.
    """
    problem = problem.lower()
    gritql = ""
    rationale = "Generated based on keyword and pattern matching."
    assumptions = []

    # More sophisticated rule-based generation
    # This is still a simple example, but demonstrates more advanced capabilities.
    
    # Rule for finding functions
    find_functions_match = re.search(r"find all functions( named (.*))?", problem)
    if find_functions_match:
        function_name = find_functions_match.group(2)
        if function_name:
            gritql = f"`function_definition(name='{function_name.strip()}')`"
            rationale = f"Generated a pattern to find function definitions with the name '{function_name.strip()}'."
        else:
            gritql = "`function_definition`"
            rationale = "Generated a pattern to find all function definitions."
        assumptions.append("Assuming 'functions' refers to function definitions.")

    # Rule for removing console.log
    elif "remove console.log" in problem:
        gritql = "`console.log($args)` => ``"
        rationale = "Generated a pattern to find and remove `console.log` statements."
        assumptions.append("This pattern is specific to JavaScript/TypeScript and similar languages.")

    # Rule for finding classes
    elif "find all classes" in problem:
        gritql = "`class_definition`"
        rationale = "Generated a pattern to find all class definitions."
        assumptions.append("Assuming 'classes' refers to class definitions.")

    # Rule for finding imports
    elif "find all imports" in problem:
        gritql = "`import_statement`"
        rationale = "Generated a pattern to find all import statements."
        assumptions.append("This pattern will find all import statements, regardless of the module.")

    # Default case
    else:
        gritql = f"`{problem}`"
        rationale = (
            "Could not determine a specific pattern, using the problem statement as a"
            " raw pattern. This is a simple pass-through and may not be valid GritQL."
        )
        assumptions.append(
            "For better results, try a more specific request like 'find all functions named my_function'."
        )

    return {
        "gritql": gritql,
        "rationale": rationale,
        "assumptions": assumptions,
    }