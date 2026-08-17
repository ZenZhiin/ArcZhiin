# =============================================================================
# ArcZhiin — Chat WebSocket Route
# Handles real-time chat communication between frontend and AI brain.
# =============================================================================

from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from core.agent import process_message
from core.context import context_manager

router = APIRouter()
logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections."""

    def __init__(self) -> None:
        self._active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket) -> str:
        """Accept connection and return a unique session ID."""
        await websocket.accept()
        session_id = str(uuid.uuid4())
        self._active_connections[session_id] = websocket
        logger.info("Client connected [%s]. Active: %d", session_id[:8], len(self._active_connections))
        return session_id

    def disconnect(self, session_id: str) -> None:
        """Remove a connection and clean up its context."""
        self._active_connections.pop(session_id, None)
        context_manager.remove(session_id)
        logger.info("Client disconnected [%s]. Active: %d", session_id[:8], len(self._active_connections))

    async def send_json(self, websocket: WebSocket, data: dict[str, Any]) -> None:
        await websocket.send_json(data)


manager = ConnectionManager()


@router.websocket("/chat")
async def websocket_chat(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for real-time chat with the AI brain.

    Client → Server:
    { "type": "message", "content": "What's the weather like?" }

    Server → Client (thinking):
    { "type": "status", "content": "thinking" }

    Server → Client (response):
    {
        "type": "response",
        "content": "I don't have weather data yet, but...",
        "model": "gemini/gemini-2.5-flash",
        "tier": "complex",
        "tokens": { "input": 120, "output": 45 }
    }
    """
    session_id = await manager.connect(websocket)
    context = context_manager.get_or_create(session_id)

    try:
        # Send welcome message
        await manager.send_json(websocket, {
            "type": "welcome",
            "content": "ArcZhiin is ready. How can I help?",
            "session_id": session_id,
        })

        while True:
            raw = await websocket.receive_text()

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await manager.send_json(websocket, {
                    "type": "error",
                    "content": "Invalid JSON format.",
                })
                continue

            message_type = data.get("type", "")
            content = data.get("content", "").strip()

            if message_type == "message" and content:
                # Notify client that we're processing
                await manager.send_json(websocket, {
                    "type": "status",
                    "content": "thinking",
                })

                # Process through the AI brain
                response = await process_message(context, content)

                await manager.send_json(websocket, {
                    "type": "response",
                    "content": response.content,
                    "model": response.model,
                    "tier": response.tier.value,
                    "tokens": {
                        "input": response.input_tokens,
                        "output": response.output_tokens,
                    },
                })

            elif message_type == "clear":
                # Clear conversation context
                context.clear()
                await manager.send_json(websocket, {
                    "type": "status",
                    "content": "Context cleared.",
                })

            else:
                await manager.send_json(websocket, {
                    "type": "error",
                    "content": "Send { \"type\": \"message\", \"content\": \"your message\" }",
                })

    except WebSocketDisconnect:
        manager.disconnect(session_id)
