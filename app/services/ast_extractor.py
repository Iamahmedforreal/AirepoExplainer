"""
Extract symbols, imports, and call sites from source files using Tree-sitter.
"""
from dataclasses import dataclass, field
from pathlib import Path
import re

from app.services.tree_sitter_parser import detect_language, parse_file


@dataclass
class Symbol:
    name: str
    kind: str  # class | function | method
    full_name: str
    start_line: int
    end_line: int
    parent_full_name: str | None = None
    language: str | None = None
    signature: str | None = None
    docstring: str | None = None
    decorators: list[str] = field(default_factory=list)
    visibility: str = "public"
    body_start_line: int | None = None


@dataclass
class ImportRef:
    module: str
    names: list[str]
    line: int
    kind: str  # import | from_import


@dataclass
class CallSite:
    caller_full_name: str
    callee_text: str
    line: int


@dataclass
class FileExtraction:
    path: str
    language: str
    symbols: list[Symbol] = field(default_factory=list)
    imports: list[ImportRef] = field(default_factory=list)
    calls: list[CallSite] = field(default_factory=list)
    exports: list[str] = field(default_factory=list)


def path_to_module(path: str) -> str:
    stem = Path(path).with_suffix("")
    return ".".join(stem.parts)


def _line(node) -> int:
    return node.start_point[0] + 1


def _end_line(node) -> int:
    return node.end_point[0] + 1


def _node_text(content: str, node) -> str:
    return content[node.start_byte : node.end_byte]


def _child_by_type(node, node_type: str):
    for child in node.children:
        if child.type == node_type:
            return child
    return None


def _definition_node(node):
    if node.type in ("function_definition", "class_definition", "class_declaration",
                     "function_declaration", "method_definition", "lexical_declaration"):
        return node
    if node.type == "decorated_definition":
        return _child_by_type(node, "function_definition") or _child_by_type(node, "class_definition")
    if node.type == "export_statement":
        for child in node.children:
            exported = _definition_node(child)
            if exported:
                return exported
    return None


def _semantic_node(def_node):
    parent = getattr(def_node, "parent", None)
    if parent is not None and parent.type == "decorated_definition":
        return parent
    return def_node


def _declaration_source(content: str, node) -> str:
    body = _child_by_type(node, "block") or _child_by_type(node, "statement_block")
    end_byte = body.start_byte if body else node.end_byte
    text = content[node.start_byte : end_byte].strip()
    return " ".join(line.strip() for line in text.splitlines() if line.strip())


def _body_start_line(node) -> int | None:
    body = _child_by_type(node, "block") or _child_by_type(node, "statement_block")
    if body:
        return _line(body)
    return None


def _clean_string_literal(text: str) -> str:
    text = text.strip()
    prefixes = ("r", "u", "f", "b", "R", "U", "F", "B")
    while text and text[0] in prefixes:
        text = text[1:].strip()
    for quote in ('"""', "'''", '"', "'"):
        if text.startswith(quote) and text.endswith(quote):
            return text[len(quote):-len(quote)].strip()
    return text


def _extract_python_docstring(node, content: str) -> str | None:
    body = _child_by_type(node, "block")
    if not body:
        return None
    for child in body.children:
        if child.type in (":", "pass"):
            continue
        if child.type == "expression_statement":
            string_node = _child_by_type(child, "string")
            if string_node:
                return _clean_string_literal(_node_text(content, string_node))
        return None
    return None


def _extract_decorators(node, content: str) -> list[str]:
    parent = getattr(node, "parent", None)
    if parent is None or parent.type != "decorated_definition":
        return []
    return [
        _node_text(content, child).strip()
        for child in parent.children
        if child.type == "decorator"
    ]


def _visibility(name: str) -> str:
    if name.startswith("#") or (name.startswith("_") and not name.startswith("__")):
        return "private"
    return "public"


