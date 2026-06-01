"""add service_unit_id to contacts

Revision ID: c5d4e3f2a1b8
Revises: b4c3d2e1f6a7
Create Date: 2026-05-31 19:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c5d4e3f2a1b8"
down_revision: Union[str, None] = "b4c3d2e1f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("contacts", sa.Column("service_unit_id", sa.Integer(), nullable=True))
    op.create_index("ix_contacts_service_unit_id", "contacts", ["service_unit_id"])


def downgrade() -> None:
    op.drop_index("ix_contacts_service_unit_id", table_name="contacts")
    with op.batch_alter_table("contacts") as batch_op:
        batch_op.drop_column("service_unit_id")
