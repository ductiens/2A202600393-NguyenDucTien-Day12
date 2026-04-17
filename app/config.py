import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")


def _to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_env: str
    host: str
    port: int
    cors_origins: list[str]
    openai_api_key: str | None
    openai_model: str
    use_mock_llm: bool
    auth_enabled: bool
    auth_api_key: str
    rate_limit_per_minute: int
    max_message_chars: int
    max_history_messages: int
    max_total_chars: int

    @classmethod
    def from_env(cls) -> "Settings":
        cors_origins = [
            item.strip()
            for item in os.getenv("CORS_ORIGINS", "*").split(",")
            if item.strip()
        ]
        return cls(
            app_name=os.getenv("APP_NAME", "Vinmec AI API"),
            app_env=os.getenv("APP_ENV", "development"),
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "8000")),
            cors_origins=cors_origins or ["*"],
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            use_mock_llm=_to_bool(os.getenv("USE_MOCK_LLM"), default=False),
            auth_enabled=_to_bool(os.getenv("AUTH_ENABLED"), default=False),
            auth_api_key=os.getenv("AUTH_API_KEY", "change-me"),
            rate_limit_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "30")),
            max_message_chars=int(os.getenv("MAX_MESSAGE_CHARS", "2000")),
            max_history_messages=int(os.getenv("MAX_HISTORY_MESSAGES", "30")),
            max_total_chars=int(os.getenv("MAX_TOTAL_CHARS", "16000")),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()
