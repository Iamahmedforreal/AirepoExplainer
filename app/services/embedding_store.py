"""
Store OpenAI embeddings for semantic code chunks in Postgres/pgvector.
"""
import hashlib
import uuid
from collections.abc import Sequence

from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.app_config import settings
from app.models.repo_models import CodeChunk, CodeChunkEmbedding


def _content_hash(chunk: CodeChunk) -> str:
    metadata = chunk.metadataJson or {}
    content_hash = metadata.get("contentHash")
    if isinstance(content_hash, str) and content_hash:
        return content_hash
    return hashlib.sha256(chunk.content.encode("utf-8")).hexdigest()


def build_embedding_input(chunk: CodeChunk, *, max_chars: int | None = None) -> str:
    metadata = chunk.metadataJson or {}
    parts = [
        f"path: {chunk.path}",
        f"type: {chunk.type}",
        f"name: {chunk.fullName}",
        f"language: {metadata.get('language') or ''}",
        f"signature: {metadata.get('signature') or ''}",
        f"docstring: {metadata.get('docstring') or ''}",
        "",
        "source:",
        chunk.content,
    ]
    text = "\n".join(parts).strip()
    if max_chars and len(text) > max_chars:
        return text[:max_chars]
    return text


def _embedding_client() -> AsyncOpenAI:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required to embed code chunks")
    return AsyncOpenAI(api_key=settings.openai_api_key)


async def _create_embeddings(
    texts: Sequence[str],
    *,
    client=None,
    model: str | None = None,
) -> list[list[float]]:
    embedding_client = client or _embedding_client()
    response = await embedding_client.embeddings.create(
        model=model or settings.embedding_model,
        input=list(texts),
    )
    return [item.embedding for item in response.data]


async def embed_repo_chunks(
    db: AsyncSession,
    repo_id: str,
    *,
    client=None,
    model: str | None = None,
    dimensions: int | None = None,
    batch_size: int | None = None,
    max_input_chars: int | None = None,
) -> dict:
    embedding_model = model or settings.embedding_model
    embedding_dimensions = dimensions or settings.embedding_dimensions
    batch_limit = batch_size or settings.embedding_batch_size
    text_limit = max_input_chars or settings.embedding_max_input_chars

    chunk_result = await db.execute(
        select(CodeChunk)
        .where(CodeChunk.repoId == repo_id)
        .order_by(CodeChunk.path, CodeChunk.startLine)
    )
    chunks = list(chunk_result.scalars().all())
    chunk_ids = [chunk.id for chunk in chunks]

    existing_by_chunk_id: dict[str, CodeChunkEmbedding] = {}
    if chunk_ids:
        existing_result = await db.execute(
            select(CodeChunkEmbedding).where(
                CodeChunkEmbedding.chunkId.in_(chunk_ids),
                CodeChunkEmbedding.embeddingModel == embedding_model,
            )
        )
        existing_by_chunk_id = {
            embedding.chunkId: embedding
            for embedding in existing_result.scalars().all()
        }

    pending_chunks: list[CodeChunk] = []
    skipped = 0
    for chunk in chunks:
        content_hash = _content_hash(chunk)
        existing = existing_by_chunk_id.get(chunk.id)
        if (
            existing
            and existing.contentHash == content_hash
            and existing.embeddingDimensions == embedding_dimensions
        ):
            skipped += 1
            continue
        pending_chunks.append(chunk)

    embedded = 0
    for start in range(0, len(pending_chunks), batch_limit):
        batch = pending_chunks[start:start + batch_limit]
        texts = [
            build_embedding_input(chunk, max_chars=text_limit)
            for chunk in batch
        ]
        vectors = await _create_embeddings(texts, client=client, model=embedding_model)
        if len(vectors) != len(batch):
            raise RuntimeError("Embedding provider returned a different number of vectors than inputs")

        values = []
        for chunk, vector in zip(batch, vectors, strict=True):
            values.append({
                "id": str(uuid.uuid4()),
                "repoId": repo_id,
                "chunkId": chunk.id,
                "embeddingModel": embedding_model,
                "embeddingDimensions": embedding_dimensions,
                "contentHash": _content_hash(chunk),
                "vector": vector,
            })

        stmt = insert(CodeChunkEmbedding).values(values)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_code_chunk_embeddings_chunk_model",
            set_={
                "repoId": stmt.excluded.repoId,
                "embeddingDimensions": stmt.excluded.embeddingDimensions,
                "contentHash": stmt.excluded.contentHash,
                "vector": stmt.excluded.vector,
            },
        )
        await db.execute(stmt)
        embedded += len(batch)

    await db.flush()

    return {
        "total_chunks": len(chunks),
        "embedded": embedded,
        "skipped": skipped,
        "failed": 0,
        "embedding_model": embedding_model,
        "embedding_dimensions": embedding_dimensions,
    }
