"""add outcome to communication logs

Revision ID: a3b2c1d4e5f6
Revises: 8a2b1c3d4e5f
Create Date: 2026-05-31 16:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a3b2c1d4e5f6"
down_revision: Union[str, None] = "8a2b1c3d4e5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "communication_logs",
        sa.Column("outcome", sa.String(100), nullable=True),
    )


def downgrade() -> None:
    with op.batch_alter_table("communication_logs") as batch_op:
        batch_op.drop_column("outcome")
