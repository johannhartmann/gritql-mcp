import os


def is_allowed_path(path: str):
    """
    Checks if a path is within the allowed paths.
    """
    allowed_paths_str = os.environ.get("GRIT_MCP_ALLOWED_PATHS")
    if not allowed_paths_str:
        # If not set, allow the current working directory
        return os.path.abspath(path).startswith(os.getcwd())

    allowed_paths = [os.path.abspath(p.strip()) for p in allowed_paths_str.split(",")]
    abs_path = os.path.abspath(path)

    return any(abs_path.startswith(p) for p in allowed_paths)


def is_allowed_language(language: str):
    """
    Checks if a language is supported.
    """
    allowed_langs_str = os.environ.get("GRIT_MCP_LANGS", "python,php,js")
    allowed_langs = [lang.strip() for lang in allowed_langs_str.split(",")]
    return language in allowed_langs
