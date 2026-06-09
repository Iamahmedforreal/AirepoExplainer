"""
Persist extracted symbols and connections to PostgreSQL.
"""
import hashlib
import uuid
from pathlib import Path

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.repo_models import CodeChunk, CodeConnection
from app.services.ast_extractor import FileExtraction, extract_repo, path_to_module
from app.services.connection_builder import build_connections

"""function to slice content by line numbers"""
def _slice_content(content: str, start_line: int, end_line: int) -> str:
    lines = content.splitlines()
    return "\n".join(lines[start_line - 1 : end_line])

"""function to compute content hash for a given string to detect changes in code chunks"""
def _content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _import_metadata(ext: FileExtraction) -> list[dict]:
    return [
        {
            "module": imp.module,
            "names": imp.names,
            "line": imp.line,
            "kind": imp.kind,
        }
        for imp in ext.imports
    ]


def _module_metadata(ext: FileExtraction, content: str, module_name: str) -> dict:
    line_count = len(content.splitlines())
    return {
        "language": ext.language,
        "semanticKind": "module",
        "module": module_name,
        "signature": None,
        "docstring": None,
        "decorators": [],
        "visibility": "public",
        "lineCount": line_count,
        "contentHash": _content_hash(content),
        "parentFullName": None,
        "childrenCount": sum(1 for sym in ext.symbols if sym.parent_full_name == module_name),
        "imports": _import_metadata(ext),
        "exports": ext.exports,
        "unresolvedCalls": [],
        "split": None,
    }


def _symbol_metadata(ext: FileExtraction, content: str, symbol, children_count: int) -> dict:
    line_count = max(symbol.end_line - symbol.start_line + 1, 0)
    unresolved_calls = [
        {
            "calleeText": call.callee_text,
            "line": call.line,
        }
        for call in ext.calls
        if call.caller_full_name == symbol.full_name
    ]
    return {
        "language": symbol.language or ext.language,
        "semanticKind": symbol.kind,
        "module": path_to_module(ext.path),
        "signature": symbol.signature,
        "docstring": symbol.docstring,
        "decorators": symbol.decorators,
        "visibility": symbol.visibility,
        "bodyStartLine": symbol.body_start_line,
        "lineCount": line_count,
        "contentHash": _content_hash(content),
        "parentFullName": symbol.parent_full_name,
        "childrenCount": children_count,
        "imports": [],
        "exports": [name for name in ext.exports if name == symbol.full_name],
        "unresolvedCalls": unresolved_calls,
        "split": None,
    }


