"""
Voice Engine for Ask Rodel — Tiered Voice Synthesis

Architectural Why:
    This module implements a resilient, tiered text-to-speech system designed
    for a production portfolio. It gracefully degrades across three tiers:

    Tier 1: ElevenLabs with a CLONED voice (requires paid plan + ELEVENLABS_VOICE_ID)
            → Use when actively job hunting for maximum "wow" factor
    Tier 2: ElevenLabs with a pre-made professional voice (free tier)
            → Default mode, still impressive, zero cost
    Tier 3: Browser-native Web Speech API (no API keys needed)
            → Ultimate fallback if ElevenLabs quota exhausted or unavailable

    The toggle is entirely driven by Streamlit secrets:
        - Set ELEVENLABS_API_KEY + ELEVENLABS_VOICE_ID → Tier 1 (cloned voice)
        - Set ELEVENLABS_API_KEY only                  → Tier 2 (pre-made voice)
        - Set neither                                  → Tier 3 (browser TTS)
"""

import os
import base64
import requests
import streamlit as st
from typing import Optional, Dict, Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1/text-to-speech"

# "Adam" — a professional, clear male voice available on ElevenLabs free tier
DEFAULT_PREMADE_VOICE_ID = "pNInz6obpgDQGcFmaJgB"

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
def get_voice_config() -> Dict[str, Any]:
    """
    Determine which voice tier to use based on available secrets/env vars.
    
    Returns:
        Dict with keys: tier (int), label (str), api_key (str|None), voice_id (str|None)
    """
    api_key = None
    voice_id = None

    # Check Streamlit secrets first, then environment variables
    try:
        api_key = st.secrets.get("ELEVENLABS_API_KEY", None)
    except BaseException:
        pass
    if not api_key:
        api_key = os.environ.get("ELEVENLABS_API_KEY")

    try:
        voice_id = st.secrets.get("ELEVENLABS_VOICE_ID", None)
    except BaseException:
        pass
    if not voice_id:
        voice_id = os.environ.get("ELEVENLABS_VOICE_ID")

    if api_key and voice_id:
        return {
            "tier": 1,
            "label": "🎙️ Rodel's Voice",
            "api_key": api_key,
            "voice_id": voice_id,
        }
    elif api_key:
        return {
            "tier": 2,
            "label": "🔊 AI Voice",
            "api_key": api_key,
            "voice_id": DEFAULT_PREMADE_VOICE_ID,
        }
    else:
        return {
            "tier": 3,
            "label": "🔊 Browser Voice",
            "api_key": None,
            "voice_id": None,
        }


# ---------------------------------------------------------------------------
# ElevenLabs TTS
# ---------------------------------------------------------------------------
def _synthesize_with_elevenlabs(
    text: str, api_key: str, voice_id: str
) -> Optional[bytes]:
    """
    Call ElevenLabs TTS API and return raw MP3 audio bytes.
    Returns None on any failure (quota exhausted, network error, etc.)
    """
    url = f"{ELEVENLABS_API_URL}/{voice_id}"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
        },
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.content
        # Log the failure reason for debugging
        return None
    except requests.RequestException:
        return None


# ---------------------------------------------------------------------------
# Main Synthesis Function
# ---------------------------------------------------------------------------
def synthesize_speech(text: str) -> Dict[str, Any]:
    """
    Synthesize speech from text using the best available tier.
    Automatically falls back through tiers on failure.

    Returns:
        Dict with keys:
            - audio (bytes|None): Raw MP3 audio bytes, or None for browser TTS
            - tier (int): Which tier was actually used
            - label (str): Human-readable label for the voice mode
            - text (str): Original text (needed for browser TTS fallback)
    """
    config = get_voice_config()

    # Tier 1: Cloned voice
    if config["tier"] == 1:
        audio_bytes = _synthesize_with_elevenlabs(
            text, config["api_key"], config["voice_id"]
        )
        if audio_bytes:
            return {
                "audio": audio_bytes,
                "tier": 1,
                "label": config["label"],
                "text": text,
            }
        # Tier 1 failed (quota?) → fall through to Tier 2
        config["tier"] = 2
        config["voice_id"] = DEFAULT_PREMADE_VOICE_ID

    # Tier 2: Pre-made ElevenLabs voice
    if config["tier"] == 2:
        audio_bytes = _synthesize_with_elevenlabs(
            text, config["api_key"], config["voice_id"]
        )
        if audio_bytes:
            return {
                "audio": audio_bytes,
                "tier": 2,
                "label": "🔊 AI Voice" if config["tier"] == 2 else "🔊 AI Voice (Fallback)",
                "text": text,
            }

    # Tier 3: Browser TTS (ultimate fallback)
    return {
        "audio": None,
        "tier": 3,
        "label": "🔊 Browser Voice",
        "text": text,
    }


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------
def render_audio_player(result: Dict[str, Any]) -> None:
    """
    Render the appropriate audio player in Streamlit based on the synthesis result.
    
    For Tiers 1 & 2: Renders an autoplay HTML5 audio element with the MP3 data.
    For Tier 3: Injects JavaScript to use the browser's built-in speech synthesis.
    """
    if result.get("audio"):
        # ElevenLabs audio — embed as base64 autoplay
        audio_b64 = base64.b64encode(result["audio"]).decode()
        st.markdown(
            f'<audio autoplay src="data:audio/mpeg;base64,{audio_b64}"></audio>',
            unsafe_allow_html=True,
        )
    else:
        render_browser_tts(result["text"])


