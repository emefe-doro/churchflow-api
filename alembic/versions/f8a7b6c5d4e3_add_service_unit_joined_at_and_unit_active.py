"""add service_unit_joined_at and unit_active to contacts

Revision ID: f8a7b6c5d4e3
Revises: e7f6a5b4c3d2
Create Date: 2026-06-01 09:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f8a7b6c5d4e3"
down_revision: Union[str, None] = "e7f6a5b4c3d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("contacts") as batch_op:
        batch_op.add_column(sa.Column("service_unit_joined_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("unit_active", sa.Boolean(), nullable=False, server_default=sa.text("1")))


def downgrade() -> None:
    with op.batch_alter_table("contacts") as batch_op:
        batch_op.drop_column("unit_active")
        batch_op.drop_column("service_unit_joined_at")
