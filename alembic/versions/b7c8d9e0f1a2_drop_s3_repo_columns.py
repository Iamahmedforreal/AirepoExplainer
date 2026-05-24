"""drop s3 repository columns

Revision ID: b7c8d9e0f1a2
Revises: a1b2c3d4e5f6
Create Date: 2026-05-24 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "b7c8d9e0f1a2"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table: str, column: str) -> bool:
    bind = op.get_bind()
    inspector = inspect(bind)
    return column in {col["name"] for col in inspector.get_columns(table)}


def upgrade() -> None:
    if _column_exists("repositories", "sourceFileCount"):
        op.drop_column("repositories", "sourceFileCount")
    if _column_exists("repositories", "s3Prefix"):
        op.drop_column("repositories", "s3Prefix")
    if _column_exists("repositories", "s3Bucket"):
        op.drop_column("repositories", "s3Bucket")


def downgrade() -> None:
    if not _column_exists("repositories", "s3Bucket"):
        op.add_column("repositories", sa.Column("s3Bucket", sa.String(), nullable=True))
    if not _column_exists("repositories", "s3Prefix"):
        op.add_column("repositories", sa.Column("s3Prefix", sa.String(), nullable=True))
    if not _column_exists("repositories", "sourceFileCount"):
        op.add_column("repositories", sa.Column("sourceFileCount", sa.Integer(), nullable=True))