def render_browser_tts(text: str) -> None:
    """
    Speak text using the browser's built-in Web Speech API.
    Reusable by any page — selects a male voice at conversational pace.
    Fixes common tech acronym pronunciation.
    """
    import re
    safe_text = (
        text
        .replace("\\", "\\\\")
        .replace("'", "\\'")
        .replace('"', '\\"')
        .replace("\n", " ")
        .replace("\r", "")
    )

    # Fix common acronym pronunciation issues
    safe_text = re.sub(r'\bAWS\b', 'A. W. S.', safe_text)
    safe_text = re.sub(r'\bAPI\b', 'A. P. I.', safe_text)
    safe_text = re.sub(r'\bAI\b', 'A. I.', safe_text)
    safe_text = re.sub(r'\bRAG\b', 'R. A. G.', safe_text)
    safe_text = re.sub(r'\bLLM\b', 'L. L. M.', safe_text)
    safe_text = re.sub(r'\bCI/CD\b', 'C. I. C. D.', safe_text)
    safe_text = re.sub(r'\bIaC\b', 'Infrastructure as Code', safe_text)
    safe_text = re.sub(r'\bK8s\b', 'Kubernetes', safe_text)
    safe_text = re.sub(r'\bS3\b', 'S. 3.', safe_text)
    safe_text = re.sub(r'\bEC2\b', 'E. C. 2.', safe_text)
    safe_text = re.sub(r'\bVPC\b', 'V. P. C.', safe_text)
    safe_text = re.sub(r'\bIAM\b', 'I. A. M.', safe_text)
    safe_text = re.sub(r'\bSTAR\b', 'S. T. A. R.', safe_text)

    st.components.v1.html(
        f"""
        <script>
            function speakText() {{
                window.speechSynthesis.cancel();
                const utterance = new SpeechSynthesisUtterance('{safe_text}');
                utterance.rate = 1.15;
                utterance.pitch = 1.0;
                utterance.volume = 1.0;

                // Select a strictly male voice
                const voices = window.speechSynthesis.getVoices();
                const preferredNames = [
                    'Google UK English Male',
                    'Microsoft Mark',
                    'Microsoft David',
                    'Daniel',
                    'Fred',
                    'Ralph',
                    'Aaron',
                    'Alex',
                ];
                let selectedVoice = null;
                for (const name of preferredNames) {{
                    selectedVoice = voices.find(v => v.name.includes(name));
                    if (selectedVoice) break;
                }}
                if (selectedVoice) utterance.voice = selectedVoice;
                window.speechSynthesis.speak(utterance);
            }}

            if (window.speechSynthesis.getVoices().length > 0) {{
                speakText();
            }} else {{
                window.speechSynthesis.onvoiceschanged = speakText;
            }}
        </script>
        """,
        height=0,
    )


def render_voice_badge(config: Dict[str, Any]) -> None:
    """Render a small badge in the sidebar showing the current voice mode."""
    tier = config["tier"]
    if tier == 1:
        color = "#4ade80"
        desc = "Cloned Voice Active"
    elif tier == 2:
        color = "#60a5fa"
        desc = "AI Voice Active"
    else:
        color = "#a0a0d0"
        desc = "Browser Voice"

    st.markdown(
        f'<div style="display: flex; align-items: center; gap: 0.5rem; margin: 0.3rem 0;">'
        f'<span style="width: 8px; height: 8px; border-radius: 50%; background: {color}; display: inline-block;"></span>'
        f'<span style="color: {color}; font-size: 0.8rem; font-weight: 500;">{desc}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )
