"""add growth tracking fields to contacts

Revision ID: b4c3d2e1f6a7
Revises: a3b2c1d4e5f6
Create Date: 2026-05-31 17:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b4c3d2e1f6a7"
down_revision: Union[str, None] = "a3b2c1d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("contacts", sa.Column("foundation_class_status", sa.String(50), nullable=True))
    op.add_column("contacts", sa.Column("baptism_status", sa.String(50), nullable=True))
    op.add_column("contacts", sa.Column("cell_group", sa.String(200), nullable=True))
    op.add_column("contacts", sa.Column("assigned_mentor_id", sa.Integer(), nullable=True))
    op.create_index("ix_contacts_assigned_mentor_id", "contacts", ["assigned_mentor_id"])


def downgrade() -> None:
    op.drop_index("ix_contacts_assigned_mentor_id", table_name="contacts")
    with op.batch_alter_table("contacts") as batch_op:
        batch_op.drop_column("assigned_mentor_id")
        batch_op.drop_column("cell_group")
        batch_op.drop_column("baptism_status")
        batch_op.drop_column("foundation_class_status")
