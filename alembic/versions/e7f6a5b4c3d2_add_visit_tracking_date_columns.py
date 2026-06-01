"""add visit tracking date columns to contacts

Revision ID: e7f6a5b4c3d2
Revises: d6e5f4a3b2c9
Create Date: 2026-05-31 21:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e7f6a5b4c3d2"
down_revision: Union[str, None] = "d6e5f4a3b2c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("contacts", sa.Column("second_visit_date", sa.DateTime(timezone=True), nullable=True))
    op.add_column("contacts", sa.Column("third_visit_date", sa.DateTime(timezone=True), nullable=True))
    op.add_column("contacts", sa.Column("last_attendance_date", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("contacts") as batch_op:
        batch_op.drop_column("last_attendance_date")
        batch_op.drop_column("third_visit_date")
        batch_op.drop_column("second_visit_date")
