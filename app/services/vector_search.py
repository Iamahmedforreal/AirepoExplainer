"""
Vector search over embedded semantic code chunks.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.app_config import settings
from app.models.repo_models import CodeChunk, CodeChunkEmbedding
from app.services.embedding_store import _create_embeddings


async def embed_query(query: str, *, client=None, model: str | None = None) -> list[float]:
    vectors = await _create_embeddings([query], client=client, model=model or settings.embedding_model)
    return vectors[0]


async def search_code_chunks(
    db: AsyncSession,
    *,
    repo_id: str,
    query: str,
    limit: int = 8,
    client=None,
    model: str | None = None,
) -> list[dict]:
    embedding_model = model or settings.embedding_model
    query_vector = await embed_query(query, client=client, model=embedding_model)
    distance = CodeChunkEmbedding.vector.cosine_distance(query_vector).label("distance")

    result = await db.execute(
        select(CodeChunk, distance)
        .join(CodeChunkEmbedding, CodeChunkEmbedding.chunkId == CodeChunk.id)
        .where(
            CodeChunkEmbedding.repoId == repo_id,
            CodeChunkEmbedding.embeddingModel == embedding_model,
        )
        .order_by(distance)
        .limit(limit)
    )

    matches = []
    for chunk, score in result.all():
        matches.append({
            "chunkId": chunk.id,
            "repoId": chunk.repoId,
            "path": chunk.path,
            "type": chunk.type,
            "name": chunk.name,
            "fullName": chunk.fullName,
            "startLine": chunk.startLine,
            "endLine": chunk.endLine,
            "content": chunk.content,
            "metadata": chunk.metadataJson or {},
            "distance": float(score),
        })
    return matches
