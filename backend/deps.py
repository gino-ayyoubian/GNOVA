"""Shared FastAPI dependencies"""

from fastapi import HTTPException, Header
from typing import Optional
from auth_service import AuthService


async def get_current_user(authorization: Optional[str] = Header(None)):
    """Dependency to get current user from JWT token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = authorization.replace("Bearer ", "")
    payload = AuthService.decode_jwt_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = await AuthService.get_user_by_id(payload["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user["status"] != "active":
        raise HTTPException(status_code=403, detail="Account is not active")

    return user
