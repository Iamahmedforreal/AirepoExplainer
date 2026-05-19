"""
AST Traversal and Chunking Service for Codebase Intelligence.
Walks the Tree-sitter AST to extract semantic code units (modules, classes, methods, functions, interfaces)
with rich metadata (parent scopes, line ranges, paths) for embedding and RAG pipelines.
"""
from pathlib import Path
from typing import TypedDict, List, Optional


class CodeChunk(TypedDict):
    type: str           # "module" | "class" | "method" | "function" | "interface" | "type"
    name: str           # Unique identifier name of the code block
    start_line: int     # 1-indexed start line
    end_line: int       # 1-indexed end line
    content: str        # Raw source substring of the code block
    parent: Optional[str] # Name of parent enclosing scope (e.g., class name)
    path: str           # Relative file path of the source


def get_node_name(node, source_bytes: bytes) -> str:
    """
    Safely extract the identifier name of a Tree-sitter AST node.
    Checks explicit field name 'name' first, and falls back to looking for
    child identifier nodes if undefined.
    """
    name_node = node.child_by_field_name("name")
    if name_node:
        try:
            return name_node.text.decode("utf-8", errors="ignore")
        except Exception:
            pass

    # Fallback search for identifier types in children
    for child in node.children:
        if child.type in ("identifier", "property_identifier", "type_identifier"):
            try:
                return child.text.decode("utf-8", errors="ignore")
            except Exception:
                pass

    return "anonymous"


def traverse_ast(
    node,
    source_bytes: bytes,
    file_path: str,
    parent_name: Optional[str] = None,
    chunks: List[dict] = None
) -> List[dict]:
    """
    Walks the AST in pre-order/DFS to isolate and capture structural units.
    Correctly maps language-specific nodes and tracks nested scopes.
    """
    if chunks is None:
        chunks = []

    node_type = node.type
    chunk_type = None

    # 1. Map AST node types to unified semantic chunk types
    # Supports Python, JavaScript, TypeScript, and TSX grammars
    if node_type in ("class_definition", "class_declaration", "class"):
        chunk_type = "class"
    elif node_type == "interface_declaration":
        chunk_type = "interface"
    elif node_type == "type_alias_declaration":
        chunk_type = "type"
    elif node_type in ("function_definition", "function_declaration", "function", "generator_function"):
        # If nested inside a class scope, represent as a method
        if parent_name:
            chunk_type = "method"
        else:
            chunk_type = "function"
    elif node_type == "method_definition":
        chunk_type = "method"

    # 2. Extract code chunk and boundary details
    if chunk_type:
        name = get_node_name(node, source_bytes)
        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1
        
        try:
            content = node.text.decode("utf-8", errors="ignore")
        except Exception:
            content = ""

        chunks.append({
            "type": chunk_type,
            "name": name,
            "start_line": start_line,
            "end_line": end_line,
            "content": content,
            "parent": parent_name,
            "path": file_path
        })
        
        # Nested functions/classes take this code unit's name as parent scope
        new_parent = name
    else:
        new_parent = parent_name

    # 3. Always traverse children recursively to support nested structures (DFS)
    for child in node.children:
        traverse_ast(child, source_bytes, file_path, new_parent, chunks)

    return chunks


def chunk_source_code(content: str, file_path: str, language: str) -> List[CodeChunk]:
    """
    High-level driver to parse and chunk source code.
    Always includes a global 'module' chunk representing the entire file,
    providing high-level context alongside deep granular AST chunks.
    """
    chunks = []
    source_bytes = content.encode("utf-8")
    total_lines = len(content.splitlines())

    # Ensure a fallback file-level chunk always exists
    chunks.append({
        "type": "module",
        "name": Path(file_path).name,
        "start_line": 1,
        "end_line": max(1, total_lines),
        "content": content,
        "parent": None,
        "path": file_path
    })

    # Safely parse and run AST traversal
    try:
        from app.services.tree_sitter_parser import parse_file
        root_node = parse_file(content, language)
        if root_node:
            traverse_ast(root_node, source_bytes, file_path, parent_name=None, chunks=chunks)
    except Exception:
        # Graceful recovery: if syntax errors occur or parsing fails,
        # return the file-level module chunk so downstream indexing is never blocked.
        pass

    return chunks
