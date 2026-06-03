"""code chunk embeddings

Revision ID: e3f5a7b9c0d2
Revises: d2f4a6b8c9e1
Create Date: 2026-06-03 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


revision: str = "e3f5a7b9c0d2"
down_revision: Union[str, Sequence[str], None] = "d2f4a6b8c9e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "code_chunk_embeddings",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("repoId", sa.String(), nullable=False),
        sa.Column("chunkId", sa.String(), nullable=False),
        sa.Column("embeddingModel", sa.String(), nullable=False),
        sa.Column("embeddingDimensions", sa.Integer(), nullable=False),
        sa.Column("contentHash", sa.String(), nullable=False),
        sa.Column("vector", Vector(1536), nullable=False),
        sa.Column("createdAt", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["chunkId"], ["code_chunks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["repoId"], ["repositories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chunkId", "embeddingModel", name="uq_code_chunk_embeddings_chunk_model"),
    )
    op.create_index("ix_code_chunk_embeddings_repoId", "code_chunk_embeddings", ["repoId"])
    op.create_index("ix_code_chunk_embeddings_chunkId", "code_chunk_embeddings", ["chunkId"])
    op.create_index("ix_code_chunk_embeddings_model", "code_chunk_embeddings", ["embeddingModel"])


def downgrade() -> None:
    op.drop_index("ix_code_chunk_embeddings_model", table_name="code_chunk_embeddings")
    op.drop_index("ix_code_chunk_embeddings_chunkId", table_name="code_chunk_embeddings")
    op.drop_index("ix_code_chunk_embeddings_repoId", table_name="code_chunk_embeddings")
    op.drop_table("code_chunk_embeddings")