def _extract_js_import(node, content: str) -> tuple[str, list[str]]:
    text = _node_text(content, node).strip().rstrip(";")
    source = _child_by_type(node, "string")
    module_name = _node_text(content, source).strip("'\"") if source else text
    names: list[str] = []

    named_match = re.search(r"\{(?P<names>[^}]+)\}", text)
    if named_match:
        for raw_name in named_match.group("names").split(","):
            name = raw_name.strip()
            if name:
                names.append(name.replace(" as ", " as "))

    default_match = re.match(r"import\s+(?P<name>[A-Za-z_$][\w$]*)\s*(?:,|\s+from)", text)
    if default_match:
        default_name = default_match.group("name")
        if default_name not in names:
            names.append(default_name)

    namespace_match = re.search(r"\*\s+as\s+(?P<name>[A-Za-z_$][\w$]*)", text)
    if namespace_match:
        namespace_name = namespace_match.group("name")
        if namespace_name not in names:
            names.append(namespace_name)

    return module_name, names


def _extract_name(node, content: str) -> str | None:
    name_node = (
        _child_by_type(node, "name")
        or _child_by_type(node, "identifier")
        or _child_by_type(node, "type_identifier")
        or _child_by_type(node, "property_identifier")
    )
    if name_node:
        return _node_text(content, name_node)
  # arrow functions assigned to const
    if node.type == "lexical_declaration":
        for child in node.children:
            if child.type == "variable_declarator":
                ident = _child_by_type(child, "identifier")
                if ident:
                    return _node_text(content, ident)
    return None


def _walk_python(node, content: str, path: str, module: str,
                 class_stack: list[str], fn_stack: list[str], result: FileExtraction):
    def_node = _definition_node(node)

    if def_node and def_node.type == "class_definition":
        name = _extract_name(def_node, content)
        if name:
            full = f"{module}.{name}" if not class_stack else f"{module}.{'.'.join(class_stack)}.{name}"
            semantic_node = _semantic_node(def_node)
            result.symbols.append(Symbol(
                name=name, kind="class", full_name=full,
                start_line=_line(semantic_node), end_line=_end_line(def_node),
                parent_full_name=f"{module}.{'.'.join(class_stack)}" if class_stack else module,
                language="python",
                signature=_declaration_source(content, def_node),
                docstring=_extract_python_docstring(def_node, content),
                decorators=_extract_decorators(def_node, content),
                visibility=_visibility(name),
                body_start_line=_body_start_line(def_node),
            ))
            for child in def_node.children:
                _walk_python(child, content, path, module, class_stack + [name], fn_stack, result)
            return

    if def_node and def_node.type == "function_definition":
        name = _extract_name(def_node, content)
        if name:
            kind = "method" if class_stack else "function"
            prefix = f"{module}.{'.'.join(class_stack)}" if class_stack else module
            full = f"{prefix}.{name}"
            parent = f"{module}.{'.'.join(class_stack)}" if class_stack else module
            semantic_node = _semantic_node(def_node)
            result.symbols.append(Symbol(
                name=name, kind=kind, full_name=full,
                start_line=_line(semantic_node), end_line=_end_line(def_node),
                parent_full_name=parent,
                language="python",
                signature=_declaration_source(content, def_node),
                docstring=_extract_python_docstring(def_node, content),
                decorators=_extract_decorators(def_node, content),
                visibility=_visibility(name),
                body_start_line=_body_start_line(def_node),
            ))
            fn_stack = fn_stack + [full]
            for child in def_node.children:
                _walk_python(child, content, path, module, class_stack, fn_stack, result)
            return

    if node.type == "import_statement":
        text = _node_text(content, node).strip()
        module_name = text.replace("import ", "").split(" as ")[0].strip()
        result.imports.append(ImportRef(module=module_name, names=[], line=_line(node), kind="import"))

    if node.type == "import_from_statement":
        module_node = _child_by_type(node, "dotted_name") or _child_by_type(node, "relative_import")
        module_name = _node_text(content, module_node) if module_node else ""
        names = []
        import_list = _child_by_type(node, "import_list") or _child_by_type(node, "aliased_import")
        if import_list:
            for child in import_list.children:
                if child.type in ("dotted_name", "identifier"):
                    names.append(_node_text(content, child).split(" as ")[0])
        result.imports.append(ImportRef(module=module_name, names=names, line=_line(node), kind="from_import"))

    if node.type == "call" and fn_stack:
        fn_node = node.children[0] if node.children else None
        if fn_node:
            result.calls.append(CallSite(
                caller_full_name=fn_stack[-1],
                callee_text=_node_text(content, fn_node),
                line=_line(node),
            ))

    for child in node.children:
        _walk_python(child, content, path, module, class_stack, fn_stack, result)


