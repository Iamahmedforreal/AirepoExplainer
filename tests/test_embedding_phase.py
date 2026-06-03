import os
import unittest
from types import SimpleNamespace

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
os.environ.setdefault("GITHUB_API_KEY", "test")
os.environ.setdefault("CLERK_WEBHOOK_SECRET", "test")
os.environ.setdefault("JWT_PUBLIK_KEY", "test")
os.environ.setdefault("CLEERK_SCERET_KEY", "test")
os.environ.setdefault("OPENAI_API_KEY", "test")

from app.ARQ.task import embed_repo_task
from app.ARQ.worker import WorkerSettings
from app.models.repo_models import CodeChunk, CodeChunkEmbedding
from app.services.embedding_store import build_embedding_input, embed_repo_chunks
from app.services.vector_search import search_code_chunks


class _ScalarResult:
    def __init__(self, values):
        self._values = values

    def all(self):
        return self._values


class _Result:
    def __init__(self, values=None, rows=None):
        self._values = values or []
        self._rows = rows or []

    def scalars(self):
        return _ScalarResult(self._values)

    def all(self):
        return self._rows


class _FakeSession:
    def __init__(self, results):
        self._results = list(results)
        self.executed = []
        self.flushed = False

    async def execute(self, statement):
        self.executed.append(statement)
        if self._results:
            return self._results.pop(0)
        return _Result()

    async def flush(self):
        self.flushed = True


class _FakeEmbeddings:
    def __init__(self, vectors):
        self.vectors = vectors
        self.calls = []

    async def create(self, *, model, input):
        self.calls.append({"model": model, "input": input})
        data = [SimpleNamespace(embedding=vector) for vector in self.vectors[:len(input)]]
        return SimpleNamespace(data=data)


class _FakeClient:
    def __init__(self, vectors):
        self.embeddings = _FakeEmbeddings(vectors)


def _chunk(
    *,
    chunk_id="chunk-1",
    repo_id="repo-1",
    content="def run():\n    return True\n",
    content_hash="hash-1",
):
    return CodeChunk(
        id=chunk_id,
        repoId=repo_id,
        path="app/service.py",
        type="function",
        name="run",
        fullName="app.service.run",
        startLine=1,
        endLine=2,
        content=content,
        metadataJson={
            "language": "python",
            "signature": "run()",
            "docstring": "Run service.",
            "contentHash": content_hash,
        },
    )


class EmbeddingPhaseTests(unittest.IsolatedAsyncioTestCase):
    def test_embedding_input_uses_metadata_and_source(self):
        text = build_embedding_input(_chunk())

        self.assertIn("path: app/service.py", text)
        self.assertIn("type: function", text)
        self.assertIn("name: app.service.run", text)
        self.assertIn("language: python", text)
        self.assertIn("signature: run()", text)
        self.assertIn("docstring: Run service.", text)
        self.assertIn("source:\ndef run()", text)

    async def test_embedding_store_skips_current_embeddings(self):
        chunk = _chunk()
        existing = CodeChunkEmbedding(
            id="embedding-1",
            repoId="repo-1",
            chunkId=chunk.id,
            embeddingModel="test-model",
            embeddingDimensions=3,
            contentHash="hash-1",
            vector=[0.1, 0.2, 0.3],
        )
        db = _FakeSession([_Result([chunk]), _Result([existing])])
        client = _FakeClient([[0.9, 0.8, 0.7]])

        summary = await embed_repo_chunks(
            db,
            "repo-1",
            client=client,
            model="test-model",
            dimensions=3,
        )

        self.assertEqual(summary["total_chunks"], 1)
        self.assertEqual(summary["embedded"], 0)
        self.assertEqual(summary["skipped"], 1)
        self.assertEqual(client.embeddings.calls, [])
        self.assertTrue(db.flushed)

    async def test_embedding_store_upserts_changed_chunks(self):
        chunk = _chunk(content_hash="hash-2")
        existing = CodeChunkEmbedding(
            id="embedding-1",
            repoId="repo-1",
            chunkId=chunk.id,
            embeddingModel="test-model",
            embeddingDimensions=3,
            contentHash="hash-1",
            vector=[0.1, 0.2, 0.3],
        )
        db = _FakeSession([_Result([chunk]), _Result([existing])])
        client = _FakeClient([[0.9, 0.8, 0.7]])

        summary = await embed_repo_chunks(
            db,
            "repo-1",
            client=client,
            model="test-model",
            dimensions=3,
            batch_size=1,
        )

        self.assertEqual(summary["embedded"], 1)
        self.assertEqual(summary["skipped"], 0)
        self.assertEqual(len(client.embeddings.calls), 1)
        self.assertEqual(len(db.executed), 3)

    async def test_vector_search_returns_chunk_matches(self):
        chunk = _chunk()
        db = _FakeSession([_Result(rows=[(chunk, 0.12)])])
        client = _FakeClient([[0.1, 0.2, 0.3]])

        matches = await search_code_chunks(
            db,
            repo_id="repo-1",
            query="how does run work?",
            limit=3,
            client=client,
            model="test-model",
        )

        self.assertEqual(matches[0]["chunkId"], chunk.id)
        self.assertEqual(matches[0]["fullName"], "app.service.run")
        self.assertEqual(matches[0]["distance"], 0.12)
        self.assertEqual(client.embeddings.calls[0]["input"], ["how does run work?"])

    def test_worker_registers_embedding_task(self):
        self.assertIn(embed_repo_task, WorkerSettings.functions)


if __name__ == "__main__":
    unittest.main()
