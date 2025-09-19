import os


def is_allowed_language(language: str):
    """
    Checks if a language is supported.
    """
    allowed_langs_str = os.environ.get("GRIT_MCP_LANGS", "python,php,js")
    allowed_langs = [lang.strip() for lang in allowed_langs_str.split(",")]
    return language in allowed_langs
