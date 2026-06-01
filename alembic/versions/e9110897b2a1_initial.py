"""initial

Revision ID: e9110897b2a1
Revises:
Create Date: 2026-05-30 19:59:38.897915
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e9110897b2a1"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "churches",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("address", sa.String(500), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_churches_id", "churches", ["id"])

    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_roles_id", "roles", ["id"])

    op.create_table(
        "branches",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("church_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("location", sa.String(500), nullable=True),
        sa.Column("pastor_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["church_id"], ["churches.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_branches_church_id", "branches", ["church_id"])
    op.create_index("ix_branches_id", "branches", ["id"])

    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("permission_key", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("role_id", "permission_key", name="uq_role_permission"),
    )
    op.create_index("ix_permissions_id", "permissions", ["id"])
    op.create_index("ix_permissions_role_id", "permissions", ["role_id"])

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("church_id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("hashed_password", sa.String(255), nullable=True),
        sa.Column("role_id", sa.Integer(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["church_id"], ["churches.id"]),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"]),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_branch_id", "users", ["branch_id"])
    op.create_index("ix_users_church_id", "users", ["church_id"])
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_role_id", "users", ["role_id"])

    contact_category_enum = sa.Enum(
        "first_timer", "new_convert", "outreach_convert", "member", "other", name="contact_category"
    )
    contact_source_enum = sa.Enum(
        "service", "outreach", "online", "referral", "other", name="contact_source"
    )
    contact_status_enum = sa.Enum(
        "new", "contacted", "follow_up", "attending", "inactive", "completed", name="contact_status"
    )

    op.create_table(
        "contacts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("church_id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("gender", sa.String(20), nullable=True),
        sa.Column("age_group", sa.String(50), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("category", contact_category_enum, nullable=False),
        sa.Column("source", contact_source_enum, nullable=True),
        sa.Column("status", contact_status_enum, nullable=False, server_default="new"),
        sa.Column("assigned_worker_id", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("consent_given", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("opt_out", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["church_id"], ["churches.id"]),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"]),
        sa.ForeignKeyConstraint(["assigned_worker_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_contacts_assigned_worker_id", "contacts", ["assigned_worker_id"])
    op.create_index("ix_contacts_branch_id", "contacts", ["branch_id"])
    op.create_index("ix_contacts_category", "contacts", ["category"])
    op.create_index("ix_contacts_church_id", "contacts", ["church_id"])
    op.create_index("ix_contacts_id", "contacts", ["id"])
    op.create_index("ix_contacts_phone", "contacts", ["phone"])
    op.create_index("ix_contacts_status", "contacts", ["status"])

    op.create_table(
        "service_units",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("church_id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("leader_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["church_id"], ["churches.id"]),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"]),
        sa.ForeignKeyConstraint(["leader_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_service_units_branch_id", "service_units", ["branch_id"])
    op.create_index("ix_service_units_church_id", "service_units", ["church_id"])
    op.create_index("ix_service_units_id", "service_units", ["id"])

    op.create_table(
        "message_templates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("church_id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column(
            "category",
            sa.Enum("first_timer", "new_convert", "outreach", "service_unit", "general", name="template_category"),
            nullable=False,
        ),
        sa.Column(
            "channel",
            sa.Enum("whatsapp", "sms", "email", "manual", name="template_channel"),
            nullable=False,
            server_default="manual",
        ),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("approved", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["church_id"], ["churches.id"]),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_message_templates_branch_id", "message_templates", ["branch_id"])
    op.create_index("ix_message_templates_church_id", "message_templates", ["church_id"])
    op.create_index("ix_message_templates_id", "message_templates", ["id"])

    op.create_table(
        "follow_up_tasks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("contact_id", sa.Integer(), nullable=False),
        sa.Column("assigned_to", sa.Integer(), nullable=True),
        sa.Column(
            "task_type",
            sa.Enum("call", "message", "visit", "invite", "other", name="task_type"),
            nullable=False,
        ),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            sa.Enum("pending", "in_progress", "completed", "overdue", name="task_status"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "priority",
            sa.Enum("low", "medium", "high", name="task_priority"),
            nullable=False,
            server_default="medium",
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"]),
        sa.ForeignKeyConstraint(["assigned_to"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_follow_up_tasks_assigned_to", "follow_up_tasks", ["assigned_to"])
    op.create_index("ix_follow_up_tasks_contact_id", "follow_up_tasks", ["contact_id"])
    op.create_index("ix_follow_up_tasks_due_date", "follow_up_tasks", ["due_date"])
    op.create_index("ix_follow_up_tasks_id", "follow_up_tasks", ["id"])
    op.create_index("ix_follow_up_tasks_status", "follow_up_tasks", ["status"])

    op.create_table(
        "communication_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("contact_id", sa.Integer(), nullable=False),
        sa.Column(
            "channel",
            sa.Enum("whatsapp", "sms", "call", "email", "manual", name="communication_channel"),
            nullable=False,
        ),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("provider", sa.String(100), nullable=True),
        sa.Column(
            "status",
            sa.Enum("sent", "delivered", "failed", "read", name="communication_status"),
            nullable=False,
            server_default="sent",
        ),
        sa.Column("sent_by", sa.Integer(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"]),
        sa.ForeignKeyConstraint(["sent_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_communication_logs_contact_id", "communication_logs", ["contact_id"])
    op.create_index("ix_communication_logs_id", "communication_logs", ["id"])

    op.create_table(
        "reminders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column(
            "reminder_type",
            sa.Enum("due", "second", "escalation", name="reminder_type"),
            nullable=False,
        ),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            sa.Enum("pending", "sent", "failed", name="reminder_status"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["follow_up_tasks.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reminders_id", "reminders", ["id"])
    op.create_index("ix_reminders_task_id", "reminders", ["task_id"])

    op.create_table(
        "workflows",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("church_id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column(
            "trigger_event",
            sa.Enum(
                "contact_created", "task_completed", "no_response", "overdue", "contact_reengaged",
                name="workflow_trigger",
            ),
            nullable=False,
        ),
        sa.Column(
            "target_category",
            sa.Enum("first_timer", "new_convert", "outreach_convert", "member", "all", name="workflow_target"),
            nullable=False,
        ),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("rules_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["church_id"], ["churches.id"]),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_workflows_branch_id", "workflows", ["branch_id"])
    op.create_index("ix_workflows_church_id", "workflows", ["church_id"])
    op.create_index("ix_workflows_id", "workflows", ["id"])

    from alembic import context as migration_context
    if migration_context.get_context().dialect.name != "sqlite":
        op.create_foreign_key(
            "fk_branches_pastor_id_users",
            "branches", "users", ["pastor_id"], ["id"],
        )


def downgrade() -> None:
    from alembic import context as migration_context
    if migration_context.get_context().dialect.name != "sqlite":
        op.drop_constraint("fk_branches_pastor_id_users", "branches", type_="foreignkey")

    op.drop_index("ix_workflows_id", table_name="workflows")
    op.drop_index("ix_workflows_church_id", table_name="workflows")
    op.drop_index("ix_workflows_branch_id", table_name="workflows")
    op.drop_table("workflows")

    op.drop_index("ix_reminders_task_id", table_name="reminders")
    op.drop_index("ix_reminders_id", table_name="reminders")
    op.drop_table("reminders")

    op.drop_index("ix_communication_logs_id", table_name="communication_logs")
    op.drop_index("ix_communication_logs_contact_id", table_name="communication_logs")
    op.drop_table("communication_logs")

    op.drop_index("ix_follow_up_tasks_status", table_name="follow_up_tasks")
    op.drop_index("ix_follow_up_tasks_id", table_name="follow_up_tasks")
    op.drop_index("ix_follow_up_tasks_due_date", table_name="follow_up_tasks")
    op.drop_index("ix_follow_up_tasks_contact_id", table_name="follow_up_tasks")
    op.drop_index("ix_follow_up_tasks_assigned_to", table_name="follow_up_tasks")
    op.drop_table("follow_up_tasks")

    op.drop_index("ix_message_templates_id", table_name="message_templates")
    op.drop_index("ix_message_templates_church_id", table_name="message_templates")
    op.drop_index("ix_message_templates_branch_id", table_name="message_templates")
    op.drop_table("message_templates")

    op.drop_index("ix_service_units_id", table_name="service_units")
    op.drop_index("ix_service_units_church_id", table_name="service_units")
    op.drop_index("ix_service_units_branch_id", table_name="service_units")
    op.drop_table("service_units")

    op.drop_index("ix_contacts_status", table_name="contacts")
    op.drop_index("ix_contacts_phone", table_name="contacts")
    op.drop_index("ix_contacts_id", table_name="contacts")
    op.drop_index("ix_contacts_church_id", table_name="contacts")
    op.drop_index("ix_contacts_category", table_name="contacts")
    op.drop_index("ix_contacts_branch_id", table_name="contacts")
    op.drop_index("ix_contacts_assigned_worker_id", table_name="contacts")
    op.drop_table("contacts")

    op.drop_index("ix_users_role_id", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_index("ix_users_church_id", table_name="users")
    op.drop_index("ix_users_branch_id", table_name="users")
    op.drop_table("users")

    op.drop_index("ix_permissions_role_id", table_name="permissions")
    op.drop_index("ix_permissions_id", table_name="permissions")
    op.drop_table("permissions")

    op.drop_index("ix_branches_id", table_name="branches")
    op.drop_index("ix_branches_church_id", table_name="branches")
    op.drop_table("branches")

    op.drop_index("ix_roles_id", table_name="roles")
    op.drop_table("roles")

    op.drop_index("ix_churches_id", table_name="churches")
    op.drop_table("churches")
