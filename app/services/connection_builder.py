"""
Resolve import/call references and build connection records.
"""
from dataclasses import dataclass
from pathlib import Path

from app.services.ast_extractor import FileExtraction, path_to_module


@dataclass
class ConnectionRecord:
    source_chunk_id: str
    target_symbol: str
    target_chunk_id: str | None
    connection_type: str  # import | call
    source_line: int | None = None
    target_path: str | None = None
    confidence: str = "unresolved"  # resolved | partial | unresolved
    metadata: dict | None = None


def _all_paths(extractions: list[FileExtraction]) -> set[str]:
    return {e.path for e in extractions}


def _module_to_path(module: str, paths: set[str]) -> str | None:
    candidate = module.replace(".", "/") + ".py"
    if candidate in paths:
        return candidate
    candidate_ts = module.replace(".", "/") + ".ts"
    if candidate_ts in paths:
        return candidate_ts
    candidate_js = module.replace(".", "/") + ".js"
    if candidate_js in paths:
        return candidate_js
    candidate_jsx = module.replace(".", "/") + ".jsx"
    if candidate_jsx in paths:
        return candidate_jsx
    candidate_tsx = module.replace(".", "/") + ".tsx"
    if candidate_tsx in paths:
        return candidate_tsx
    return None


def _resolve_import_path(imp, source_path: str, paths: set[str]) -> str | None:
    module = imp.module
    if not module:
        return None

    if module.startswith("."):
        source_dir = Path(source_path).parent
        level = len(module) - len(module.lstrip("."))
        remainder = module[level:].lstrip("./")
        base_parts = source_dir.parts
        if level > len(base_parts):
            return None
        base = Path(*base_parts[: len(base_parts) - level + 1]) if level else source_dir
        if remainder:
            joined = str(base / remainder.replace(".", "/"))
        else:
            joined = str(base)
        for ext in (".py", ".ts", ".tsx", ".js", ".jsx"):
            candidate = joined.replace("\\", "/") + ext
            if candidate in paths:
                return candidate
        init_py = joined.replace("\\", "/") + "/__init__.py"
        if init_py in paths:
            return init_py
        return None

    return _module_to_path(module, paths)


def _resolve_call_target(callee: str, source_path: str, extraction: FileExtraction,
                         chunk_by_name: dict[str, str], paths: set[str],
                         full_name_to_path: dict[str, str]) -> tuple[str | None, str | None, str]:
    callee = callee.strip()
    if not callee:
        return None, None, "unresolved"
    parts = callee.split(".")
    local_name = parts[-1] if parts[0] in {"self", "this"} else parts[0]

    # same-file bare name
    for sym in extraction.symbols:
        if sym.name == local_name:
            target_id = chunk_by_name.get(sym.full_name)
            if target_id:
                return target_id, extraction.path, "resolved"

    # qualified call matching known symbol suffix
    for full_name, chunk_id in chunk_by_name.items():
        if full_name.endswith(f".{callee}") or full_name == callee:
            return chunk_id, full_name_to_path.get(full_name), "resolved"

    # imported name — check last segment of imports
    for imp in extraction.imports:
        for name in imp.names:
            imported_name, _, alias = name.partition(" as ")
            local_name = alias or imported_name
            if local_name == callee.split(".")[0]:
                target_path = _resolve_import_path(imp, source_path, paths)
                if target_path:
                    module = path_to_module(target_path)
                    rest = callee.split(".")[1:] if "." in callee else []
                    target_name = rest[0] if rest else imported_name
                    target_id = chunk_by_name.get(f"{module}.{target_name}")
                    return target_id, target_path, "resolved" if target_id else "partial"

    return None, None, "unresolved"


def build_connections(
    extractions: list[FileExtraction],
    chunk_by_full_name: dict[str, str],
    module_chunk_by_path: dict[str, str],
) -> list[ConnectionRecord]:
    paths = _all_paths(extractions)
    full_name_to_path = {
        symbol.full_name: ext.path
        for ext in extractions
        for symbol in ext.symbols
    }
    full_name_to_path.update({
        path_to_module(ext.path): ext.path
        for ext in extractions
    })
    records: list[ConnectionRecord] = []

    for ext in extractions:
        module_chunk_id = module_chunk_by_path.get(ext.path)
        if not module_chunk_id:
            continue

        for imp in ext.imports:
            target_path = _resolve_import_path(imp, ext.path, paths)
            target_chunk_id = module_chunk_by_path.get(target_path) if target_path else None
            target_symbol = imp.module
            if imp.names:
                target_symbol = f"{imp.module}.{','.join(imp.names)}"
            records.append(ConnectionRecord(
                source_chunk_id=module_chunk_id,
                target_symbol=target_symbol,
                target_chunk_id=target_chunk_id,
                connection_type="import",
                source_line=imp.line,
                target_path=target_path,
                confidence="resolved" if target_chunk_id else "unresolved",
                metadata={
                    "kind": imp.kind,
                    "module": imp.module,
                    "names": imp.names,
                    "sourcePath": ext.path,
                },
            ))

        for call in ext.calls:
            source_id = chunk_by_full_name.get(call.caller_full_name)
            if not source_id:
                continue
            target_id, target_path, confidence = _resolve_call_target(
                call.callee_text, ext.path, ext, chunk_by_full_name, paths, full_name_to_path,
            )
            records.append(ConnectionRecord(
                source_chunk_id=source_id,
                target_symbol=call.callee_text,
                target_chunk_id=target_id,
                connection_type="call",
                source_line=call.line,
                target_path=target_path,
                confidence=confidence,
                metadata={
                    "callerFullName": call.caller_full_name,
                    "calleeText": call.callee_text,
                    "sourcePath": ext.path,
                },
            ))

    return records
