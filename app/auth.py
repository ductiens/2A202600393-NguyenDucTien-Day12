import secrets

from fastapi import Header, HTTPException, status

from app.config import get_settings


async def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    settings = get_settings()
    if not settings.auth_enabled:
        return

    if not x_api_key or not secrets.compare_digest(x_api_key, settings.auth_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