def build_extraction_payload(repo_id: str, files: list[dict]) -> dict:
    """Build semantic chunk and connection rows without writing them."""
    extractions = extract_repo(files)
    content_by_path = {f["path"]: f["content"] for f in files}

    chunk_by_full_name: dict[str, str] = {}
    module_chunk_by_path: dict[str, str] = {}
    metadata_by_chunk_id: dict[str, dict] = {}
    chunk_rows: list[CodeChunk] = []
    chunk_payloads: list[dict] = []

    for ext in extractions:
        content = content_by_path[ext.path]
        module_name = path_to_module(ext.path)
        module_id = str(uuid.uuid4())
        module_chunk = CodeChunk(
            id=module_id,
            repoId=repo_id,
            path=ext.path,
            type="module",
            name=Path(ext.path).stem,
            fullName=module_name,
            startLine=1,
            endLine=len(content.splitlines()),
            content=content,
            metadataJson=_module_metadata(ext, content, module_name),
            parentChunkId=None,
        )
        chunk_rows.append(module_chunk)
        metadata_by_chunk_id[module_id] = module_chunk.metadataJson
        module_chunk_by_path[ext.path] = module_id
        chunk_by_full_name[module_name] = module_id
        chunk_payloads.append({
            "id": module_id,
            "path": ext.path,
            "type": "module",
            "name": module_name,
            "fullName": module_name,
            "startLine": 1,
            "endLine": len(content.splitlines()),
            "metadata": module_chunk.metadataJson,
        })

        symbol_id_by_full: dict[str, str] = {}
        for sym in ext.symbols:
            sym_id = str(uuid.uuid4())
            if sym.parent_full_name == module_name:
                parent_id = module_id
            elif sym.parent_full_name in chunk_by_full_name:
                parent_id = chunk_by_full_name[sym.parent_full_name]
            elif sym.parent_full_name in symbol_id_by_full:
                parent_id = symbol_id_by_full[sym.parent_full_name]
            else:
                parent_id = module_id
            child_count = sum(1 for child in ext.symbols if child.parent_full_name == sym.full_name)
            sym_content = _slice_content(content, sym.start_line, sym.end_line)
            symbol_id_by_full[sym.full_name] = sym_id
            chunk = CodeChunk(
                id=sym_id,
                repoId=repo_id,
                path=ext.path,
                type=sym.kind,
                name=sym.name,
                fullName=sym.full_name,
                startLine=sym.start_line,
                endLine=sym.end_line,
                content=sym_content,
                metadataJson=_symbol_metadata(ext, sym_content, sym, child_count),
                parentChunkId=parent_id,
            )
            chunk_rows.append(chunk)
            metadata_by_chunk_id[sym_id] = chunk.metadataJson
            chunk_by_full_name[sym.full_name] = sym_id
            chunk_payloads.append({
                "id": sym_id,
                "path": ext.path,
                "type": sym.kind,
                "name": sym.name,
                "fullName": sym.full_name,
                "startLine": sym.start_line,
                "endLine": sym.end_line,
                "metadata": chunk.metadataJson,
            })

    connection_records = build_connections(extractions, chunk_by_full_name, module_chunk_by_path)
    connection_rows: list[CodeConnection] = []
    connection_payloads: list[dict] = []

    for rec in connection_records:
        conn_id = str(uuid.uuid4())
        if rec.connection_type == "call" and rec.confidence != "unresolved":
            metadata = metadata_by_chunk_id.get(rec.source_chunk_id)
            if metadata:
                metadata["unresolvedCalls"] = [
                    call for call in metadata.get("unresolvedCalls", [])
                    if call.get("calleeText") != rec.target_symbol or call.get("line") != rec.source_line
                ]
        connection_rows.append(CodeConnection(
            id=conn_id,
            repoId=repo_id,
            sourceChunkId=rec.source_chunk_id,
            targetSymbol=rec.target_symbol,
            targetChunkId=rec.target_chunk_id,
            connectionType=rec.connection_type,
            sourceLine=rec.source_line,
            targetPath=rec.target_path,
            confidence=rec.confidence,
            metadataJson=rec.metadata or {},
        ))
        connection_payloads.append({
            "sourceChunkId": rec.source_chunk_id,
            "targetSymbol": rec.target_symbol,
            "targetChunkId": rec.target_chunk_id,
            "connectionType": rec.connection_type,
            "sourceLine": rec.source_line,
            "targetPath": rec.target_path,
            "confidence": rec.confidence,
            "metadata": rec.metadata or {},
        })

    return {
        "files_extracted": len(extractions),
        "chunks_created": len(chunk_rows),
        "connections_created": len(connection_rows),
        "chunk_rows": chunk_rows,
        "connection_rows": connection_rows,
        "chunk_payloads": chunk_payloads,
        "connection_payloads": connection_payloads,
    }


async def persist_extraction(
    db: AsyncSession,
    repo_id: str,
    files: list[dict],
) -> dict:
    """
    Extract symbols, save CodeChunk + CodeConnection rows in PostgreSQL.
    Returns a summary dict with counts and chunk/connection payloads.
    """
    await db.execute(delete(CodeConnection).where(CodeConnection.repoId == repo_id))
    await db.execute(delete(CodeChunk).where(CodeChunk.repoId == repo_id))

    payload = build_extraction_payload(repo_id, files)

    db.add_all(payload["chunk_rows"])
    db.add_all(payload["connection_rows"])
    await db.flush()

    return {
        "files_extracted": payload["files_extracted"],
        "chunks_created": payload["chunks_created"],
        "connections_created": payload["connections_created"],
        "chunk_payloads": payload["chunk_payloads"],
        "connection_payloads": payload["connection_payloads"],
    }
