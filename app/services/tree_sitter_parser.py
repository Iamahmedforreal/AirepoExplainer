"""
Production-ready Tree-sitter parser service for multi-language AST extraction.
Supports Python, JavaScript, TypeScript, and TSX using dynamic grammar loading
and safe UTF-8 source-code parsing.
"""
from pathlib import Path
from tree_sitter import Language, Parser
from functools import  lru_cache

# Precise extension mapping to standard Tree-sitter grammar keys
EXTENSION_TO_LANGUAGE = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx"
}


def detect_language(path: str) -> str | None:
    """
    Return the TreeSitter language name for a file based on its extension.
    """
    ext = Path(path).suffix.lower()
    return EXTENSION_TO_LANGUAGE.get(ext)


@lru_cache(maxsize=None)
def _parse_single_language(language: str) -> Parser:
    """
    """
    if language == "python":
        import tree_sitter_python as lang_module
        capsule = lang_module.language()
    elif language == "javascript":
        import tree_sitter_javascript as lang_module
        capsule = lang_module.language()
    elif language == "typescript":
        import tree_sitter_typescript as lang_module
        capsule = lang_module.language_typescript()
    elif language == "tsx":
        import tree_sitter_typescript as lang_module
        capsule = lang_module.language_tsx()
    else:
        raise ValueError(f"Unsupported tree-sitter language: {language}")

    try:
        return Parser(language(capsule)) # newer Api style
    except TypeError:
        parser = Parser()                   # older API fallback
        parser.language = Language(capsule)
        return parser


def parse_file(content: str, language: str):
    """
    Parse source code using the selected language grammar and return the root AST node.
    """
    parser = _parse_single_language(language)
    # Safely parse content using UTF-8 encoding to match byte indices of the AST
    tree = parser.parse(content.encode("utf-8"))
    return tree.root_node


def extract_languages_from_clean_files(files: list[dict]) -> set[str]:
    """
    Process a list of accepted file dictionaries and return a sorted list
    of unique supported language names found.
    """
    languages = set()
    for file_item in files:
        # Extract path either from 'path' key
        path_str = file_item.get("path")
        if path_str:
            lang = detect_language(path_str)
            if lang:
                languages.add(lang)
    return sorted(list(languages))


def get_parser(language: set[str]) -> dict[str, Parser]:
    parser = {}
    for lang in language:
        try:
            parser[lang] = _parse_single_language(lang)
        except ValueError as e:
            pass
    return parser
