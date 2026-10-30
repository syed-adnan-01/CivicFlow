from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID

try:
    from app.modules.counter.dependencies import get_counter_repo, get_db
    from app.modules.counter.service import (
        call_next,
        start_token,
        hold_token,
        resume_token,
        complete_token,
        withdraw_call,
        no_show_token,
        transfer_token,
    )
except ImportError:
    from backend.app.modules.counter.dependencies import get_counter_repo, get_db
    from backend.app.modules.counter.service import (
        call_next,
        start_token,
        hold_token,
        resume_token,
        complete_token,
        withdraw_call,
        no_show_token,
        transfer_token,
    )

router = APIRouter(prefix="/api/v1/counters", tags=["Counter Operations"])


@router.post("/{counter_id}/call-next")
async def call_next_endpoint(counter_id: UUID, db=Depends(get_db)):
    repo = await get_counter_repo(db)
    return await call_next(db, repo, counter_id)


@router.post("/{counter_id}/start")
async def start_endpoint(counter_id: UUID, db=Depends(get_db)):
    repo = await get_counter_repo(db)
    return await start_token(db, repo, counter_id)


@router.post("/{counter_id}/hold")
async def hold_endpoint(counter_id: UUID, db=Depends(get_db)):
    repo = await get_counter_repo(db)
    return await hold_token(db, repo, counter_id)


@router.post("/{counter_id}/resume")
async def resume_endpoint(counter_id: UUID, db=Depends(get_db)):
    repo = await get_counter_repo(db)
    return await resume_token(db, repo, counter_id)


@router.post("/{counter_id}/complete")
async def complete_endpoint(counter_id: UUID, db=Depends(get_db)):
    repo = await get_counter_repo(db)
    return await complete_token(db, repo, counter_id)


@router.post("/{counter_id}/withdraw-call")
async def withdraw_call_endpoint(counter_id: UUID, db=Depends(get_db)):
    repo = await get_counter_repo(db)
    return await withdraw_call(db, repo, counter_id)


@router.post("/{counter_id}/no-show")
async def no_show_endpoint(counter_id: UUID, db=Depends(get_db)):
    repo = await get_counter_repo(db)
    return await no_show_token(db, repo, counter_id)


@router.post("/{counter_id}/transfer/{target_counter_id}")
async def transfer_endpoint(counter_id: UUID, target_counter_id: UUID, db=Depends(get_db)):
    repo = await get_counter_repo(db)
    return await transfer_token(db, repo, counter_id, target_counter_id)
