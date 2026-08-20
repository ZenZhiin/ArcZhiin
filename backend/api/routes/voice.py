# =============================================================================
# ArcZhiin — Voice WebSocket Route
# Handles audio streaming from browser for voice interaction.
# =============================================================================

from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from core.agent import process_message
from core.context import context_manager
from voice.stt import transcribe_audio

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/voice")
async def websocket_voice(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for voice interaction.

    Protocol:
    1. Client connects → server sends welcome
    2. Client sends binary audio data (WAV or raw PCM)
    3. Server transcribes → processes through AI brain → sends text response
    4. Client uses browser speechSynthesis for TTS

    Client → Server:
        Binary: audio bytes (WAV format from MediaRecorder)
        JSON: { "type": "clear" } to reset context

    Server → Client:
        { "type": "welcome", "content": "...", "session_id": "..." }
        { "type": "transcription", "content": "what user said" }
        { "type": "status", "content": "thinking" }
        { "type": "response", "content": "AI response", "model": "...", "tier": "..." }
        { "type": "error", "content": "error message" }
    """
    await websocket.accept()
    session_id = str(uuid.uuid4())
    context = context_manager.get_or_create(session_id)

    logger.info("Voice client connected [%s]", session_id[:8])

    try:
        # Send welcome
        await websocket.send_json({
            "type": "welcome",
            "content": "Voice interface active. Tap to speak.",
            "session_id": session_id,
        })

        while True:
            # Receive message — can be binary (audio) or text (JSON commands)
            message = await websocket.receive()

            # Handle disconnect
            if message.get("type") == "websocket.disconnect":
                break

            if "bytes" in message and message["bytes"]:
                audio_bytes = message["bytes"]
                logger.info(
                    "Received audio: %d bytes from [%s]",
                    len(audio_bytes), session_id[:8],
                )

                # Step 1: Transcribe audio → text
                try:
                    await websocket.send_json({
                        "type": "status",
                        "content": "transcribing",
                    })

                    transcription = transcribe_audio(audio_bytes)

                    if not transcription:
                        await websocket.send_json({
                            "type": "error",
                            "content": "Could not understand audio. Try again.",
                        })
                        continue

                    # Send transcription back to client
                    await websocket.send_json({
                        "type": "transcription",
                        "content": transcription,
                    })

                except Exception as exc:
                    logger.error("Transcription failed: %s", exc)
                    await websocket.send_json({
                        "type": "error",
                        "content": f"Transcription failed: {exc}",
                    })
                    continue

                # Step 2: Process through AI brain
                try:
                    await websocket.send_json({
                        "type": "status",
                        "content": "thinking",
                    })

                    response = await process_message(context, transcription)

                    await websocket.send_json({
                        "type": "response",
                        "content": response.content,
                        "model": response.model,
                        "tier": response.tier.value,
                        "tokens": {
                            "input": response.input_tokens,
                            "output": response.output_tokens,
                        },
                    })

                except Exception as exc:
                    logger.error("AI processing failed: %s", exc)
                    await websocket.send_json({
                        "type": "error",
                        "content": f"Processing failed: {exc}",
                    })

            elif "text" in message and message["text"]:
                import json
                try:
                    data = json.loads(message["text"])
                    if data.get("type") == "clear":
                        context.clear()
                        await websocket.send_json({
                            "type": "status",
                            "content": "Context cleared.",
                        })
                except json.JSONDecodeError:
                    pass

    except WebSocketDisconnect:
        context_manager.remove(session_id)
        logger.info("Voice client disconnected [%s]", session_id[:8])
