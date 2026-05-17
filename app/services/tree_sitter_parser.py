from pathlib import Path
from tree_sitter import Language, Parser

EXTENSION_TO_LANGUAGE = {
    ".py":   "python",
    ".js":   "javascript",
    ".ts":   "typescript"
}


def detect_language(path: str) -> str | None:
    """Return TreeSitter language name for this file, or None if unsupported."""
    if path not in EXTENSION_TO_LANGUAGE:
        raise ValueError(f"Unsupported file type: {path}")
    ext = Path(path).suffix.lower()
    return EXTENSION_TO_LANGUAGE.get(ext)

"""functions to parse code using each files language and tree-sitter grammars. """
def parser(language: str):
    if language == "python":
        import tree_sitter_python as lang_modula
    elif language == "javascript":
        import tree_sitter_javascript as lang_modula
    elif language == "typescript":
        import tree_sitter_typescript as lang_modula

    lang = Language(lang_modula.language())
    parser = Parser(lang)
    return parser

    
  