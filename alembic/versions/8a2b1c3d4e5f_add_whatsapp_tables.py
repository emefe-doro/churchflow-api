"""add whatsapp tables

Revision ID: 8a2b1c3d4e5f
Revises: e9110897b2a1
Create Date: 2026-05-30 20:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



revision: str = '8a2b1c3d4e5f'
down_revision: Union[str, None] = 'e9110897b2a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "whatsapp_messages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("church_id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("contact_id", sa.Integer(), nullable=False),
        sa.Column("template_id", sa.Integer(), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "draft", "pending_approval", "approved", "rejected",
                "queued", "sent", "delivered", "read", "failed",
                name="whatsapp_message_status",
            ),
            nullable=False,
            server_default="draft",
        ),
        sa.Column(
            "priority",
            sa.Enum("low", "normal", "high", name="whatsapp_message_priority"),
            nullable=False,
            server_default="normal",
        ),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("approved_by", sa.Integer(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejected_reason", sa.Text(), nullable=True),
        sa.Column("external_message_id", sa.String(100), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["church_id"], ["churches.id"]),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"]),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"]),
        sa.ForeignKeyConstraint(["template_id"], ["message_templates.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_whatsapp_messages_branch_id"), "whatsapp_messages", ["branch_id"])
    op.create_index(op.f("ix_whatsapp_messages_church_id"), "whatsapp_messages", ["church_id"])
    op.create_index(op.f("ix_whatsapp_messages_contact_id"), "whatsapp_messages", ["contact_id"])
    op.create_index(op.f("ix_whatsapp_messages_external_message_id"), "whatsapp_messages", ["external_message_id"])
    op.create_index(op.f("ix_whatsapp_messages_id"), "whatsapp_messages", ["id"])
    op.create_index(op.f("ix_whatsapp_messages_status"), "whatsapp_messages", ["status"])

    op.create_table(
        "whatsapp_queue_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "processing", "completed", "failed", name="queue_item_status"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("external_message_id", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["whatsapp_messages.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_whatsapp_queue_items_id"), "whatsapp_queue_items", ["id"])
    op.create_index(op.f("ix_whatsapp_queue_items_message_id"), "whatsapp_queue_items", ["message_id"])
    op.create_index(op.f("ix_whatsapp_queue_items_status"), "whatsapp_queue_items", ["status"])

    op.create_table(
        "whatsapp_delivery_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("external_message_id", sa.String(100), nullable=True),
        sa.Column(
            "status",
            sa.Enum("sent", "delivered", "read", "failed", "deleted", name="delivery_log_status"),
            nullable=False,
        ),
        sa.Column("event_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column("error_code", sa.String(50), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["whatsapp_messages.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_whatsapp_delivery_logs_external_message_id"), "whatsapp_delivery_logs", ["external_message_id"])
    op.create_index(op.f("ix_whatsapp_delivery_logs_id"), "whatsapp_delivery_logs", ["id"])
    op.create_index(op.f("ix_whatsapp_delivery_logs_message_id"), "whatsapp_delivery_logs", ["message_id"])

    op.create_table(
        "whatsapp_opt_outs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("church_id", sa.Integer(), nullable=False),
        sa.Column("contact_id", sa.Integer(), nullable=True),
        sa.Column("phone_number", sa.String(20), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "source",
            sa.Enum("manual", "webhook", "incoming_message", name="opt_out_source"),
            nullable=False,
            server_default="manual",
        ),
        sa.Column("opted_out_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["church_id"], ["churches.id"]),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_whatsapp_opt_outs_church_id"), "whatsapp_opt_outs", ["church_id"])
    op.create_index(op.f("ix_whatsapp_opt_outs_contact_id"), "whatsapp_opt_outs", ["contact_id"])
    op.create_index(op.f("ix_whatsapp_opt_outs_id"), "whatsapp_opt_outs", ["id"])
    op.create_index(op.f("ix_whatsapp_opt_outs_phone_number"), "whatsapp_opt_outs", ["phone_number"])


def downgrade() -> None:
    op.drop_index(op.f("ix_whatsapp_opt_outs_phone_number"), table_name="whatsapp_opt_outs")
    op.drop_index(op.f("ix_whatsapp_opt_outs_id"), table_name="whatsapp_opt_outs")
    op.drop_index(op.f("ix_whatsapp_opt_outs_contact_id"), table_name="whatsapp_opt_outs")
    op.drop_index(op.f("ix_whatsapp_opt_outs_church_id"), table_name="whatsapp_opt_outs")
    op.drop_table("whatsapp_opt_outs")
    op.execute("DROP TYPE IF EXISTS opt_out_source")

    op.drop_index(op.f("ix_whatsapp_delivery_logs_message_id"), table_name="whatsapp_delivery_logs")
    op.drop_index(op.f("ix_whatsapp_delivery_logs_id"), table_name="whatsapp_delivery_logs")
    op.drop_index(op.f("ix_whatsapp_delivery_logs_external_message_id"), table_name="whatsapp_delivery_logs")
    op.drop_table("whatsapp_delivery_logs")
    op.execute("DROP TYPE IF EXISTS delivery_log_status")

    op.drop_index(op.f("ix_whatsapp_queue_items_status"), table_name="whatsapp_queue_items")
    op.drop_index(op.f("ix_whatsapp_queue_items_message_id"), table_name="whatsapp_queue_items")
    op.drop_index(op.f("ix_whatsapp_queue_items_id"), table_name="whatsapp_queue_items")
    op.drop_table("whatsapp_queue_items")
    op.execute("DROP TYPE IF EXISTS queue_item_status")

    op.drop_index(op.f("ix_whatsapp_messages_status"), table_name="whatsapp_messages")
    op.drop_index(op.f("ix_whatsapp_messages_id"), table_name="whatsapp_messages")
    op.drop_index(op.f("ix_whatsapp_messages_external_message_id"), table_name="whatsapp_messages")
    op.drop_index(op.f("ix_whatsapp_messages_contact_id"), table_name="whatsapp_messages")
    op.drop_index(op.f("ix_whatsapp_messages_church_id"), table_name="whatsapp_messages")
    op.drop_index(op.f("ix_whatsapp_messages_branch_id"), table_name="whatsapp_messages")
    op.drop_table("whatsapp_messages")
    op.execute("DROP TYPE IF EXISTS whatsapp_message_status")
    op.execute("DROP TYPE IF EXISTS whatsapp_message_priority")
