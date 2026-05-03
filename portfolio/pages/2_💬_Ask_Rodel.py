import streamlit as st
import os
import sys
import google.generativeai as genai

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.rag_engine import GEMINI_AVAILABLE, query_rag, generate_response
from utils.voice_engine import get_voice_config, synthesize_speech, render_audio_player, render_voice_badge

st.set_page_config(page_title="Ask Rodel — AI Chat", page_icon="💬", layout="wide")

st.markdown("""
<div style="background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); padding: 2rem; border-radius: 12px; margin-bottom: 2rem; text-align: center;">
    <h1 style="color: #e0e0ff; margin: 0;">💬 Ask Rodel</h1>
    <p style="color: #a0a0d0; margin: 0.5rem 0 0 0;">AI-powered chat grounded in my real profile, projects, and experience</p>
</div>
""", unsafe_allow_html=True)

# API Key — check secrets, env, then session
api_key = None
try:
    # st.secrets raises if no secrets.toml exists — guard with try/except
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

# Initialize voice toggle in session state
if "voice_enabled" not in st.session_state:
    st.session_state.voice_enabled = True

# Init chat history
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = [{"role": "assistant", "content": "Hey! I'm Rodel's AI — built to answer your questions about his skills, projects, and experience. Everything I say is grounded in his actual docs. What would you like to know?"}]

# Suggested questions
st.markdown("##### 💡 Try asking:")
scols = st.columns(4)
suggestions = ["What's your experience with AWS?", "Tell me about your RAG project", "What security projects have you built?", "How do you approach IaC?"]
for col, s in zip(scols, suggestions):
    with col:
        if st.button(s, key=f"s_{s[:15]}", use_container_width=True):
            st.session_state.chat_messages.append({"role": "user", "content": s})
            st.session_state._pq = s
            st.rerun()

st.divider()

# Display history
for msg in st.session_state.chat_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Handle pending suggestion
if hasattr(st.session_state, "_pq"):
    q = st.session_state._pq
    del st.session_state._pq
    with st.chat_message("assistant"):
        try:
            with st.spinner("Searching profile and projects..."):
                ctx = query_rag(q, api_key, k=5)
            with st.spinner("Thinking..."):
                resp = generate_response(q, ctx, api_key, st.session_state.chat_messages[:-1])
            st.markdown(resp)
            st.session_state.chat_messages.append({"role": "assistant", "content": resp})

            # Voice response
            if st.session_state.voice_enabled:
                with st.spinner("🎙️ Generating voice..."):
                    voice_result = synthesize_speech(resp)
                render_audio_player(voice_result)

            st.rerun()
        except Exception as e:
            st.error(f"Something went wrong while generating a response. Check the Debug info below.")
            with st.expander("🛠️ Debug Info (Suggested Question)", expanded=True):
                st.code(str(e))
                import traceback
                st.code(traceback.format_exc())

# Chat input
if prompt := st.chat_input("Ask about my experience, projects, or skills..."):
    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    # Generate response
    with st.chat_message("assistant"):
        try:
            with st.spinner("Searching my profile and projects..."):
                ctx = query_rag(prompt, api_key, k=5)
            with st.spinner("Thinking..."):
                resp = generate_response(prompt, ctx, api_key, st.session_state.chat_messages[:-1])
            st.markdown(resp)
            st.session_state.chat_messages.append({"role": "assistant", "content": resp})

            # Voice response
            if st.session_state.voice_enabled:
                with st.spinner("🎙️ Generating voice..."):
                    voice_result = synthesize_speech(resp)
                render_audio_player(voice_result)

        except Exception as e:
            st.error(f"Something went wrong while generating a response. Check the Debug info below.")
            with st.expander("🛠️ Debug Info", expanded=True):
                st.code(str(e))
                import traceback
                st.code(traceback.format_exc())

# Sidebar
with st.sidebar:
    st.markdown("### About This Chat")
    st.markdown("Powered by **Gemini 1.5 Pro** + **FAISS** vector search. Grounded in Rodel's profile data and 5 project READMEs. Never fabricates or exaggerates.")

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
