import streamlit as st
import os
import sys
import google.generativeai as genai

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.rag_engine import GEMINI_AVAILABLE, query_rag, generate_response
from utils.voice_engine import get_voice_config, synthesize_speech, render_audio_player, render_voice_badge

st.set_page_config(page_title="Ask Rodel — AI Chat", page_icon="💬", layout="wide")

# Inject CSS to prevent layout shift during Streamlit reruns
st.markdown("""
<style>
    /* Stabilize layout during reruns — prevent content jump */
    [data-testid="stAppViewContainer"] {
        min-height: 100vh;
    }
    /* Smooth transitions instead of hard flash */
    .stChatMessage, .stMarkdown, .stButton {
        animation: fadeIn 0.15s ease-in;
    }
    @keyframes fadeIn {
        from { opacity: 0.7; }
        to { opacity: 1; }
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); padding: 2rem; border-radius: 12px; margin-bottom: 2rem; text-align: center;">
    <h1 style="color: #e0e0ff; margin: 0;">💬 Ask Rodel</h1>
    <p style="color: #a0a0d0; margin: 0.5rem 0 0 0;">AI-powered chat grounded in my real profile, projects, and experience</p>
</div>
""", unsafe_allow_html=True)

# API Key — check secrets, env, then session
api_key = None
try:
    api_key = st.secrets.get("GEMINI_API_KEY", None)
except BaseException:
    pass
if not api_key:
    api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    st.error("🔑 API Key not found. Please set GEMINI_API_KEY in `.streamlit/secrets.toml` or environment.")
    st.stop()

if not GEMINI_AVAILABLE:
    st.error("`google-generativeai` not installed. Run: `pip install google-generativeai`")
    st.stop()

# Voice configuration
voice_config = get_voice_config()

# Initialize session state
if "voice_enabled" not in st.session_state:
    st.session_state.voice_enabled = True
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = [{"role": "assistant", "content": "Hey! I'm Rodel's AI — built to answer your questions about his skills, projects, and experience. Everything I say is grounded in his actual docs. What would you like to know?"}]

# ---------------------------------------------------------------------------
# Helper: generate response and handle voice (plays inline, ZERO reruns)
# ---------------------------------------------------------------------------
def _handle_query(question):
    """Generate a RAG response for the given question."""
    with st.chat_message("assistant"):
        try:
            with st.spinner("Searching profile and projects..."):
                ctx = query_rag(question, api_key, k=5)
            with st.spinner("Thinking..."):
                resp = generate_response(question, ctx, api_key, st.session_state.chat_messages[:-1])
            st.markdown(resp)
            st.session_state.chat_messages.append({"role": "assistant", "content": resp})

            # Play voice inline — only for real responses, NOT errors
            is_error = resp.startswith("I'm having trouble")
            if st.session_state.voice_enabled and not is_error:
                voice_result = synthesize_speech(resp)
                render_audio_player(voice_result)

        except Exception as e:
            st.error("Something went wrong. Please try again.")
            with st.expander("🛠️ Debug Info", expanded=False):
                st.code(str(e))
                import traceback
                st.code(traceback.format_exc())

# ---------------------------------------------------------------------------
# Suggestion buttons inside a fragment to avoid full-page rerun
# ---------------------------------------------------------------------------
@st.fragment
def suggestion_buttons():
    """Render suggestion buttons. Clicks only rerun this fragment, not the whole page."""
    st.markdown("##### 💡 Try asking:")
    scols = st.columns(4)
    suggestions = [
        "What's your experience with AWS?",
        "Tell me about your RAG project",
        "What security projects have you built?",
        "How do you approach IaC?",
    ]
    for col, s in zip(scols, suggestions):
        with col:
            if st.button(s, key=f"s_{s[:15]}", use_container_width=True):
                st.session_state.chat_messages.append({"role": "user", "content": s})
                with st.chat_message("user"):
                    st.markdown(s)
                _handle_query(s)

suggestion_buttons()

st.divider()

