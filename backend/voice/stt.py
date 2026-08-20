# =============================================================================
# ArcZhiin — Speech-to-Text Engine
# Uses faster-whisper for local, fast, and accurate transcription.
# =============================================================================

from __future__ import annotations

import io
import logging
import tempfile
import wave
from pathlib import Path

from faster_whisper import WhisperModel

from config import settings

logger = logging.getLogger(__name__)

# Lazy-loaded singleton
_model: WhisperModel | None = None


def _get_model() -> WhisperModel:
    """Lazy-load the Whisper model on first use."""
    global _model
    if _model is None:
        model_size = settings.voice.stt_model_size
        logger.info("Loading Whisper model: %s (this may take a moment...)", model_size)

        _model = WhisperModel(
            model_size,
            device="cpu",          # Mac dev — GPU on desktop later
            compute_type="int8",   # Fastest on CPU
        )

        logger.info("Whisper model loaded: %s", model_size)
    return _model


def transcribe_audio(audio_bytes: bytes, sample_rate: int = 16000) -> str:
    """
    Transcribe raw audio bytes to text.

    Args:
        audio_bytes: Raw PCM audio data (16-bit mono) or WAV file bytes.
        sample_rate: Sample rate of the audio (default 16kHz for Whisper).

    Returns:
        Transcribed text string.
    """
    model = _get_model()

    # Write audio to a temporary WAV file (faster-whisper needs a file path)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
        # Check if it's already a WAV file
        if audio_bytes[:4] == b"RIFF":
            tmp.write(audio_bytes)
        else:
            # Wrap raw PCM in WAV container
            with wave.open(tmp.name, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(sample_rate)
                wf.writeframes(audio_bytes)

        tmp.flush()

        # Transcribe
        segments, info = model.transcribe(
            tmp.name,
            beam_size=3,
            language="en",
            vad_filter=True,           # Built-in Silero VAD
            vad_parameters=dict(
                min_silence_duration_ms=500,
                speech_pad_ms=200,
            ),
        )

        # Collect all segments into text
        text_parts: list[str] = []
        for segment in segments:
            text_parts.append(segment.text.strip())

        transcription = " ".join(text_parts).strip()

        logger.info(
            "Transcription: '%s' (lang=%s, prob=%.2f, duration=%.1fs)",
            transcription[:80],
            info.language,
            info.language_probability,
            info.duration,
        )

        return transcription
