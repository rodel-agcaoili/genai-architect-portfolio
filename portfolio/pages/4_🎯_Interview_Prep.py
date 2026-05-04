import streamlit as st
import os
import sys
import time
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    from utils.interview_engine import (
        analyze_job_description, evaluate_answer, get_best_answer,
        generate_interview_report, save_session, save_incomplete_session,
        get_progress_summary, get_recent_jds
    )
    from utils.voice_engine import render_browser_tts
    ENGINE_OK = True
except ImportError as e:
    ENGINE_OK = False

st.set_page_config(page_title="Interview Prep — AI Coach", page_icon="🎯", layout="wide")

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { min-height: 100vh; }
    .stChatMessage, .stMarkdown, .stButton { animation: fadeIn 0.15s ease-in; }
    @keyframes fadeIn { from { opacity: 0.7; } to { opacity: 1; } }
    .grade-badge {
        display: inline-block; padding: 0.3rem 0.8rem; border-radius: 20px;
        font-weight: 700; font-size: 1.1rem; color: white;
    }
    .grade-A { background: linear-gradient(135deg, #10b981, #059669); }
    .grade-B { background: linear-gradient(135deg, #3b82f6, #2563eb); }
    .grade-C { background: linear-gradient(135deg, #f59e0b, #d97706); }
    .grade-D { background: linear-gradient(135deg, #f97316, #ea580c); }
    .grade-F { background: linear-gradient(135deg, #ef4444, #dc2626); }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown("""
<div style="background: linear-gradient(135deg, #0f0c29, #1a1a4e, #24243e); padding: 2rem; border-radius: 12px; margin-bottom: 1.5rem; text-align: center;">
    <h1 style="color: #e0e0ff; margin: 0;">🎯 Interview Prep & Upskilling Coach</h1>
    <p style="color: #a0a0d0; margin: 0.5rem 0 0 0;">AI-powered mock interviews calibrated to top-company standards</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Access Control
# ---------------------------------------------------------------------------
interview_password = None
try:
    interview_password = st.secrets.get("INTERVIEW_PASSWORD", None)
except BaseException:
    pass

api_key = None
try:
    api_key = st.secrets.get("INTERVIEW_API_KEY", None) or st.secrets.get("GEMINI_API_KEY", None)
except BaseException:
    pass
if not api_key:
    api_key = os.environ.get("INTERVIEW_API_KEY") or os.environ.get("GEMINI_API_KEY")

# Gate logic
if interview_password:
    if "interview_authenticated" not in st.session_state:
        st.session_state.interview_authenticated = False

    if not st.session_state.interview_authenticated:
        # Recruiter showcase card
        st.markdown("""
<div style="background: linear-gradient(135deg, #1a1a3e, #2d2b6b); border: 1px solid #7c83ff; border-radius: 12px; padding: 2rem; margin: 1rem 0;">
    <h3 style="color: #e0e0ff; margin-top: 0;">🔒 Personal Development Tool</h3>
    <p style="color: #c0c0e0; line-height: 1.7;">
        Rodel built an <strong style="color: #7c83ff;">AI-powered interview coach and upskilling platform</strong> that:
    </p>
    <ul style="color: #c0c0e0; line-height: 2;">
        <li>📄 Analyzes any job description to generate a tailored interviewer persona</li>
        <li>🎙️ Conducts realistic voice-based mock interviews calibrated to FAANG standards</li>
        <li>📊 Provides real-time STAR-framework coaching with per-answer grading</li>
        <li>📚 Recommends targeted learning resources for continuous upskilling</li>
        <li>📈 Tracks progress across sessions for long-term professional growth</li>
    </ul>
    <p style="color: #a0a0d0; font-size: 0.85rem; margin-bottom: 0;">
        This tool demonstrates Rodel's ability to design and ship production-grade AI applications
        with complex multi-turn reasoning, voice UX, and persistent data tracking.
    </p>
</div>
        """, unsafe_allow_html=True)

        with st.form("auth_form"):
            pwd = st.text_input("Enter access password:", type="password")
            if st.form_submit_button("Unlock", use_container_width=True):
                if pwd == interview_password:
                    st.session_state.interview_authenticated = True
                    st.rerun()
                else:
                    st.error("Incorrect password.")
        st.stop()

if not api_key:
    st.error("🔑 API Key not found. Set `INTERVIEW_API_KEY` or `GEMINI_API_KEY` in Streamlit secrets.")
    st.stop()

if not ENGINE_OK:
    st.error("Interview engine failed to load. Check server logs.")
    st.stop()

# ---------------------------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------------------------
DEFAULTS = {
    "iv_phase": "setup",       # setup | interview | report
    "iv_jd": "",
    "iv_analysis": None,
    "iv_current_q": 0,
    "iv_answers": {},
    "iv_evaluations": {},
    "iv_skipped": 0,
    "iv_help_count": 0,
    "iv_answer_times": {},
    "iv_report": None,
    "iv_voice_on": True,
    "iv_voice_speed": 1.15,
    "iv_session_id": None,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


def _reset_session():
    for k, v in DEFAULTS.items():
        st.session_state[k] = v


def _grade_color(grade):
    return {"A": "#10b981", "B": "#3b82f6", "C": "#f59e0b", "D": "#f97316", "F": "#ef4444"}.get(grade, "#888")


def _type_emoji(qtype):
    return {"Technical": "🔧", "Behavioral": "🧠", "System Design": "📐", "Scenario": "🎯", "Leadership": "👥"}.get(qtype, "❓")


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🎯 Interview Coach")
    st.session_state.iv_voice_on = st.toggle("🔊 Interviewer Voice", value=st.session_state.iv_voice_on, key="iv_voice_toggle")
    if st.session_state.iv_voice_on:
        st.session_state.iv_voice_speed = st.slider(
            "🗣️ Voice Speed",
            min_value=0.5, max_value=2.0, value=st.session_state.iv_voice_speed, step=0.05,
            format="%.2fx",
            help="0.5 = slow, 1.0 = normal, 1.15 = conversational, 2.0 = fast",
            key="iv_speed_slider",
        )

    st.divider()
    progress = get_progress_summary()
    if progress["total_sessions"] > 0:
        st.markdown("### 📈 Your Progress")
        st.metric("Total Sessions", progress["total_sessions"])
        st.metric("Latest Score", f"{progress['latest_score']:.0f}/100")
        st.metric("Best Score", f"{progress['best_score']:.0f}/100")
        if progress["improvement"] != 0:
            st.metric("Trend", f"{progress['improvement']:+.0f} pts", delta=f"{progress['improvement']:+.0f}")
        st.caption(f"Latest: {progress['latest_readiness']}")
    else:
        st.caption("No sessions yet. Complete your first interview to start tracking progress!")

    st.divider()
    if st.session_state.iv_phase != "setup":
        if st.button("🔄 New Interview", use_container_width=True):
            _reset_session()
            st.rerun()


# ========================== PHASE 1: SETUP ==========================
if st.session_state.iv_phase == "setup":
    st.markdown("### 📄 Paste the Job Description")
    st.caption("The AI will analyze it to create a tailored interviewer and question bank.")

    jd_input = st.text_area(
        "Job Description",
        height=250,
        placeholder="Paste the full job description here...",
        key="jd_textarea",
    )

    if st.button("🚀 Start Interview", type="primary", use_container_width=True, disabled=len(jd_input.strip()) < 50):
        if len(jd_input.strip()) < 50:
            st.warning("Please paste a more detailed job description (at least 50 characters).")
        else:
            with st.spinner("🔍 Analyzing job description and preparing your interviewer..."):
                try:
                    analysis = analyze_job_description(jd_input, api_key)
                    st.session_state.iv_jd = jd_input
                    st.session_state.iv_analysis = analysis
                    st.session_state.iv_phase = "interview"
                    st.session_state.iv_current_q = 0
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to analyze JD: {e}")

    # Fetch recent job descriptions
    recent_jds = get_recent_jds()
    
    if recent_jds:
        st.divider()
        st.markdown("### 🕒 Recent Job Descriptions")
        for s in recent_jds:
            col1, col2 = st.columns([3, 1])
            with col1:
                status_icon = "⏳" if s.get("status") == "incomplete" else "✅"
                st.markdown(
                    f'**{status_icon} {s.get("jd_title", "Untitled")}**<br>'
                    f'<span style="color: #a0a0d0; font-size: 0.8rem;">'
                    f'{s.get("role_level", "")} · {s.get("industry", "")} · '
                    f'Progress: {s.get("answered_count", 0) + s.get("skipped_count", 0)}/{s.get("questions_count", 8)} questions'
                    f'</span>',
                    unsafe_allow_html=True
                )
            with col2:
                if s.get("status") == "incomplete":
                    if st.button("▶️ Resume", key=f"resume_{s['id']}", use_container_width=True):
                        # Restore state
                        try:
                            state = json.loads(s.get("session_state_json", "{}"))
                            if state:
                                st.session_state.iv_jd = s.get("jd_text", "")
                                st.session_state.iv_analysis = state.get("analysis")
                                st.session_state.iv_answers = state.get("answers", {})
                                st.session_state.iv_evaluations = state.get("evaluations", {})
                                st.session_state.iv_current_q = state.get("current_q", 0)
                                st.session_state.iv_skipped = state.get("skipped", 0)
                                st.session_state.iv_help_count = state.get("help_count", 0)
                                st.session_state.iv_answer_times = state.get("answer_times", {})
                                st.session_state.iv_session_id = s['id']
                                st.session_state.iv_phase = "interview"
                                st.rerun()
                            else:
                                st.error("Failed to parse saved session state.")
                        except Exception as e:
                            st.error(f"Error resuming: {e}")
                else:
                    if st.button("🔄 Start Fresh", key=f"fresh_{s['id']}", use_container_width=True):
                        # Start a new interview with the same JD text
                        jd_text = s.get("jd_text", "")
                        with st.spinner("🔍 Analyzing job description..."):
                            try:
                                analysis = analyze_job_description(jd_text, api_key)
                                st.session_state.iv_jd = jd_text
                                st.session_state.iv_analysis = analysis
                                st.session_state.iv_phase = "interview"
                                st.session_state.iv_current_q = 0
                                st.session_state.iv_session_id = None
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to analyze JD: {e}")
            st.markdown("<hr style='margin: 0.5rem 0; border-color: #334'>", unsafe_allow_html=True)


# ========================== PHASE 2: INTERVIEW ==========================
elif st.session_state.iv_phase == "interview":
    analysis = st.session_state.iv_analysis
    persona = analysis.get("persona", {})
    questions = analysis.get("questions", [])
    current_q = st.session_state.iv_current_q
    total_q = len(questions)

    # Persona card
    st.markdown(
        f'<div style="background: rgba(30,30,60,0.7); border: 1px solid #7c83ff; border-radius: 10px; '
        f'padding: 1rem 1.5rem; margin-bottom: 1rem;">'
        f'<strong style="color: #7c83ff; font-size: 1.1rem;">👤 {persona.get("name", "Interviewer")}</strong>'
        f'<span style="color: #a0a0d0;"> — {persona.get("title", "Senior Manager")}</span><br>'
        f'<span style="color: #888; font-size: 0.85rem;">{persona.get("company_style", "")}</span></div>',
        unsafe_allow_html=True,
    )

    # Progress bar
    answered_count = len(st.session_state.iv_answers) + st.session_state.iv_skipped
    st.progress(answered_count / total_q if total_q else 0, text=f"Question {current_q + 1} of {total_q}")

    if current_q < total_q:
        q = questions[current_q]
        qtype = q.get("type", "Technical")
        emoji = _type_emoji(qtype)

        # Question display
        st.markdown(
            f'<div style="background: rgba(20,20,50,0.8); border-radius: 10px; padding: 1.5rem; margin: 1rem 0;">'
            f'<span style="background: rgba(124,131,255,0.2); color: #7c83ff; padding: 0.2rem 0.6rem; '
            f'border-radius: 12px; font-size: 0.75rem; font-weight: 600;">{emoji} {qtype}</span>'
            f'<span style="color: #a0a0d0; font-size: 0.75rem; margin-left: 0.5rem;">Domain: {q.get("domain", "General")}</span>'
            f'<p style="color: #e0e0ff; font-size: 1.1rem; margin-top: 0.8rem; line-height: 1.6;">{q["question"]}</p>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # STAR reminder for behavioral
        if qtype == "Behavioral":
            st.info("💡 **STAR Framework:** Structure your answer as **Situation** → **Task** → **Action** → **Result**")

        # Speak the question
        if st.session_state.iv_voice_on and f"iv_spoken_{current_q}" not in st.session_state:
            render_browser_tts(q["question"], rate=st.session_state.iv_voice_speed)
            st.session_state[f"iv_spoken_{current_q}"] = True

        # Answer input
        st.markdown("#### Your Response")

        # Mic input
        mic_clicked = st.button("🎤 Toggle Microphone", key=f"mic_{current_q}", use_container_width=True)

        if mic_clicked:
            st.components.v1.html("""
            <div id="mic-container" style="background: rgba(15,12,41,0.9); border: 1px solid #7c83ff; border-radius: 8px; padding: 1rem; margin: 0.5rem 0; font-family: sans-serif; color: #e0e0ff;">
                <div style="display: flex; gap: 10px; margin-bottom: 10px;">
                    <button id="btn-start" style="background: #10b981; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; font-weight: bold;">🔴 Start Recording</button>
                    <button id="btn-stop" style="background: #ef4444; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; font-weight: bold;" disabled>⏹️ Stop Recording</button>
                </div>
                <div id="mic-status" style="font-size: 0.9rem; color: #a0a0d0; margin-bottom: 10px;">Waiting to start...</div>
                <div id="mic-transcript" style="background: rgba(0,0,0,0.3); padding: 10px; border-radius: 4px; min-height: 60px; font-size: 0.95rem;"></div>
                <div style="color: #7c83ff; font-size: 0.8rem; margin-top: 10px;">💡 When finished, copy the text above and paste it into the answer box below.</div>
            </div>
            <script>
                const btnStart = document.getElementById('btn-start');
                const btnStop = document.getElementById('btn-stop');
                const statusEl = document.getElementById('mic-status');
                const transcriptEl = document.getElementById('mic-transcript');
                
                const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
                if (!SR) { 
                    statusEl.innerHTML = '❌ Your browser does not support Speech Recognition. Use Chrome or Edge.'; 
                    btnStart.disabled = true;
                } else {
                    const r = new SR(); 
                    r.lang = 'en-US'; 
                    r.interimResults = true;
                    r.continuous = true; // Crucial for manual control
                    
                    let finalTranscript = '';

                    r.onstart = () => { 
                        statusEl.innerHTML = '🔴 Listening... (Speak freely, it will not cut you off until you click Stop)'; 
                        btnStart.disabled = true;
                        btnStop.disabled = false;
                    };
                    
                    r.onresult = (e) => {
                        let interimTranscript = '';
                        for (let i = e.resultIndex; i < e.results.length; ++i) {
                            if (e.results[i].isFinal) {
                                finalTranscript += e.results[i][0].transcript + ' ';
                            } else {
                                interimTranscript += e.results[i][0].transcript;
                            }
                        }
                        transcriptEl.innerHTML = finalTranscript + '<i style="color:#a0a0d0;">' + interimTranscript + '</i>';
                    };
                    
                    r.onerror = (e) => { 
                        statusEl.innerHTML = '❌ Error: ' + e.error; 
                        btnStart.disabled = false;
                        btnStop.disabled = true;
                    };
                    
                    r.onend = () => { 
                        statusEl.innerHTML = '⏹️ Recording stopped.'; 
                        btnStart.disabled = false;
                        btnStop.disabled = true;
                    };
                    
                    btnStart.onclick = () => { r.start(); };
                    btnStop.onclick = () => { r.stop(); };
                }
            </script>
            """, height=220)

        answer_text = st.text_area(
            "Type or paste your answer here:",
            key=f"answer_{current_q}",
            height=150,
            placeholder="Type your response, or use the mic above and paste the transcript...",
        )

        # Timer tracking
        if f"iv_start_{current_q}" not in st.session_state:
            st.session_state[f"iv_start_{current_q}"] = time.time()

        # Action buttons
        btn_cols = st.columns([2, 2, 1, 2])
        with btn_cols[0]:
            submit_clicked = st.button("✅ Submit Answer", key=f"sub_{current_q}", use_container_width=True, type="primary",
                                       disabled=not answer_text.strip())
        with btn_cols[1]:
            help_clicked = st.button("💡 Help Me Answer", key=f"help_{current_q}", use_container_width=True)
        with btn_cols[2]:
            skip_clicked = st.button("⏭️ Skip", key=f"skip_{current_q}", use_container_width=True)
        with btn_cols[3]:
            end_clicked = st.button("🛑 End Interview", key=f"end_{current_q}", use_container_width=True)

        # Handle actions
        if submit_clicked and answer_text.strip():
            elapsed = time.time() - st.session_state.get(f"iv_start_{current_q}", time.time())
            st.session_state.iv_answer_times[str(current_q)] = elapsed

            with st.spinner("📝 Evaluating your response..."):
                try:
                    ev = evaluate_answer(q["question"], answer_text, st.session_state.iv_jd, qtype, api_key)
                    st.session_state.iv_answers[str(current_q)] = answer_text
                    st.session_state.iv_evaluations[str(current_q)] = ev

                    # Checkpoint session
                    session_data = {
                        "session_id": st.session_state.iv_session_id,
                        "jd_text": st.session_state.iv_jd,
                        "role_level": analysis.get("role_level", ""),
                        "industry": analysis.get("persona", {}).get("industry", ""),
                        "questions_asked": analysis.get("questions", []),
                        "answers": st.session_state.iv_answers,
                        "evaluations": st.session_state.iv_evaluations,
                        "skipped_count": st.session_state.iv_skipped,
                        "help_count": st.session_state.iv_help_count,
                    }
                    full_state = {
                        "analysis": st.session_state.iv_analysis,
                        "answers": st.session_state.iv_answers,
                        "evaluations": st.session_state.iv_evaluations,
                        "current_q": st.session_state.iv_current_q,
                        "skipped": st.session_state.iv_skipped,
                        "help_count": st.session_state.iv_help_count,
                        "answer_times": st.session_state.iv_answer_times,
                    }
                    st.session_state.iv_session_id = save_incomplete_session(session_data, full_state)

                    # Display feedback
                    grade = ev.get("grade", "C")
                    score = ev.get("score", 50)
                    grade_css = grade.replace("+", "").replace("-", "")

                    st.markdown(f'<div style="margin: 1rem 0;"><span class="grade-badge grade-{grade_css}">{grade}</span> <strong style="color: #e0e0ff;">{score}/100</strong>'
                                f'<span style="color: #a0a0d0; margin-left: 1rem;">⏱️ {elapsed:.0f}s</span></div>', unsafe_allow_html=True)

                    st.progress(score / 100)

                    if ev.get("strengths"):
                        st.success("**💪 Strengths:** " + " • ".join(ev["strengths"]))
                    if ev.get("improvements"):
                        st.warning("**🎯 Improve:** " + " • ".join(ev["improvements"]))
                    if ev.get("missing_keywords"):
                        st.info("**🔑 Keywords you missed:** " + ", ".join(ev["missing_keywords"]))

                    # Resources
                    resources = ev.get("resources", [])
                    if resources:
                        st.markdown("**📚 Learning Resources:**")
                        for r in resources:
                            rtype = r.get("type", "Resource")
                            st.markdown(f"- [{r.get('title', 'Link')}]({r.get('url', '#')}) ({rtype})")

                    with st.expander("📖 See Ideal Answer"):
                        ideal = get_best_answer(q["question"], st.session_state.iv_jd, qtype, api_key)
                        st.markdown(ideal)

                    # Advance button
                    if current_q + 1 < total_q:
                        if st.button("➡️ Next Question", key=f"next_{current_q}", type="primary"):
                            st.session_state.iv_current_q += 1
                            st.rerun()
                    else:
                        if st.button("📊 See Final Report", key="final_report", type="primary"):
                            st.session_state.iv_phase = "report"
                            st.rerun()

                except Exception as e:
                    st.error(f"Evaluation error: {e}")

        if help_clicked:
            st.session_state.iv_help_count += 1
            with st.spinner("🧠 Generating ideal answer..."):
                try:
                    ideal = get_best_answer(q["question"], st.session_state.iv_jd, qtype, api_key)
                    st.markdown("### 💡 Suggested Answer")
                    st.markdown(ideal)
                    if st.session_state.iv_voice_on:
                        # Only read a short excerpt
                        render_browser_tts(ideal[:400], rate=st.session_state.iv_voice_speed)
                        
                    # Checkpoint session
                    session_data = {
                        "session_id": st.session_state.iv_session_id,
                        "jd_text": st.session_state.iv_jd,
                        "role_level": analysis.get("role_level", ""),
                        "industry": analysis.get("persona", {}).get("industry", ""),
                        "questions_asked": analysis.get("questions", []),
                        "answers": st.session_state.iv_answers,
                        "evaluations": st.session_state.iv_evaluations,
                        "skipped_count": st.session_state.iv_skipped,
                        "help_count": st.session_state.iv_help_count,
                    }
                    full_state = {
                        "analysis": st.session_state.iv_analysis,
                        "answers": st.session_state.iv_answers,
                        "evaluations": st.session_state.iv_evaluations,
                        "current_q": st.session_state.iv_current_q,
                        "skipped": st.session_state.iv_skipped,
                        "help_count": st.session_state.iv_help_count,
                        "answer_times": st.session_state.iv_answer_times,
                    }
                    st.session_state.iv_session_id = save_incomplete_session(session_data, full_state)
                    
                except Exception as e:
                    st.error(f"Error: {e}")

        if skip_clicked:
            st.session_state.iv_skipped += 1
            
            # Checkpoint session
            session_data = {
                "session_id": st.session_state.iv_session_id,
                "jd_text": st.session_state.iv_jd,
                "role_level": analysis.get("role_level", ""),
                "industry": analysis.get("persona", {}).get("industry", ""),
                "questions_asked": analysis.get("questions", []),
                "answers": st.session_state.iv_answers,
                "evaluations": st.session_state.iv_evaluations,
                "skipped_count": st.session_state.iv_skipped,
                "help_count": st.session_state.iv_help_count,
            }
            full_state = {
                "analysis": st.session_state.iv_analysis,
                "answers": st.session_state.iv_answers,
                "evaluations": st.session_state.iv_evaluations,
                "current_q": st.session_state.iv_current_q + 1, # Save the advanced state
                "skipped": st.session_state.iv_skipped,
                "help_count": st.session_state.iv_help_count,
                "answer_times": st.session_state.iv_answer_times,
            }
            st.session_state.iv_session_id = save_incomplete_session(session_data, full_state)
            
            if current_q + 1 < total_q:
                st.session_state.iv_current_q += 1
                st.rerun()
            else:
                st.session_state.iv_phase = "report"
                st.rerun()

        if end_clicked:
            st.session_state.iv_phase = "report"
            st.rerun()


# ========================== PHASE 3: REPORT ==========================
elif st.session_state.iv_phase == "report":
    analysis = st.session_state.iv_analysis or {}

    if st.session_state.iv_report is None:
        with st.spinner("📊 Generating your comprehensive coaching report..."):
            try:
                session_data = {
                    "session_id": st.session_state.iv_session_id,
                    "jd_text": st.session_state.iv_jd,
                    "role_level": analysis.get("role_level", ""),
                    "industry": analysis.get("persona", {}).get("industry", ""),
                    "questions_asked": analysis.get("questions", []),
                    "answers": st.session_state.iv_answers,
                    "evaluations": st.session_state.iv_evaluations,
                    "skipped_count": st.session_state.iv_skipped,
                    "help_count": st.session_state.iv_help_count,
                    "full_state": {
                        "analysis": st.session_state.iv_analysis,
                        "answers": st.session_state.iv_answers,
                        "evaluations": st.session_state.iv_evaluations,
                        "current_q": st.session_state.iv_current_q,
                        "skipped": st.session_state.iv_skipped,
                        "help_count": st.session_state.iv_help_count,
                        "answer_times": st.session_state.iv_answer_times,
                    }
                }
                report = generate_interview_report(session_data, api_key)
                st.session_state.iv_report = report

                # Save to SQLite for long-term tracking
                try:
                    save_session(session_data, report)
                except Exception:
                    pass  # Don't crash if DB write fails

            except Exception as e:
                st.error(f"Report generation error: {e}")
                st.session_state.iv_report = "Report generation failed. Please try again."

    # Display report
    st.markdown(st.session_state.iv_report)

    # Per-question breakdown table
    questions = analysis.get("questions", [])
    evals = st.session_state.iv_evaluations
    if evals:
        st.divider()
        st.markdown("### 📋 Question-by-Question Breakdown")
        for i, q in enumerate(questions):
            ev = evals.get(str(i))
            if ev:
                grade = ev.get("grade", "?")
                score = ev.get("score", 0)
                color = _grade_color(grade)
                elapsed = st.session_state.iv_answer_times.get(str(i), 0)
                st.markdown(
                    f'<div style="background: rgba(30,30,60,0.5); border-left: 3px solid {color}; '
                    f'padding: 0.6rem 1rem; border-radius: 6px; margin-bottom: 0.4rem;">'
                    f'<strong style="color: {color};">{grade}</strong> '
                    f'<span style="color: #e0e0ff;">({score}/100)</span> '
                    f'<span style="color: #a0a0d0; font-size: 0.85rem;">⏱️ {elapsed:.0f}s — '
                    f'{_type_emoji(q.get("type", ""))} {q.get("type", "")}: {q["question"][:80]}...</span></div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div style="background: rgba(30,30,60,0.3); border-left: 3px solid #666; '
                    f'padding: 0.6rem 1rem; border-radius: 6px; margin-bottom: 0.4rem;">'
                    f'<span style="color: #888;">⏭️ Skipped: {q["question"][:80]}...</span></div>',
                    unsafe_allow_html=True,
                )

    st.divider()
    if st.button("🔄 Start New Interview", type="primary", use_container_width=True):
        _reset_session()
        st.rerun()
