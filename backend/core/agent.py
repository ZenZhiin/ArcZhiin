# =============================================================================
# ArcZhiin — Agent Loop
# Main orchestration layer: receives user input, routes to LLM, returns response.
# =============================================================================

from __future__ import annotations

import logging

from core.llm_router import LLMResponse, ModelTier, chat
from core.context import ConversationContext
from db.database import db, generate_id

logger = logging.getLogger(__name__)


def classify_intent(user_message: str) -> ModelTier:
    """
    Classify the complexity of a user message to determine which LLM tier to use.

    Simple heuristic for now — will be replaced with a proper classifier later.
    """
    message_lower = user_message.lower().strip()
    word_count = len(message_lower.split())

    # Fast tier: very short commands or greetings
    fast_patterns = [
        "hi", "hello", "hey", "thanks", "thank you", "bye", "goodbye",
        "what time", "what's the time", "what date",
        "turn on", "turn off", "switch on", "switch off",
        "lights on", "lights off", "lock", "unlock",
    ]
    if word_count <= 5 or any(message_lower.startswith(p) for p in fast_patterns):
        return ModelTier.FAST

    # Pro tier: complex analysis, planning, coding
    pro_patterns = [
        "analyze", "compare", "explain in detail", "write a",
        "create a plan", "debug", "review this code",
        "summarize this document", "what are the pros and cons",
    ]
    if any(p in message_lower for p in pro_patterns):
        return ModelTier.COMPLEX

    # Default tier: everything else
    return ModelTier.DEFAULT


async def process_message(
    context: ConversationContext,
    user_message: str,
) -> LLMResponse:
    """
    Process a user message through the full agent pipeline.

    1. Classify intent → determine LLM tier
    2. Add to working memory
    3. Send to LLM with conversation history
    4. Store response in working memory
    5. Persist to database

    Returns the LLM response.
    """
    # 1. Classify intent
    tier = classify_intent(user_message)
    logger.info(
        "Intent classified: tier=%s for message='%s'",
        tier.value,
        user_message[:50],
    )

    # 2. Add user message to context
    context.add_message("user", user_message)

    # 3. Get conversation history and send to LLM
    messages = context.get_messages()
    response = await chat(messages=messages, tier=tier)

    # 4. Add assistant response to context
    context.add_message("assistant", response.content)

    # 5. Persist to database (fire and forget)
    try:
        await _persist_messages(
            context.conversation_id,
            user_message,
            response,
        )
    except Exception as exc:
        logger.warning("Failed to persist messages: %s", exc)

    return response


async def _persist_messages(
    conversation_id: str,
    user_message: str,
    response: LLMResponse,
) -> None:
    """Save the user message and assistant response to the database."""
    # Ensure conversation exists
    existing = await db.fetch_one(
        "SELECT id FROM conversations WHERE id = ?",
        (conversation_id,),
    )

    if not existing:
        await db.execute(
            "INSERT INTO conversations (id, title) VALUES (?, ?)",
            (conversation_id, user_message[:100]),
        )

    # Save user message
    await db.execute(
        "INSERT INTO messages (id, conversation_id, role, content) VALUES (?, ?, ?, ?)",
        (generate_id(), conversation_id, "user", user_message),
    )

    # Save assistant response
    await db.execute(
        "INSERT INTO messages (id, conversation_id, role, content, model, tokens_used) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (
            generate_id(),
            conversation_id,
            "assistant",
            response.content,
            response.model,
            response.output_tokens,
        ),
    )

    await db.commit()
