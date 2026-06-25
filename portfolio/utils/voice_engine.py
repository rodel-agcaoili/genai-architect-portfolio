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
# Helper: Text Cleaning and Truncation
# ---------------------------------------------------------------------------
def clean_and_truncate_text(text: str, max_chars: int = 250) -> str:
    """
    Clean markdown, list symbols, and link syntax from text, and truncate it
    to the first few natural sentences up to max_chars to prevent timeouts,
    conserve ElevenLabs character quota, and keep speech concise.
    """
    import re
    # Remove markdown bold/italic
    text = re.sub(r"\*+", "", text)
    # Remove markdown headers
    text = re.sub(r"#+\s+", "", text)
    # Remove link formatting [text](url) -> text
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    # Replace bullet points or numbering at start of lines
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)
    # Collapse multiple spaces/newlines into a single space
    text = re.sub(r"\s+", " ", text).strip()
    
    if len(text) <= max_chars:
        return text

    # Try to truncate at sentence boundaries (period, exclamation, question mark followed by space)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    truncated = ""
    for s in sentences:
        if len(truncated) + len(s) + (1 if truncated else 0) <= max_chars:
            truncated = f"{truncated} {s}".strip() if truncated else s
        else:
            # If nothing fits, take a hard slice
            if not truncated:
                truncated = s[:max_chars].strip()
            break
            
    # Add a polite trailing indicator if truncated
    if len(truncated) < len(text):
        if not truncated.endswith('.'):
            truncated = truncated.rstrip('.,!?;:') + "..."
        else:
            truncated = truncated[:-1] + "..."
        truncated += " (Full response shown below.)"
        
    return truncated


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
            st.session_state["voice_last_error"] = None
            return response.content
        
        # Log the failure reason for debugging
        try:
            err_json = response.json()
            err_detail = err_json.get("detail", {}).get("message", response.text)
        except Exception:
            err_detail = response.text
        
        error_msg = f"ElevenLabs API error {response.status_code}: {err_detail}"
        st.session_state["voice_last_error"] = error_msg
        print(f"[Voice Engine] {error_msg}")
        return None
    except requests.RequestException as e:
        error_msg = f"ElevenLabs network error: {str(e)}"
        st.session_state["voice_last_error"] = error_msg
        print(f"[Voice Engine] {error_msg}")
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
    # 1. Clean and truncate the text first
    cleaned_text = clean_and_truncate_text(text)
    
    config = get_voice_config()

    # Tier 1: Cloned voice
    if config["tier"] == 1:
        audio_bytes = _synthesize_with_elevenlabs(
            cleaned_text, config["api_key"], config["voice_id"]
        )
        if audio_bytes:
            st.session_state["voice_active_tier"] = 1
            return {
                "audio": audio_bytes,
                "tier": 1,
                "label": config["label"],
                "text": cleaned_text,
            }
        # Tier 1 failed (quota/timeout) → fall through to Tier 2
        config["tier"] = 2
        config["voice_id"] = DEFAULT_PREMADE_VOICE_ID

    # Tier 2: Pre-made ElevenLabs voice
    if config["tier"] == 2:
        audio_bytes = _synthesize_with_elevenlabs(
            cleaned_text, config["api_key"], config["voice_id"]
        )
        if audio_bytes:
            st.session_state["voice_active_tier"] = 2
            return {
                "audio": audio_bytes,
                "tier": 2,
                "label": "🔊 AI Voice" if config["tier"] == 2 else "🔊 AI Voice (Fallback)",
                "text": cleaned_text,
            }

    # Tier 3: Browser TTS (ultimate fallback)
    st.session_state["voice_active_tier"] = 3
    return {
        "audio": None,
        "tier": 3,
        "label": "🔊 Browser Voice",
        "text": cleaned_text,
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
                    'Google US English Male',
                    'Google AU English Male',
                    'Microsoft Mark',
                    'Microsoft David',
                    'Daniel',
                    'Alex',
                    'Fred',
                    'Ralph',
                    'Aaron'
                ];
                let selectedVoice = null;
                // 1. Try exact matches from preferred list (case-insensitive)
                for (const name of preferredNames) {{
                    selectedVoice = voices.find(v => v.name.toLowerCase().includes(name.toLowerCase()));
                    if (selectedVoice) break;
                }}
                // 2. Fallback: Search for any voice with 'male' in the name (case-insensitive)
                if (!selectedVoice) {{
                    selectedVoice = voices.find(v => v.name.toLowerCase().includes('male'));
                }}
                // 3. Fallback: Search for other known male voices by language
                if (!selectedVoice) {{
                    const fallbackMaleNames = ['mikhail', 'rishi', 'jorge', 'thomas', 'nicolas'];
                    for (const name of fallbackMaleNames) {{
                        selectedVoice = voices.find(v => v.name.toLowerCase().includes(name));
                        if (selectedVoice) break;
                    }}
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
    # Use the last active tier if available, otherwise default to config tier
    tier = st.session_state.get("voice_active_tier", config["tier"])
    
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

    # Show debugging error if there's any ElevenLabs failure logged
    last_error = st.session_state.get("voice_last_error")
    if last_error:
        st.markdown(
            f'<div style="color: #f87171; font-size: 0.75rem; line-height: 1.2; margin-top: 0.2rem; word-break: break-word;">'
            f'⚠️ {last_error}'
            f'</div>',
            unsafe_allow_html=True,
        )
