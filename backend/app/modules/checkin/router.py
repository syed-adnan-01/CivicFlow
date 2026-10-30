from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

try:
    from app.common.dependencies import get_current_user
    from app.modules.checkin.service import checkin_qr, manual_checkin
except ImportError:
    from backend.app.common.dependencies import get_current_user
    from backend.app.modules.checkin.service import checkin_qr, manual_checkin

router = APIRouter()

class QRCheckinRequest(BaseModel):
    reference: str = Field(..., description="Opaque QR reference string")

class ManualCheckinRequest(BaseModel):
    confirmation: bool = Field(..., description="Officer confirms the citizen identity")
    reason: str = Field(..., description="Reason for manual check‑in")

@router.post("/checkin", status_code=status.HTTP_201_CREATED)
async def qr_checkin(request: QRCheckinRequest, user=Depends(get_current_user)):
    try:
        token = await checkin_qr(request.reference, user)
        return {"token": token}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/appointments/{appointment_id}/check-in/manual", status_code=status.HTTP_201_CREATED)
async def manual_checkin_endpoint(appointment_id: str, request: ManualCheckinRequest, user=Depends(get_current_user)):
    if not request.confirmation:
        raise HTTPException(status_code=400, detail="Confirmation must be true")
    try:
        token = await manual_checkin(appointment_id, request.reason, user)
        return {"token": token}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
