"""semantic chunk metadata

Revision ID: d2f4a6b8c9e1
Revises: c8d9e0f1a2b3
Create Date: 2026-06-02 18:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "d2f4a6b8c9e1"
down_revision: Union[str, Sequence[str], None] = "c8d9e0f1a2b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "code_chunks",
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.add_column("code_connections", sa.Column("sourceLine", sa.Integer(), nullable=True))
    op.add_column("code_connections", sa.Column("targetPath", sa.String(), nullable=True))
    op.add_column(
        "code_connections",
        sa.Column("confidence", sa.String(), nullable=False, server_default="unresolved"),
    )
    op.add_column(
        "code_connections",
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.alter_column("code_chunks", "metadata", server_default=None)
    op.alter_column("code_connections", "confidence", server_default=None)
    op.alter_column("code_connections", "metadata", server_default=None)


def downgrade() -> None:
    op.drop_column("code_connections", "metadata")
    op.drop_column("code_connections", "confidence")
    op.drop_column("code_connections", "targetPath")
    op.drop_column("code_connections", "sourceLine")
    op.drop_column("code_chunks", "metadata")
