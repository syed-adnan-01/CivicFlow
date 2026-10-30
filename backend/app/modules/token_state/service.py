from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import NoResultFound
from datetime import datetime, timezone
import enum
import uuid

try:
    from app.models.queue_token import QueueToken, TokenStatus
    from app.models.queue_event import QueueEvent, EventType
    from app.core.database import Base
except ImportError:
    from backend.app.models.queue_token import QueueToken, TokenStatus
    from backend.app.models.queue_event import QueueEvent, EventType
    from backend.app.core.database import Base

# Define allowed transitions as a set of (from_status, to_status)
ALLOWED_TRANSITIONS = {
    (TokenStatus.WAITING, TokenStatus.CALLED),
    (TokenStatus.CALLED, TokenStatus.WAITING),  # withdraw/reset
    (TokenStatus.CALLED, TokenStatus.SERVING),
    (TokenStatus.SERVING, TokenStatus.ON_HOLD),
    (TokenStatus.ON_HOLD, TokenStatus.SERVING),
    (TokenStatus.SERVING, TokenStatus.COMPLETED),
    (TokenStatus.ON_HOLD, TokenStatus.COMPLETED),
    (TokenStatus.CALLED, TokenStatus.NO_SHOW),
    (TokenStatus.WAITING, TokenStatus.CANCELLED),
}


async def transition_token(
    db: AsyncSession,
    token_id: uuid.UUID,
    target_status: TokenStatus,
    actor_user_id: uuid.UUID,
    reason: str | None = None,
    counter_id: uuid.UUID | None = None,
    expected_status: TokenStatus | None = None,
) -> QueueToken:
    """Central service to transition a queue token.

    Steps performed atomically within a single DB transaction:
    1. Load and lock the token row (SELECT ... FOR UPDATE).
    2. Verify the current status matches ``expected_status`` if provided.
    3. Validate the transition is allowed by ``ALLOWED_TRANSITIONS``.
    4. Apply status-specific side effects (timestamps, counter assignment, etc.).
    5. Insert an immutable ``QueueEvent`` recording the change.
    6. Insert an ``OutboxEvent`` placeholder (to be published asynchronously).
    7. Commit the transaction (caller should commit/rollback).
    """
    # 1. Load and lock the token
    stmt = select(QueueToken).where(QueueToken.id == token_id).with_for_update()
    result = await db.execute(stmt)
    token: QueueToken | None = result.scalars().first()
    if not token:
        raise NoResultFound(f"QueueToken {token_id} not found")

    # 2. Expected status check
    if expected_status and token.status != expected_status:
        raise ValueError(
            f"Token {token_id} status {token.status} does not match expected {expected_status}"
        )

    # 3. Validate transition
    if (token.status, target_status) not in ALLOWED_TRANSITIONS:
        raise ValueError(
            f"Invalid transition from {token.status} to {target_status} for token {token_id}"
        )

    # 4. Apply side effects
    now = datetime.now(timezone.utc)
    from_status = token.status
    token.status = target_status
    if target_status == TokenStatus.CALLED:
        token.called_at = now
        token.last_called_at = now
        token.call_attempt_count = (token.call_attempt_count or 0) + 1
        token.assigned_counter_id = counter_id
    elif target_status == TokenStatus.SERVING:
        token.service_started_at = now
    elif target_status == TokenStatus.ON_HOLD:
        token.hold_started_at = now
    elif target_status == TokenStatus.COMPLETED:
        token.completed_at = now
    elif target_status == TokenStatus.NO_SHOW:
        token.completed_at = now  # treat as completed for audit purposes
    elif target_status == TokenStatus.CANCELLED:
        token.completed_at = now

    # 5. Insert QueueEvent
    event = QueueEvent(
        id=uuid.uuid4(),
        queue_token_id=token.id,
        office_id=token.office_id,
        service_id=token.service_id,
        event_type=EventType.TOKEN_CREATED,  # placeholder, adjust per transition
        from_status=from_status.value if isinstance(from_status, TokenStatus) else str(from_status),
        to_status=target_status.value if isinstance(target_status, TokenStatus) else str(target_status),
        actor_user_id=actor_user_id,
        reason=reason,
        created_at=now,
    )
    db.add(event)

    # 6. Insert OutboxEvent placeholder
    try:
        from app.models.outbox_event import OutboxEvent
    except ImportError:
        try:
            from backend.app.models.outbox_event import OutboxEvent
        except ImportError:
            from sqlalchemy import Column, String, DateTime
            from sqlalchemy.dialects.postgresql import UUID as PGUUID

            class OutboxEvent(Base):
                __tablename__ = "outbox_events"
                id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
                aggregate_type = Column(String, nullable=False)
                aggregate_id = Column(PGUUID(as_uuid=True), nullable=False)
                event_type = Column(String, nullable=False)
                payload = Column(String, nullable=False)  # JSON string
                created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
                published_at = Column(DateTime(timezone=True), nullable=True)

    event_type_val = event.event_type.value if hasattr(event.event_type, "value") else str(event.event_type)
    outbox = OutboxEvent(
        id=uuid.uuid4(),
        aggregate_type="queue_token",
        aggregate_id=token.id,
        event_type=event_type_val,
        payload=str({
            "token_id": str(token.id),
            "from": token.status.value if hasattr(token.status, "value") else str(token.status),
            "to": target_status.value if hasattr(target_status, "value") else str(target_status),
        }),
        created_at=now,
    )
    db.add(outbox)

    return token
