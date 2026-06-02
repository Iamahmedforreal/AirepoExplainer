"""repository pipeline metadata columns

Revision ID: c8d9e0f1a2b3
Revises: 26c6df937faf
Create Date: 2026-05-26 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c8d9e0f1a2b3"
down_revision: Union[str, Sequence[str], None] = "26c6df937faf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("repositories", sa.Column("clonePath", sa.String(), nullable=True))
    op.add_column("repositories", sa.Column("sourceFileCount", sa.Integer(), nullable=True))
    op.add_column("repositories", sa.Column("chunkCount", sa.Integer(), nullable=True))
    op.add_column("repositories", sa.Column("connectionCount", sa.Integer(), nullable=True))
    op.add_column("repositories", sa.Column("indexedAt", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("repositories", "indexedAt")
    op.drop_column("repositories", "connectionCount")
    op.drop_column("repositories", "chunkCount")
    op.drop_column("repositories", "sourceFileCount")
    op.drop_column("repositories", "clonePath")
