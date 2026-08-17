# =============================================================================
# ArcZhiin — Application Configuration
# Loads settings from environment variables with sensible defaults.
# =============================================================================

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Load .env file from project root
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_env_path)


def _get_env(key: str, default: str = "") -> str:
    """Read an environment variable with a fallback default."""
    return os.getenv(key, default)


def _get_env_bool(key: str, default: bool = False) -> bool:
    """Read a boolean environment variable."""
    return _get_env(key, str(default)).lower() in ("true", "1", "yes")


def _get_env_float(key: str, default: float = 0.0) -> float:
    """Read a float environment variable."""
    try:
        return float(_get_env(key, str(default)))
    except ValueError:
        return default


@dataclass(frozen=True)
class LLMConfig:
    """Configuration for LLM routing across multiple providers."""

    gemini_api_key: str = field(default_factory=lambda: _get_env("GEMINI_API_KEY"))
    openai_api_key: str = field(default_factory=lambda: _get_env("OPENAI_API_KEY"))
    ollama_base_url: str = field(
        default_factory=lambda: _get_env("OLLAMA_BASE_URL", "http://localhost:11434")
    )

    # Tiered model routing
    model_fast: str = field(
        default_factory=lambda: _get_env("LLM_MODEL_FAST", "ollama/llama3.2:3b")
    )
    model_default: str = field(
        default_factory=lambda: _get_env("LLM_MODEL_DEFAULT", "ollama/llama3.1:8b")
    )
    model_complex: str = field(
        default_factory=lambda: _get_env("LLM_MODEL_COMPLEX", "gemini/gemini-2.5-flash")
    )
    model_pro: str = field(
        default_factory=lambda: _get_env("LLM_MODEL_PRO", "gemini/gemini-2.5-pro")
    )


@dataclass(frozen=True)
class VoiceConfig:
    """Configuration for the voice pipeline."""

    wake_word_sensitivity: float = field(
        default_factory=lambda: _get_env_float("WAKE_WORD_SENSITIVITY", 0.5)
    )
    wake_word_model: str = field(
        default_factory=lambda: _get_env("WAKE_WORD_MODEL", "hey_jarvis")
    )
    stt_model_size: str = field(
        default_factory=lambda: _get_env("STT_MODEL_SIZE", "base.en")
    )
    tts_voice: str = field(
        default_factory=lambda: _get_env("TTS_VOICE", "en_US-lessac-medium")
    )


@dataclass(frozen=True)
class HomeAssistantConfig:
    """Configuration for Home Assistant integration."""

    url: str = field(
        default_factory=lambda: _get_env("HOME_ASSISTANT_URL", "http://localhost:8123")
    )
    token: str = field(
        default_factory=lambda: _get_env("HOME_ASSISTANT_TOKEN")
    )


@dataclass(frozen=True)
class DatabaseConfig:
    """Configuration for SQLite database."""

    path: str = field(
        default_factory=lambda: _get_env("DATABASE_PATH", "./data/arczhiin.db")
    )


@dataclass(frozen=True)
class ServerConfig:
    """Configuration for the FastAPI server."""

    host: str = field(default_factory=lambda: _get_env("HOST", "0.0.0.0"))
    port: int = field(
        default_factory=lambda: int(_get_env("PORT", "8000"))
    )
    debug: bool = field(default_factory=lambda: _get_env_bool("DEBUG", True))
    log_level: str = field(
        default_factory=lambda: _get_env("LOG_LEVEL", "info")
    )
    secret_key: str = field(
        default_factory=lambda: _get_env("SECRET_KEY", "change_me")
    )
    cors_origins: list[str] = field(
        default_factory=lambda: _get_env(
            "CORS_ORIGINS", "http://localhost:3000,http://localhost:5173"
        ).split(",")
    )


@dataclass(frozen=True)
class Settings:
    """Root configuration container for the entire application."""

    llm: LLMConfig = field(default_factory=LLMConfig)
    voice: VoiceConfig = field(default_factory=VoiceConfig)
    home_assistant: HomeAssistantConfig = field(default_factory=HomeAssistantConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    server: ServerConfig = field(default_factory=ServerConfig)


# Singleton instance — import this throughout the app
settings = Settings()
