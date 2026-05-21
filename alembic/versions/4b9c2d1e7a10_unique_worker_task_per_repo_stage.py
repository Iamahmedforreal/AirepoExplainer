"""unique worker task per repo stage

Revision ID: 4b9c2d1e7a10
Revises: fe0313a069ec
Create Date: 2026-05-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "4b9c2d1e7a10"
down_revision: Union[str, Sequence[str], None] = "fe0313a069ec"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_worker_tasks_repo_type",
        "worker_tasks",
        ["repoId", "taskTypeId"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_worker_tasks_repo_type",
        "worker_tasks",
        type_="unique",
    )