def _walk_js(node, content: str, path: str, module: str,
             class_stack: list[str], fn_stack: list[str], result: FileExtraction):
    def_node = _definition_node(node)

    if def_node and def_node.type == "class_declaration":
        name = _extract_name(def_node, content)
        if name:
            full = f"{module}.{name}"
            result.symbols.append(Symbol(
                name=name, kind="class", full_name=full,
                start_line=_line(def_node), end_line=_end_line(def_node),
                parent_full_name=module,
                language=result.language,
                signature=_declaration_source(content, def_node),
                docstring=None,
                decorators=[],
                visibility=_visibility(name),
                body_start_line=_body_start_line(def_node),
            ))
            if getattr(node, "type", None) == "export_statement":
                result.exports.append(full)
            for child in def_node.children:
                _walk_js(child, content, path, module, class_stack + [name], fn_stack, result)
            return

    if def_node and def_node.type in ("function_declaration", "method_definition"):
        name = _extract_name(def_node, content)
        if name:
            kind = "method" if class_stack or def_node.type == "method_definition" else "function"
            prefix = f"{module}.{'.'.join(class_stack)}" if class_stack else module
            full = f"{prefix}.{name}"
            parent = f"{module}.{'.'.join(class_stack)}" if class_stack else module
            result.symbols.append(Symbol(
                name=name, kind=kind, full_name=full,
                start_line=_line(def_node), end_line=_end_line(def_node),
                parent_full_name=parent,
                language=result.language,
                signature=_declaration_source(content, def_node),
                docstring=None,
                decorators=[],
                visibility=_visibility(name),
                body_start_line=_body_start_line(def_node),
            ))
            if getattr(node, "type", None) == "export_statement":
                result.exports.append(full)
            fn_stack = fn_stack + [full]
            for child in def_node.children:
                _walk_js(child, content, path, module, class_stack, fn_stack, result)
            return

    if def_node and def_node.type == "lexical_declaration":
        name = _extract_name(def_node, content)
        fn_child = None
        for child in def_node.children:
            if child.type == "variable_declarator":
                fn_child = _child_by_type(child, "arrow_function") or _child_by_type(child, "function")
        if name and fn_child:
            full = f"{module}.{name}"
            result.symbols.append(Symbol(
                name=name, kind="function", full_name=full,
                start_line=_line(def_node), end_line=_end_line(def_node),
                parent_full_name=module,
                language=result.language,
                signature=_declaration_source(content, def_node),
                docstring=None,
                decorators=[],
                visibility=_visibility(name),
                body_start_line=_body_start_line(def_node),
            ))
            if getattr(node, "type", None) == "export_statement":
                result.exports.append(full)
            fn_stack = fn_stack + [full]
            for child in fn_child.children:
                _walk_js(child, content, path, module, class_stack, fn_stack, result)
            return

    if node.type == "import_statement":
        module_name, names = _extract_js_import(node, content)
        result.imports.append(ImportRef(module=module_name, names=names, line=_line(node), kind="import"))

    if node.type == "call_expression" and fn_stack:
        fn_node = node.children[0] if node.children else None
        if fn_node:
            result.calls.append(CallSite(
                caller_full_name=fn_stack[-1],
                callee_text=_node_text(content, fn_node),
                line=_line(node),
            ))

    for child in node.children:
        _walk_js(child, content, path, module, class_stack, fn_stack, result)


def extract_file(path: str, content: str) -> FileExtraction | None:
    language = detect_language(path)
    if not language:
        return None

    root = parse_file(content, language)
    module = path_to_module(path)
    result = FileExtraction(path=path, language=language)

    if language == "python":
        _walk_python(root, content, path, module, [], [], result)
    else:
        _walk_js(root, content, path, module, [], [], result)

    return result


def extract_repo(files: list[dict]) -> list[FileExtraction]:
    extractions = []
    for item in files:
        path = item.get("path")
        content = item.get("content")
        if not isinstance(path, str) or not isinstance(content, str):
            continue
        extracted = extract_file(path, content)
        if extracted:
            extractions.append(extracted)
    return extractions
