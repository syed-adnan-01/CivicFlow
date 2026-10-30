import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class UserProfileResponse(BaseModel):
    id: uuid.UUID
    firebase_uid: str
    phone_number: Optional[str] = None
    display_name: Optional[str] = None
    role: str
    office_id: Optional[uuid.UUID] = None
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserUpdateProfileRequest(BaseModel):
    display_name: Optional[str] = None
