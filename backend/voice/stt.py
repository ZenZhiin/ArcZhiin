# =============================================================================
# ArcZhiin — Speech-to-Text Engine
# Uses faster-whisper (large-v3) for local, accurate transcription.
# Auto-detects GPU (CUDA) on desktop, falls back to CPU on Mac.
# =============================================================================

from __future__ import annotations

import logging
import tempfile
import wave

from faster_whisper import WhisperModel

from config import settings

logger = logging.getLogger(__name__)

# Lazy-loaded singleton
_model: WhisperModel | None = None

# Smart home vocabulary hints — biases Whisper toward these words
VOCAB_HINTS = (
    "ArcZhiin, ZenZhiin, turn on, turn off, "
    "living room, bedroom, kitchen, bathroom, dining room, "
    "air conditioner, air cond, AC, fan, ceiling fan, "
    "lights, lamp, brightness, dim, bright, "
    "temperature, humidity, sensor, "
    "lock, unlock, door, window, curtain, "
    "play music, stop music, volume, "
    "good morning, good night, I'm home, I'm leaving"
)


def _detect_device() -> tuple[str, str]:
    """Auto-detect the best device and compute type."""
    device_setting = settings.voice.stt_device

    if device_setting == "auto":
        try:
            import torch
            if torch.cuda.is_available():
                logger.info("CUDA GPU detected — using GPU for STT")
                return "cuda", "float16"
        except ImportError:
            pass

        logger.info("No GPU detected — using CPU for STT")
        return "cpu", "int8"

    elif device_setting == "cuda":
        return "cuda", "float16"
    else:
        return "cpu", "int8"


def _get_model() -> WhisperModel:
    """Lazy-load the Whisper model on first use."""
    global _model
    if _model is None:
        model_size = settings.voice.stt_model_size
        device, compute_type = _detect_device()

        logger.info(
            "Loading Whisper model: %s on %s (%s) — this may take a moment...",
            model_size, device, compute_type,
        )

        _model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type,
        )

        logger.info("Whisper model loaded: %s (%s)", model_size, device)
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

        # Transcribe with vocabulary hints and VAD
        segments, info = model.transcribe(
            tmp.name,
            beam_size=5,
            language="en",
            initial_prompt=VOCAB_HINTS,
            vad_filter=True,
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
            "Transcription: '%s' (model=%s, lang=%s, prob=%.2f, duration=%.1fs)",
            transcription[:80],
            settings.voice.stt_model_size,
            info.language,
            info.language_probability,
            info.duration,
        )

        return transcription
