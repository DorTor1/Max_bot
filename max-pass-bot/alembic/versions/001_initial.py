"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-05-24

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("max_user_id", sa.String(64), nullable=False, unique=True),
        sa.Column("display_name", sa.String(256), nullable=False),
        sa.Column(
            "role",
            sa.Enum("initiator", "admin", "tech_admin", name="roleenum"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "zones",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0"),
    )
    op.create_table(
        "consent_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("doc_version", sa.String(32), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("max_user_id", sa.String(64), nullable=False),
        sa.Column("display_name", sa.String(256), nullable=False),
        sa.Column("ip_meta", postgresql.JSONB(), nullable=True),
        sa.UniqueConstraint("user_id", "doc_version"),
    )
    op.create_table(
        "requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("number", sa.String(32), nullable=False, unique=True),
        sa.Column("guest_full_name", sa.String(120), nullable=False),
        sa.Column("visit_date", sa.Date(), nullable=False),
        sa.Column(
            "visit_time",
            sa.Enum("morning", "day", "evening", name="visittimeenum"),
            nullable=False,
        ),
        sa.Column("zone_id", sa.String(64), sa.ForeignKey("zones.id"), nullable=False),
        sa.Column("purpose", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "approved",
                "rejected",
                "clarification",
                "cancelled",
                "closed",
                name="requeststatusenum",
            ),
            nullable=False,
        ),
        sa.Column("initiator_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("decision_by_id", sa.String(64), nullable=True),
        sa.Column("decision_by_name", sa.String(256), nullable=True),
        sa.Column("decision_comment", sa.Text(), nullable=True),
        sa.Column(
            "reject_reason",
            sa.Enum(
                "INVALID_DATA",
                "SECURITY_POLICY",
                "DUPLICATE",
                "OTHER",
                name="rejectreasonenum",
            ),
            nullable=True,
        ),
        sa.Column("clarification_question", sa.Text(), nullable=True),
        sa.Column("clarification_answer", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_requests_initiator", "requests", ["initiator_user_id", "updated_at"])
    op.create_index("ix_requests_status", "requests", ["status", "updated_at"])
    op.create_table(
        "audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("requests.id"), nullable=True),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("actor_max_user_id", sa.String(64), nullable=False),
        sa.Column("actor_display_name", sa.String(256), nullable=False),
        sa.Column("payload", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "bot_sessions",
        sa.Column("max_user_id", sa.String(64), primary_key=True),
        sa.Column("step", sa.String(64), nullable=False),
        sa.Column("draft", postgresql.JSONB(), server_default="{}"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "request_number_seq",
        sa.Column("year", sa.Integer(), primary_key=True),
        sa.Column("last_value", sa.Integer(), server_default="100"),
    )


def downgrade() -> None:
    op.drop_table("request_number_seq")
    op.drop_table("bot_sessions")
    op.drop_table("audit_events")
    op.drop_index("ix_requests_status", "requests")
    op.drop_index("ix_requests_initiator", "requests")
    op.drop_table("requests")
    op.drop_table("consent_records")
    op.drop_table("zones")
    op.drop_table("users")
    for name in ("rejectreasonenum", "requeststatusenum", "visittimeenum", "roleenum"):
        op.execute(f"DROP TYPE IF EXISTS {name}")
