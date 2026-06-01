"""add foundation class date fields

Revision ID: d6e5f4a3b2c9
Revises: c5d4e3f2a1b8
Create Date: 2026-05-31 20:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d6e5f4a3b2c9"
down_revision: Union[str, None] = "c5d4e3f2a1b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("contacts", sa.Column("foundation_class_start_date", sa.DateTime(timezone=True), nullable=True))
    op.add_column("contacts", sa.Column("foundation_class_completion_date", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("contacts") as batch_op:
        batch_op.drop_column("foundation_class_completion_date")
        batch_op.drop_column("foundation_class_start_date")
