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


def render_browser_tts(text: str, rate: float = 1.15) -> None:
    """
    Speak text using the browser's built-in Web Speech API.
    Reusable by any page — selects a male voice at conversational pace.
    Fixes common tech acronym pronunciation and strips markdown.
    """
    import re
    
    # 1. Strip Markdown and special characters before escaping for JS
    clean_text = text
    clean_text = re.sub(r'\*\*', '', clean_text)  # Strip bolding
    clean_text = re.sub(r'__', '', clean_text)   # Strip underlining
    clean_text = re.sub(r'#+\s', '', clean_text) # Strip headers
    clean_text = re.sub(r'[`*_-]', '', clean_text) # Strip other markdown symbols
    clean_text = clean_text.replace("\\", "")    # Strip backslashes

    # 2. Escape for JavaScript string literal
    safe_text = (
        clean_text
        .replace("'", "\\'")
        .replace('"', '\\"')
        .replace("\n", " ")
        .replace("\r", "")
    )

    # 3. Phonetic normalization for tech acronyms (including plurals)
    replacements = {
        r'\bAWS\b': 'A. W. S.',
        r'\bAPIs\b': 'A. P. Is',
        r'\bAPI\b': 'A. P. I.',
        r'\bPIIs\b': 'P. I. Is',
        r'\bPII\b': 'P. I. I.',
        r'\bAI\b': 'A. I.',
        r'\bRAGs\b': 'R. A. Gs',
        r'\bRAG\b': 'R. A. G.',
        r'\bLLMs\b': 'L. L. Ms',
        r'\bLLM\b': 'L. L. M.',
        r'\bCI/CD\b': 'C. I. C. D.',
        r'\bIaC\b': 'Infrastructure as Code',
        r'\bK8s\b': 'Kubernetes',
        r'\bS3\b': 'S. 3.',
        r'\bEC2\b': 'E. C. 2.',
        r'\bVPC\b': 'V. P. C.',
        r'\bIAM\b': 'I. A. M.',
        r'\bSTAR\b': 'S. T. A. R.',
        r'\bSRE\b': 'S. R. E.',
        r'\bSREs\b': 'S. R. Es',
    }
    
    for pattern, replacement in replacements.items():
        safe_text = re.sub(pattern, replacement, safe_text)

    st.components.v1.html(
        f"""
        <script>
            function speakText() {{
                window.speechSynthesis.cancel();
                const utterance = new SpeechSynthesisUtterance('{safe_text}');
                utterance.rate = {rate};
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
