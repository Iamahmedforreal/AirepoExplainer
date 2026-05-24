"""add code_connections

Revision ID: a1b2c3d4e5f6
Revises: 4b9c2d1e7a10
Create Date: 2026-05-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "4b9c2d1e7a10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "code_connections",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("repoId", sa.String(), nullable=False),
        sa.Column("sourceChunkId", sa.String(), nullable=False),
        sa.Column("targetSymbol", sa.String(), nullable=False),
        sa.Column("targetChunkId", sa.String(), nullable=True),
        sa.Column("connectionType", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["repoId"], ["repositories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sourceChunkId"], ["code_chunks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["targetChunkId"], ["code_chunks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_code_connections_repoId", "code_connections", ["repoId"], unique=False)
    op.create_index("ix_code_connections_sourceChunkId", "code_connections", ["sourceChunkId"], unique=False)
    op.create_index("ix_code_connections_targetChunkId", "code_connections", ["targetChunkId"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_code_connections_targetChunkId", table_name="code_connections")
    op.drop_index("ix_code_connections_sourceChunkId", table_name="code_connections")
    op.drop_index("ix_code_connections_repoId", table_name="code_connections")
    op.drop_table("code_connections")
