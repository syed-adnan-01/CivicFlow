from typing import Optional
from pydantic import BaseModel


class LogoutResponse(BaseModel):
    message: str = "Successfully logged out."
    status: str = "ok"
