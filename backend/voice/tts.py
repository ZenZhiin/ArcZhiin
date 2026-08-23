# =============================================================================
# ArcZhiin — Text-to-Speech Engine
# Uses Piper TTS for local, fast, and high-quality voice synthesis.
# =============================================================================

from __future__ import annotations

import io
import logging
import urllib.request
import wave
from pathlib import Path

from piper import PiperVoice

logger = logging.getLogger(__name__)

# We'll use a high-quality, medium-sized English voice by default
MODEL_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx"
CONFIG_URL = f"{MODEL_URL}.json"

MODEL_DIR = Path("data/models/tts")
MODEL_PATH = MODEL_DIR / "en_US-lessac-medium.onnx"
CONFIG_PATH = MODEL_DIR / "en_US-lessac-medium.onnx.json"

# Lazy-loaded singleton
_voice: PiperVoice | None = None


def _get_voice() -> PiperVoice:
    """Lazy-load the Piper TTS model. Downloads it if missing."""
    global _voice
    if _voice is None:
        if not MODEL_PATH.exists():
            logger.info("Downloading Piper TTS model (~60MB)...")
            MODEL_DIR.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
            urllib.request.urlretrieve(CONFIG_URL, CONFIG_PATH)
            logger.info("Piper TTS model downloaded successfully.")

        logger.info("Loading Piper TTS voice...")
        _voice = PiperVoice.load(str(MODEL_PATH))
        logger.info("Piper TTS loaded.")
        
    return _voice


def synthesize_audio(text: str) -> bytes:
    """
    Synthesize text to raw WAV audio bytes.

    Args:
        text: The string to speak.

    Returns:
        WAV formatted audio bytes.
    """
    voice = _get_voice()
    
    # We write the generated audio into an in-memory WAV buffer
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(1)                      # Mono
        wav.setsampwidth(2)                      # 16-bit
        wav.setframerate(voice.config.sample_rate)
        
        # Piper writes directly to the wave file object
        voice.synthesize(text, wav)
        
    return buf.getvalue()
