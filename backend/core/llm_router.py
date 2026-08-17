# =============================================================================
# ArcZhiin — LLM Router
# Unified interface for multiple LLM providers via LiteLLM.
# Routes queries to the appropriate model tier based on complexity.
# =============================================================================

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import AsyncGenerator

import litellm

from config import settings

logger = logging.getLogger(__name__)

# Suppress LiteLLM's verbose logging
litellm.suppress_debug_info = True


class ModelTier(str, Enum):
    """LLM routing tiers based on task complexity."""

    FAST = "fast"           # Quick commands, device control
    DEFAULT = "default"     # Standard conversations
    COMPLEX = "complex"     # Multi-step reasoning
    PRO = "pro"             # Deep analysis, planning


# Map tiers to configured model names
_TIER_MODEL_MAP: dict[ModelTier, str] = {
    ModelTier.FAST: settings.llm.model_fast,
    ModelTier.DEFAULT: settings.llm.model_default,
    ModelTier.COMPLEX: settings.llm.model_complex,
    ModelTier.PRO: settings.llm.model_pro,
}

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
    return _TIER_MODEL_MAP.get(tier, settings.llm.model_default)


def _build_api_params(model: str) -> dict:
    """Build provider-specific API parameters."""
    params: dict = {}

    if model.startswith("gemini/"):
        if settings.llm.gemini_api_key:
            params["api_key"] = settings.llm.gemini_api_key

    elif model.startswith("ollama/"):
        params["api_base"] = settings.llm.ollama_base_url

    elif model.startswith("gpt") or model.startswith("openai/"):
        if settings.llm.openai_api_key:
            params["api_key"] = settings.llm.openai_api_key

    return params


async def chat(
    messages: list[dict[str, str]],
    tier: ModelTier = ModelTier.DEFAULT,
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> LLMResponse:
    """
    Send a chat completion request to the appropriate LLM tier.

    Args:
        messages: List of message dicts with 'role' and 'content' keys.
        tier: The complexity tier to route to.
        temperature: Sampling temperature (0.0 - 1.0).
        max_tokens: Maximum tokens in the response.

    Returns:
        LLMResponse with the generated content and metadata.
    """
    model = _get_model_for_tier(tier)
    api_params = _build_api_params(model)

    # Prepend system prompt if not already present
    if not messages or messages[0].get("role") != "system":
        messages = [{"role": "system", "content": SYSTEM_PROMPT}, *messages]

    try:
        response = await litellm.acompletion(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **api_params,
        )

        content = response.choices[0].message.content or ""
        usage = response.usage

        logger.info(
            "LLM response: model=%s, tokens=%d/%d",
            model,
            usage.prompt_tokens if usage else 0,
            usage.completion_tokens if usage else 0,
        )

        return LLMResponse(
            content=content,
            model=model,
            tier=tier,
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
        )

    except Exception as exc:
        logger.error("LLM call failed (tier=%s, model=%s): %s", tier, model, exc)

        # Fallback: try the next tier down
        fallback_chain = [ModelTier.COMPLEX, ModelTier.DEFAULT, ModelTier.FAST]
        for fallback_tier in fallback_chain:
            if fallback_tier == tier:
                continue
            try:
                fallback_model = _get_model_for_tier(fallback_tier)
                fallback_params = _build_api_params(fallback_model)

                logger.info("Falling back to: %s (%s)", fallback_model, fallback_tier)

                response = await litellm.acompletion(
                    model=fallback_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **fallback_params,
                )

                content = response.choices[0].message.content or ""
                usage = response.usage

                return LLMResponse(
                    content=content,
                    model=fallback_model,
                    tier=fallback_tier,
                    input_tokens=usage.prompt_tokens if usage else 0,
                    output_tokens=usage.completion_tokens if usage else 0,
                )
            except Exception:
                continue

        # All tiers failed
        return LLMResponse(
            content="I'm sorry, I'm unable to process your request right now. All LLM providers are unavailable.",
            model="none",
            tier=tier,
            input_tokens=0,
            output_tokens=0,
        )


async def chat_stream(
    messages: list[dict[str, str]],
    tier: ModelTier = ModelTier.DEFAULT,
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> AsyncGenerator[str, None]:
    """
    Stream a chat completion response token by token.

    Yields individual content chunks as they arrive.
    """
    model = _get_model_for_tier(tier)
    api_params = _build_api_params(model)

    if not messages or messages[0].get("role") != "system":
        messages = [{"role": "system", "content": SYSTEM_PROMPT}, *messages]

    try:
        response = await litellm.acompletion(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **api_params,
        )

        async for chunk in response:
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content

    except Exception as exc:
        logger.error("LLM stream failed: %s", exc)
        yield f"Error: Unable to generate response — {exc}"
