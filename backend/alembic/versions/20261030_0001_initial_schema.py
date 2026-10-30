"""initial_schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-10-30 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Offices table
    op.create_table(
        "offices",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("address", sa.String(length=500), nullable=True),
        sa.Column("timezone", sa.String(length=64), server_default="Asia/Kolkata", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # 2. Users table (identities and roles)
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("firebase_uid", sa.String(length=128), nullable=False),
        sa.Column("phone_number", sa.String(length=32), nullable=True),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("role", sa.String(length=32), server_default="CITIZEN", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("office_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["office_id"], ["offices.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_firebase_uid"), "users", ["firebase_uid"], unique=True)
    op.create_index(op.f("ix_users_phone_number"), "users", ["phone_number"], unique=False)
    op.create_index(op.f("ix_users_role"), "users", ["role"], unique=False)

    # 3. Services table
    op.create_table(
        "services",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("office_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=True),
        sa.Column("average_service_duration_minutes", sa.Integer(), server_default="15", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["office_id"], ["offices.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("office_id", "name", name="uq_service_office_name"),
    )
    op.create_index(op.f("ix_services_office_id"), "services", ["office_id"], unique=False)

    # 4. Queue Policy table
    op.create_table(
        "queue_policy",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("office_id", sa.UUID(), nullable=False),
        sa.Column("service_id", sa.UUID(), nullable=True),
        sa.Column("slot_duration_minutes", sa.Integer(), server_default="15", nullable=False),
        sa.Column("walk_in_share", sa.Float(), server_default="0.20", nullable=False),
        sa.Column("max_walk_in_wait_minutes", sa.Integer(), server_default="60", nullable=False),
        sa.Column("checkin_open_minutes", sa.Integer(), server_default="15", nullable=False),
        sa.Column("checkin_close_minutes", sa.Integer(), server_default="10", nullable=False),
        sa.Column("policy_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_by", sa.UUID(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["office_id"], ["offices.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["service_id"], ["services.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_queue_policy_office_id"), "queue_policy", ["office_id"], unique=False)
    op.create_index(op.f("ix_queue_policy_service_id"), "queue_policy", ["service_id"], unique=False)

    # 5. Appointment Slots table
    op.create_table(
        "appointment_slots",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("office_id", sa.UUID(), nullable=False),
        sa.Column("service_id", sa.UUID(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("operating_date", sa.Date(), nullable=False),
        sa.Column("block_start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("capacity", sa.Integer(), server_default="0", nullable=False),
        sa.Column("booked_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("status", sa.String(length=32), server_default="OPEN", nullable=False),
        sa.Column("capacity_policy_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("booked_count >= 0", name="chk_slot_booked_count_non_negative"),
        sa.CheckConstraint("capacity >= 0", name="chk_slot_capacity_non_negative"),
        sa.CheckConstraint("booked_count <= capacity", name="chk_slot_booked_count_le_capacity"),
        sa.CheckConstraint("ends_at > starts_at", name="chk_slot_ends_at_after_starts_at"),
        sa.ForeignKeyConstraint(["office_id"], ["offices.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["service_id"], ["services.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("office_id", "service_id", "starts_at", name="uq_slot_office_service_starts_at"),
    )
    op.create_index(op.f("ix_appointment_slots_office_id"), "appointment_slots", ["office_id"], unique=False)
    op.create_index(op.f("ix_appointment_slots_service_id"), "appointment_slots", ["service_id"], unique=False)
    op.create_index(op.f("ix_appointment_slots_starts_at"), "appointment_slots", ["starts_at"], unique=False)
    op.create_index(op.f("ix_appointment_slots_operating_date"), "appointment_slots", ["operating_date"], unique=False)
    op.create_index(op.f("ix_appointment_slots_status"), "appointment_slots", ["status"], unique=False)
    op.create_index("ix_slots_lookup", "appointment_slots", ["office_id", "service_id", "operating_date", "status"], unique=False)

    # 6. Appointments table
    op.create_table(
        "appointments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("citizen_id", sa.UUID(), nullable=False),
        sa.Column("office_id", sa.UUID(), nullable=False),
        sa.Column("service_id", sa.UUID(), nullable=False),
        sa.Column("slot_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="BOOKED", nullable=False),
        sa.Column("booking_reference", sa.String(length=64), nullable=True),
        sa.Column("slot_start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("check_in_open_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("check_in_close_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rescheduled_from_id", sa.UUID(), nullable=True),
        sa.Column("rescheduled_to_id", sa.UUID(), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancellation_reason", sa.String(length=500), nullable=True),
        sa.Column("no_show_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("no_show_reason", sa.String(length=500), nullable=True),
        sa.Column("reminder_status", sa.String(length=32), server_default="PENDING", nullable=False),
        sa.Column("qr_rotated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["citizen_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["office_id"], ["offices.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["service_id"], ["services.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["slot_id"], ["appointment_slots.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["rescheduled_from_id"], ["appointments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["rescheduled_to_id"], ["appointments.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("booking_reference", name="uq_appointment_booking_reference"),
    )
    op.create_index(op.f("ix_appointments_citizen_id"), "appointments", ["citizen_id"], unique=False)
    op.create_index(op.f("ix_appointments_office_id"), "appointments", ["office_id"], unique=False)
    op.create_index(op.f("ix_appointments_service_id"), "appointments", ["service_id"], unique=False)
    op.create_index(op.f("ix_appointments_slot_id"), "appointments", ["slot_id"], unique=False)
    op.create_index(op.f("ix_appointments_status"), "appointments", ["status"], unique=False)
    op.create_index(op.f("ix_appointments_slot_start_at"), "appointments", ["slot_start_at"], unique=False)
    op.create_index("ix_appointments_citizen_history", "appointments", ["citizen_id", "created_at"], unique=False)
    op.create_index(
        "uq_active_citizen_slot_booking",
        "appointments",
        ["citizen_id", "office_id", "service_id", "slot_id"],
        unique=True,
        postgresql_where=sa.text("status = 'BOOKED'"),
    )

    # 7. Check-in References (QR hashes) table
    op.create_table(
        "checkin_references",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("appointment_id", sa.UUID(), nullable=False),
        sa.Column("reference_hash", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("invalidated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("invalidation_reason", sa.String(length=64), nullable=True),
        sa.Column("created_by_user_id", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(["appointment_id"], ["appointments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_checkin_references_appointment_id"), "checkin_references", ["appointment_id"], unique=False)
    op.create_index(op.f("ix_checkin_references_reference_hash"), "checkin_references", ["reference_hash"], unique=True)
    op.create_index("ix_checkin_ref_active", "checkin_references", ["appointment_id", "invalidated_at", "used_at"], unique=False)

    # 8. Idempotency Keys table
    op.create_table(
        "idempotency_keys",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("actor_id", sa.UUID(), nullable=False),
        sa.Column("scope", sa.String(length=64), nullable=False),
        sa.Column("key_hash", sa.String(length=128), nullable=False),
        sa.Column("request_hash", sa.String(length=128), nullable=False),
        sa.Column("response_status", sa.Integer(), nullable=True),
        sa.Column("response_body", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("actor_id", "scope", "key_hash", name="uq_idempotency_actor_scope_key"),
    )
    op.create_index(op.f("ix_idempotency_keys_actor_id"), "idempotency_keys", ["actor_id"], unique=False)
    op.create_index(op.f("ix_idempotency_keys_scope"), "idempotency_keys", ["scope"], unique=False)
    op.create_index(op.f("ix_idempotency_keys_key_hash"), "idempotency_keys", ["key_hash"], unique=False)
    op.create_index(op.f("ix_idempotency_keys_expires_at"), "idempotency_keys", ["expires_at"], unique=False)

    # 9. Audit Events table
    op.create_table(
        "audit_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("actor_id", sa.UUID(), nullable=True),
        sa.Column("actor_role", sa.String(length=32), nullable=True),
        sa.Column("office_id", sa.UUID(), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("resource_type", sa.String(length=64), nullable=False),
        sa.Column("resource_id", sa.String(length=128), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_events_actor_id"), "audit_events", ["actor_id"], unique=False)
    op.create_index(op.f("ix_audit_events_office_id"), "audit_events", ["office_id"], unique=False)
    op.create_index(op.f("ix_audit_events_action"), "audit_events", ["action"], unique=False)
    op.create_index(op.f("ix_audit_events_resource_type"), "audit_events", ["resource_type"], unique=False)
    op.create_index(op.f("ix_audit_events_timestamp"), "audit_events", ["timestamp"], unique=False)


def downgrade() -> None:
    op.drop_table("audit_events")
    op.drop_table("idempotency_keys")
    op.drop_table("checkin_references")
    op.drop_table("appointments")
    op.drop_table("appointment_slots")
    op.drop_table("queue_policy")
    op.drop_table("services")
    op.drop_table("users")
    op.drop_table("offices")
