"""
Production-ready Tree-sitter parser service for multi-language AST extraction.
Supports Python, JavaScript, TypeScript, and TSX using dynamic grammar loading
and safe UTF-8 source-code parsing.
"""
from pathlib import Path
from tree_sitter import Language as TSLanguage, Parser
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
def _map_languages_to_correct_libary(language: str) -> Parser:
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
        return Parser(TSLanguage(capsule)) # newer Api style
    except TypeError:
        parser = Parser()                   # older API fallback
        parser.language = TSLanguage(capsule)
        return parser


def parse_file(content: str, language: str):
    """
    Parse source code using the selected language grammar and return the root AST node.
    """
    parser = _map_languages_to_correct_libary(language)
    # Safely parse content using UTF-8 encoding to match byte indices of the AST
    tree = parser.parse(content.encode("utf-8"))
    return tree.root_node

def _point_to_dict(point) -> dict:
    """
    Convert Tree-sitter point objects/tuples into JSON-serializable coordinates.
    """
    if hasattr(point, "row") and hasattr(point, "column"):
        return {
            "row": point.row,
            "column": point.column,
        }

    return {
        "row": point[0],
        "column": point[1],
    }


def _serialize_node(node) -> dict:
    """
    Convert a Tree-sitter node into plain Python data that ARQ can serialize.
    """
    return {
        "type": node.type,
        "is_named": node.is_named,
        "start_point": _point_to_dict(node.start_point),
        "end_point": _point_to_dict(node.end_point),
        "start_byte": node.start_byte,
        "end_byte": node.end_byte,
        "children": [_serialize_node(child) for child in node.named_children],
    }


def parse_repo(files: list[dict]) -> list[dict]:
    parsed_files = []

    for source_file in files:
        path = source_file.get("path")
        content = source_file.get("content")

        if not isinstance(path, str) or not isinstance(content, str):
            continue

        lang = detect_language(path)

        if not lang:
            continue

        ast = parse_file(content, lang)

        parsed_files.append({
            "path": path,
            "language": lang,
            "ast": _serialize_node(ast),
        })

    return parsed_files
