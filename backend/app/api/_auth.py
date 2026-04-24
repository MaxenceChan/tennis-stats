"""Auth simple par bearer token pour les endpoints admin."""
from fastapi import Header, HTTPException, status

from app.config import get_settings


def require_admin(authorization: str | None = Header(default=None)) -> None:
    expected = get_settings().admin_token
    if not expected:
        return  # pas de token configuré -> ouvert (dev)
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    if token != expected:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid admin token")
