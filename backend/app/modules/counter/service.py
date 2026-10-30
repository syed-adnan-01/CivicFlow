from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from backend.app.models.queue_token import QueueToken, TokenStatus
from backend.app.models.counter import Counter
from backend.app.repositories.queue import QueueTokenRepository
from backend.app.repositories.counter import CounterRepository
from backend.app.modules.token_state.service import transition_token
from datetime import datetime, timezone
import uuid

# Helper to lock rows for update
async def lock_counter_and_token(db: AsyncSession, counter_id: UUID, token_id: UUID | None = None):
    # Lock the counter row
    stmt_counter = select(Counter).where(Counter.id == counter_id).with_for_update()
    result_counter = await db.execute(stmt_counter)
    counter = result_counter.scalars().first()
    if not counter:
        raise ValueError(f"Counter {counter_id} not found")
    token = None
    if token_id:
        stmt_token = select(QueueToken).where(QueueToken.id == token_id).with_for_update()
        result_token = await db.execute(stmt_token)
        token = result_token.scalars().first()
        if not token:
            raise ValueError(f"QueueToken {token_id} not found")
    return counter, token

async def call_next(db: AsyncSession, repo: CounterRepository, counter_id: UUID):
    # Ensure counter eligibility
    counter = await repo.get_by_id(counter_id)
    if not await repo.is_eligible(counter):
        raise ValueError("Counter not eligible for call-next")
    # Fetch next waiting token (service‑compatible and same office)
    token_repo = QueueTokenRepository(db)
    stmt = select(QueueToken).where(
        QueueToken.office_id == counter.office_id,
        QueueToken.service_id == counter.service_id,
        QueueToken.status == TokenStatus.WAITING,
    ).order_by(QueueToken.created_at).limit(1).with_for_update()
    result = await db.execute(stmt)
    token = result.scalars().first()
    if not token:
        raise ValueError("No waiting token available for this counter")
    # Lock both rows
    await lock_counter_and_token(db, counter_id, token.id)
    # Transition token to CALLED and assign to counter atomically
    await transition_token(
        db=db,
        token_id=token.id,
        target_status=TokenStatus.CALLED,
        actor_user_id=uuid.uuid4(),  # placeholder, replace with actual user id
        counter_id=counter.id,
        expected_status=TokenStatus.WAITING,
    )
    await repo.assign_token(counter, token)
    await db.commit()
    return {"token_id": str(token.id)}

async def start_token(db: AsyncSession, repo: CounterRepository, counter_id: UUID):
    counter = await repo.get_by_id(counter_id)
    if not counter.current_token_id:
        raise ValueError("Counter has no assigned token to start")
    token_repo = QueueTokenRepository(db)
    token = await token_repo.get_by_id(counter.current_token_id)
    await lock_counter_and_token(db, counter_id, token.id)
    await transition_token(
        db=db,
        token_id=token.id,
        target_status=TokenStatus.SERVING,
        actor_user_id=uuid.uuid4(),
        expected_status=TokenStatus.CALLED,
    )
    await db.commit()
    return {"token_id": str(token.id)}

async def hold_token(db: AsyncSession, repo: CounterRepository, counter_id: UUID):
    counter = await repo.get_by_id(counter_id)
    if not counter.current_token_id:
        raise ValueError("No token to hold")
    token_repo = QueueTokenRepository(db)
    token = await token_repo.get_by_id(counter.current_token_id)
    await lock_counter_and_token(db, counter_id, token.id)
    await transition_token(
        db=db,
        token_id=token.id,
        target_status=TokenStatus.ON_HOLD,
        actor_user_id=uuid.uuid4(),
        expected_status=TokenStatus.SERVING,
    )
    await db.commit()
    return {"token_id": str(token.id)}

async def resume_token(db: AsyncSession, repo: CounterRepository, counter_id: UUID):
    counter = await repo.get_by_id(counter_id)
    if not counter.current_token_id:
        raise ValueError("No token to resume")
    token_repo = QueueTokenRepository(db)
    token = await token_repo.get_by_id(counter.current_token_id)
    await lock_counter_and_token(db, counter_id, token.id)
    await transition_token(
        db=db,
        token_id=token.id,
        target_status=TokenStatus.SERVING,
        actor_user_id=uuid.uuid4(),
        expected_status=TokenStatus.ON_HOLD,
    )
    await db.commit()
    return {"token_id": str(token.id)}

async def complete_token(db: AsyncSession, repo: CounterRepository, counter_id: UUID):
    counter = await repo.get_by_id(counter_id)
    if not counter.current_token_id:
        raise ValueError("No token to complete")
    token_repo = QueueTokenRepository(db)
    token = await token_repo.get_by_id(counter.current_token_id)
    await lock_counter_and_token(db, counter_id, token.id)
    await transition_token(
        db=db,
        token_id=token.id,
        target_status=TokenStatus.COMPLETED,
        actor_user_id=uuid.uuid4(),
        expected_status=TokenStatus.SERVING,
    )
    await repo.clear_current_token(counter)
    await db.commit()
    return {"token_id": str(token.id)}

async def withdraw_call(db: AsyncSession, repo: CounterRepository, counter_id: UUID):
    counter = await repo.get_by_id(counter_id)
    if not counter.current_token_id:
        raise ValueError("No token to withdraw")
    token_repo = QueueTokenRepository(db)
    token = await token_repo.get_by_id(counter.current_token_id)
    await lock_counter_and_token(db, counter_id, token.id)
    await transition_token(
        db=db,
        token_id=token.id,
        target_status=TokenStatus.WAITING,
        actor_user_id=uuid.uuid4(),
        expected_status=TokenStatus.CALLED,
    )
    await repo.clear_current_token(counter)
    await db.commit()
    return {"token_id": str(token.id)}

async def no_show_token(db: AsyncSession, repo: CounterRepository, counter_id: UUID):
    counter = await repo.get_by_id(counter_id)
    if not counter.current_token_id:
        raise ValueError("No token to mark as no‑show")
    token_repo = QueueTokenRepository(db)
    token = await token_repo.get_by_id(counter.current_token_id)
    await lock_counter_and_token(db, counter_id, token.id)
    await transition_token(
        db=db,
        token_id=token.id,
        target_status=TokenStatus.NO_SHOW,
        actor_user_id=uuid.uuid4(),
        expected_status=TokenStatus.CALLED,
    )
    await repo.clear_current_token(counter)
    await db.commit()
    return {"token_id": str(token.id)}

async def transfer_token(db: AsyncSession, repo: CounterRepository, source_counter_id: UUID, target_counter_id: UUID):
    # Withdraw token from source and assign to target atomically
    source_counter = await repo.get_by_id(source_counter_id)
    target_counter = await repo.get_by_id(target_counter_id)
    if not source_counter.current_token_id:
        raise ValueError("Source counter has no token to transfer")
    if not await repo.is_eligible(target_counter):
        raise ValueError("Target counter not eligible for receiving token")
    token_repo = QueueTokenRepository(db)
    token = await token_repo.get_by_id(source_counter.current_token_id)
    await lock_counter_and_token(db, source_counter_id, token.id)
    # Also lock target counter row
    stmt_target = select(Counter).where(Counter.id == target_counter_id).with_for_update()
    await db.execute(stmt_target)
    # Clear source assignment
    await repo.clear_current_token(source_counter)
    # Assign to target
    await repo.assign_token(target_counter, token)
    await db.commit()
    return {"token_id": str(token.id), "new_counter_id": str(target_counter.id)}
