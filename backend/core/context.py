# =============================================================================
# ArcZhiin — Conversation Context Manager
# Manages working memory (ring buffer) and message history.
# =============================================================================

from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Maximum number of turns (user + assistant) to keep in working memory
MAX_WORKING_MEMORY_TURNS = 10


@dataclass
class Message:
    """A single message in a conversation."""

    role: str       # 'user', 'assistant', 'system', 'tool'
    content: str


@dataclass
class ConversationContext:
    """
    Manages the conversation state for a single session.

    Working memory keeps the last N turns as a ring buffer.
    When the buffer is full, oldest messages are dropped.
    """

    conversation_id: str
    working_memory: deque[Message] = field(
        default_factory=lambda: deque(maxlen=MAX_WORKING_MEMORY_TURNS * 2)
    )

    def add_message(self, role: str, content: str) -> None:
        """Add a message to working memory."""
        self.working_memory.append(Message(role=role, content=content))
        logger.debug(
            "Context [%s]: +%s message (%d in memory)",
            self.conversation_id[:8],
            role,
            len(self.working_memory),
        )

    def get_messages(self) -> list[dict[str, str]]:
        """
        Get all messages in working memory as dicts
        suitable for LLM API calls.
        """
        return [
            {"role": msg.role, "content": msg.content}
            for msg in self.working_memory
        ]

    def clear(self) -> None:
        """Clear working memory."""
        self.working_memory.clear()

    @property
    def turn_count(self) -> int:
        """Number of user messages in the conversation."""
        return sum(1 for msg in self.working_memory if msg.role == "user")

    @property
    def is_empty(self) -> bool:
        """Whether the conversation has any messages."""
        return len(self.working_memory) == 0


class ContextManager:
    """
    Manages multiple conversation contexts.
    Each WebSocket connection gets its own context.
    """

    def __init__(self) -> None:
        self._contexts: dict[str, ConversationContext] = {}

    def get_or_create(self, conversation_id: str) -> ConversationContext:
        """Get an existing context or create a new one."""
        if conversation_id not in self._contexts:
            self._contexts[conversation_id] = ConversationContext(
                conversation_id=conversation_id
            )
            logger.info("New context created: %s", conversation_id[:8])
        return self._contexts[conversation_id]

    def remove(self, conversation_id: str) -> None:
        """Remove a context when a session ends."""
        if conversation_id in self._contexts:
            del self._contexts[conversation_id]
            logger.info("Context removed: %s", conversation_id[:8])

    @property
    def active_count(self) -> int:
        """Number of active conversation contexts."""
        return len(self._contexts)


# Singleton instance
context_manager = ContextManager()
