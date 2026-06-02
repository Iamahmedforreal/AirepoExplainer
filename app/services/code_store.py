"""
Persist extracted symbols and connections to PostgreSQL.
"""
import uuid
from pathlib import Path

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.repo_models import CodeChunk, CodeConnection
from app.services.ast_extractor import FileExtraction, extract_repo, path_to_module
from app.services.connection_builder import build_connections


def _slice_content(content: str, start_line: int, end_line: int) -> str:
    lines = content.splitlines()
    return "\n".join(lines[start_line - 1 : end_line])


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

    extractions = extract_repo(files)
    content_by_path = {f["path"]: f["content"] for f in files}

    chunk_by_full_name: dict[str, str] = {}
    module_chunk_by_path: dict[str, str] = {}
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
            parentChunkId=None,
        )
        chunk_rows.append(module_chunk)
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
                content=_slice_content(content, sym.start_line, sym.end_line),
                parentChunkId=parent_id,
            )
            chunk_rows.append(chunk)
            chunk_by_full_name[sym.full_name] = sym_id
            chunk_payloads.append({
                "id": sym_id,
                "path": ext.path,
                "type": sym.kind,
                "name": sym.name,
                "fullName": sym.full_name,
                "startLine": sym.start_line,
                "endLine": sym.end_line,
            })

    connection_records = build_connections(extractions, chunk_by_full_name, module_chunk_by_path)
    connection_rows: list[CodeConnection] = []
    connection_payloads: list[dict] = []

    for rec in connection_records:
        conn_id = str(uuid.uuid4())
        connection_rows.append(CodeConnection(
            id=conn_id,
            repoId=repo_id,
            sourceChunkId=rec.source_chunk_id,
            targetSymbol=rec.target_symbol,
            targetChunkId=rec.target_chunk_id,
            connectionType=rec.connection_type,
        ))
        connection_payloads.append({
            "sourceChunkId": rec.source_chunk_id,
            "targetSymbol": rec.target_symbol,
            "targetChunkId": rec.target_chunk_id,
            "connectionType": rec.connection_type,
        })

    db.add_all(chunk_rows)
    db.add_all(connection_rows)
    await db.flush()

    return {
        "files_extracted": len(extractions),
        "chunks_created": len(chunk_rows),
        "connections_created": len(connection_rows),
        "chunk_payloads": chunk_payloads,
        "connection_payloads": connection_payloads,
    }
