# =============================================================================
# ArcZhiin — LLM Router
# Unified interface for Gemini (google-genai) and Ollama (HTTP).
# Routes queries to the appropriate model tier based on complexity.
# =============================================================================

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import AsyncGenerator

import httpx
from google import genai

from config import settings

logger = logging.getLogger(__name__)


class ModelTier(str, Enum):
    """LLM routing tiers based on task complexity."""

    FAST = "fast"           # Quick commands, device control
    DEFAULT = "default"     # Standard conversations
    COMPLEX = "complex"     # Multi-step reasoning
    PRO = "pro"             # Deep analysis, planning


# ArcZhiin's system personality
SYSTEM_PROMPT = """You are ArcZhiin, an intelligent AI assistant created by ZenZhiin.
You are helpful, concise, and friendly. You assist with smart home control,
answering questions, managing tasks, and general conversation.

Key traits:
- Respond naturally and conversationally
- Be concise — avoid unnecessary verbosity
- When controlling smart home devices, confirm the action taken
- If unsure about something, say so honestly
- You can remember user preferences from past conversations

Current context:
- You are running on a home server
- You have access to smart home devices via Home Assistant
- You can manage tasks, calendars, and notes for the user
"""


@dataclass
class LLMResponse:
    """Structured response from an LLM call."""

    content: str
    model: str
    tier: ModelTier
    input_tokens: int
    output_tokens: int


def _get_model_for_tier(tier: ModelTier) -> str:
    """Resolve the model name for a given tier."""
    tier_map: dict[ModelTier, str] = {
        ModelTier.FAST: settings.llm.model_fast,
        ModelTier.DEFAULT: settings.llm.model_default,
        ModelTier.COMPLEX: settings.llm.model_complex,
        ModelTier.PRO: settings.llm.model_pro,
    }
    return tier_map.get(tier, settings.llm.model_default)


def _is_ollama_model(model: str) -> bool:
    """Check if a model is an Ollama (local) model."""
    return model.startswith("ollama/")


def _get_gemini_client() -> genai.Client:
    """Create a Gemini API client."""
    return genai.Client(api_key=settings.llm.gemini_api_key)


async def _call_gemini(
    model: str,
    messages: list[dict[str, str]],
    temperature: float,
    max_tokens: int,
) -> LLMResponse:
    """Call Gemini API via the official google-genai SDK."""
    client = _get_gemini_client()

    # Build the contents from messages
    # Gemini expects a system instruction separately
    system_parts: list[str] = []
    contents: list[dict[str, str]] = []

    for msg in messages:
        if msg["role"] == "system":
            system_parts.append(msg["content"])
        else:
            # Map 'assistant' role to 'model' for Gemini
            role = "model" if msg["role"] == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})

    # Ensure conversation starts with a user message
    if not contents or contents[0]["role"] != "user":
        contents.insert(0, {"role": "user", "parts": [{"text": "Hello"}]})

    config = {
        "temperature": temperature,
        "max_output_tokens": max_tokens,
    }
    if system_parts:
        config["system_instruction"] = "\n".join(system_parts)

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=config,
    )

    input_tokens = getattr(response.usage_metadata, "prompt_token_count", 0) or 0
    output_tokens = getattr(response.usage_metadata, "candidates_token_count", 0) or 0

    return LLMResponse(
        content=response.text or "",
        model=model,
        tier=ModelTier.DEFAULT,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )


async def _call_ollama(
    model: str,
    messages: list[dict[str, str]],
    temperature: float,
    max_tokens: int,
) -> LLMResponse:
    """Call Ollama API via HTTP."""
    # Strip 'ollama/' prefix for the API call
    model_name = model.replace("ollama/", "")

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{settings.llm.ollama_base_url}/api/chat",
            json={
                "model": model_name,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            },
        )
        response.raise_for_status()
        data = response.json()

    content = data.get("message", {}).get("content", "")
    input_tokens = data.get("prompt_eval_count", 0)
    output_tokens = data.get("eval_count", 0)

    return LLMResponse(
        content=content,
        model=model,
        tier=ModelTier.DEFAULT,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )


async def chat(
    messages: list[dict[str, str]],
    tier: ModelTier = ModelTier.DEFAULT,
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> LLMResponse:
    """
    Send a chat completion request to the appropriate LLM tier.

    Tries the requested tier first, then falls back through alternatives.
    """
    model = _get_model_for_tier(tier)

    # Prepend system prompt if not present
    if not messages or messages[0].get("role") != "system":
        messages = [{"role": "system", "content": SYSTEM_PROMPT}, *messages]

    # Build fallback chain: requested tier → other tiers
    all_tiers = [tier] + [t for t in ModelTier if t != tier]

    for attempt_tier in all_tiers:
        attempt_model = _get_model_for_tier(attempt_tier)
        try:
            if _is_ollama_model(attempt_model):
                response = await _call_ollama(attempt_model, messages, temperature, max_tokens)
            else:
                response = await _call_gemini(attempt_model, messages, temperature, max_tokens)

            response.tier = attempt_tier

            logger.info(
                "LLM response: model=%s, tier=%s, tokens=%d/%d",
                response.model, attempt_tier.value,
                response.input_tokens, response.output_tokens,
            )
            return response

        except Exception as exc:
            logger.warning(
                "LLM call failed (tier=%s, model=%s): %s",
                attempt_tier.value, attempt_model, str(exc)[:120],
            )
            continue

    # All tiers failed
    return LLMResponse(
        content="I'm sorry, I'm unable to process your request right now. All LLM providers are unavailable.",
        model="none",
        tier=tier,
        input_tokens=0,
        output_tokens=0,
    )
