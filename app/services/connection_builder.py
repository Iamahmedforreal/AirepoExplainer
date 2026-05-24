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
        remainder = module[level:].lstrip(".")
        base_parts = source_dir.parts
        if level > len(base_parts):
            return None
        base = Path(*base_parts[: len(base_parts) - level + 1]) if level else source_dir
        if remainder:
            joined = str(base / remainder.replace(".", "/"))
        else:
            joined = str(base)
        for ext in (".py", ".ts", ".tsx", ".js"):
            candidate = joined.replace("\\", "/") + ext
            if candidate in paths:
                return candidate
        init_py = joined.replace("\\", "/") + "/__init__.py"
        if init_py in paths:
            return init_py
        return None

    return _module_to_path(module, paths)


def _resolve_call_target(callee: str, source_path: str, extraction: FileExtraction,
                         chunk_by_name: dict[str, str], paths: set[str]) -> str | None:
    callee = callee.strip()
    if not callee:
        return None

    # same-file bare name
    for sym in extraction.symbols:
        if sym.name == callee.split(".")[0]:
            return chunk_by_name.get(sym.full_name)

    # qualified call matching known symbol suffix
    for full_name, chunk_id in chunk_by_name.items():
        if full_name.endswith(f".{callee}") or full_name == callee:
            return chunk_id

    # imported name — check last segment of imports
    for imp in extraction.imports:
        for name in imp.names:
            if name.split(" as ")[0] == callee.split(".")[0]:
                target_path = _resolve_import_path(imp, source_path, paths)
                if target_path:
                    module = path_to_module(target_path)
                    rest = callee.split(".")[1:] if "." in callee else []
                    target_name = rest[0] if rest else name
                    return chunk_by_name.get(f"{module}.{target_name}")

    return None


def build_connections(
    extractions: list[FileExtraction],
    chunk_by_full_name: dict[str, str],
    module_chunk_by_path: dict[str, str],
) -> list[ConnectionRecord]:
    paths = _all_paths(extractions)
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
            ))

        for call in ext.calls:
            source_id = chunk_by_full_name.get(call.caller_full_name)
            if not source_id:
                continue
            target_id = _resolve_call_target(
                call.callee_text, ext.path, ext, chunk_by_full_name, paths,
            )
            records.append(ConnectionRecord(
                source_chunk_id=source_id,
                target_symbol=call.callee_text,
                target_chunk_id=target_id,
                connection_type="call",
            ))

    return records
