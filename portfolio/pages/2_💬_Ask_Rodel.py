import streamlit as st
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.rag_engine import GEMINI_AVAILABLE, query_rag, generate_response

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
    api_key = st.session_state.get("gemini_api_key")


if not api_key:
    st.info("🔑 This chat is powered by Google Gemini. Enter your API key to start.")
    st.markdown("Get a free key at [Google AI Studio](https://aistudio.google.com/apikey)")
    key_input = st.text_input("Gemini API Key", type="password", key="gemini_key_input")
    if st.button("Connect", type="primary"):
        if key_input:
            st.session_state.gemini_api_key = key_input
            st.rerun()
    st.stop()

if not GEMINI_AVAILABLE:
    st.error("`google-generativeai` not installed. Run: `pip install google-generativeai`")
    st.stop()

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
        with st.spinner("Searching profile and projects..."):
            ctx = query_rag(q, api_key, k=5)
        with st.spinner("Thinking..."):
            resp = generate_response(q, ctx, api_key, st.session_state.chat_messages[:-1])
        st.markdown(resp)
    st.session_state.chat_messages.append({"role": "assistant", "content": resp})
    st.rerun()

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
        except Exception as e:
            st.error(f"Something went wrong while generating a response. Check the Debug info below.")
            with st.expander("🛠️ Debug Info", expanded=False):
                st.markdown("### Available Models")
                try:
                    models = [m.name for m in genai.list_models()]
                    st.write(models)
                except Exception as me:
                    st.write(f"Could not list models: {me}")
                
                st.markdown("### Traceback")
                st.code(str(e))
                import traceback
                st.code(traceback.format_exc())


# Sidebar
with st.sidebar:

    st.markdown("### About This Chat")
    st.markdown("Powered by **Gemini 1.5 Flash** + **FAISS** vector search. Grounded in Rodel's profile data and 5 project READMEs. Never fabricates or exaggerates.")
    if st.button("🗑️ Clear Chat"):
        st.session_state.chat_messages = [{"role": "assistant", "content": "Chat cleared! What would you like to know?"}]
        st.rerun()
