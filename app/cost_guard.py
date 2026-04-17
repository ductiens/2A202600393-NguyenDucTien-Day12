from fastapi import HTTPException, status

from app.config import get_settings


def guard_chat_cost(message: str, history: list[object]) -> None:
    settings = get_settings()

    if len(message) > settings.max_message_chars:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Message too long. Max {settings.max_message_chars} characters.",
        )

    if len(history) > settings.max_history_messages:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"History too long. Max {settings.max_history_messages} messages.",
        )

    total_chars = len(message) + sum(len(getattr(m, "content", "")) for m in history)
    if total_chars > settings.max_total_chars:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Conversation too large. Max {settings.max_total_chars} characters.",
        )

