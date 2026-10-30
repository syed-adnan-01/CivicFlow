"""
Role-based authorization dependencies.
"""

from typing import Callable
from fastapi import Depends, HTTPException, status

from app.common.dependencies import AuthenticatedUser, get_current_user


def require_role(*allowed_roles: str) -> Callable:
    """
    Dependency factory to enforce role-based access control.
    e.g. Depends(require_role("OFFICE_ADMIN"))
    """
    async def role_checker(current_user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "USER_INACTIVE", "message": "Account is inactive."},
            )

        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "FORBIDDEN",
                    "message": f"Operation requires one of the following roles: {', '.join(allowed_roles)}.",
                },
            )
        return current_user

    return role_checker