# Display chat history
for msg in st.session_state.chat_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------------------------------------------------------------------
# Microphone Input inside a fragment
# ---------------------------------------------------------------------------
@st.fragment
def mic_input():
    """Microphone input. Runs in its own fragment to avoid page flash."""
    mic_col, _ = st.columns([1, 5])
    with mic_col:
        mic_clicked = st.button("🎤 Speak", use_container_width=True, type="primary")

    if mic_clicked:
        st.components.v1.html("""
        <div id="mic-status" style="
            background: rgba(15,12,41,0.9); border: 1px solid #7c83ff;
            border-radius: 8px; padding: 1rem; margin: 0.5rem 0;
            font-family: 'Inter', sans-serif; color: #e0e0ff; font-size: 0.9rem;
        ">
            <div id="mic-text">🎤 Requesting microphone access...</div>
            <div id="mic-hint" style="color: #a0a0d0; font-size: 0.75rem; margin-top: 0.3rem;">
                If you see a permission prompt, click "Allow" to enable your microphone.
            </div>
        </div>
        <script>
            const statusEl = document.getElementById('mic-text');
            const hintEl = document.getElementById('mic-hint');
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

            if (!SpeechRecognition) {
                statusEl.innerHTML = '❌ Speech recognition not supported. Use <strong>Chrome</strong> or <strong>Edge</strong>.';
                hintEl.innerHTML = '';
            } else {
                const recognition = new SpeechRecognition();
                recognition.lang = 'en-US';
                recognition.interimResults = true;
                recognition.maxAlternatives = 1;

                recognition.onstart = function() {
                    statusEl.innerHTML = '🔴 Listening... speak now.';
                    hintEl.innerHTML = 'I\\'ll stop listening when you pause.';
                };

                recognition.onresult = function(event) {
                    const transcript = event.results[0][0].transcript;
                    const isFinal = event.results[0].isFinal;
                    if (isFinal) {
                        statusEl.innerHTML = '✅ Got it: <strong>' + transcript + '</strong>';
                        hintEl.innerHTML = 'Submitting your question...';
                        const url = new URL(window.parent.location);
                        url.searchParams.set('voice_query', transcript);
                        window.parent.history.replaceState({}, '', url);
                        setTimeout(() => { window.parent.location.reload(); }, 800);
                    } else {
                        statusEl.innerHTML = '🎤 Hearing: <em>' + transcript + '</em>...';
                    }
                };

                recognition.onerror = function(event) {
                    if (event.error === 'not-allowed') {
                        statusEl.innerHTML = '🔒 Microphone access denied.';
                        hintEl.innerHTML = 'Allow microphone in browser settings, then click 🎤 again.';
                    } else if (event.error === 'no-speech') {
                        statusEl.innerHTML = '⏹️ No speech detected.';
                        hintEl.innerHTML = 'Click 🎤 Speak to try again.';
                    } else {
                        statusEl.innerHTML = '❌ Error: ' + event.error;
                        hintEl.innerHTML = 'Click 🎤 Speak to try again.';
                    }
                };

                recognition.onend = function() {
                    if (!statusEl.innerHTML.includes('✅') && !statusEl.innerHTML.includes('🔒') && !statusEl.innerHTML.includes('❌')) {
                        statusEl.innerHTML = '⏹️ No speech detected.';
                        hintEl.innerHTML = 'Click 🎤 Speak to try again.';
                    }
                };

                recognition.start();
            }
        </script>
        """, height=80)

mic_input()

# Check for voice query from URL params — handle inline
voice_params = st.query_params
if "voice_query" in voice_params:
    voice_query = voice_params["voice_query"]
    # Clear without triggering extra rerun by using del
    del st.query_params["voice_query"]
    if voice_query.strip():
        st.session_state.chat_messages.append({"role": "user", "content": voice_query})
        with st.chat_message("user"):
            st.markdown(voice_query)
        _handle_query(voice_query)

# Text chat input (always available)
if prompt := st.chat_input("Ask about my experience, projects, or skills..."):
    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    _handle_query(prompt)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### About This Chat")
    st.markdown("Powered by **Gemini 2.0 Flash** + **FAISS** vector search. Grounded in Rodel's profile data and 5 project READMEs. Never fabricates or exaggerates.")

    st.divider()

    # Voice Controls
    st.markdown("### 🎙️ Voice Mode")
    render_voice_badge(voice_config)
    st.session_state.voice_enabled = st.toggle(
        "Enable Voice Responses",
        value=st.session_state.voice_enabled,
        key="voice_toggle",
    )

    if voice_config["tier"] == 3:
        st.caption("💡 Add `ELEVENLABS_API_KEY` to secrets for premium AI voice.")

    st.divider()

    with st.expander("🛠️ Environment Debug", expanded=False):
        st.markdown("### Available Models")
        try:
            models = [m.name for m in genai.list_models()]
            st.write(models)
        except Exception as me:
            st.write(f"Could not list models: {me}")

    if st.button("🗑️ Clear Chat"):
        st.session_state.chat_messages = [{"role": "assistant", "content": "Chat cleared! What would you like to know?"}]
        st.rerun()
