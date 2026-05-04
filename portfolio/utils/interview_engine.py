"""
Interview Engine — AI-Powered Mock Interview & Upskilling Coach

Provides:
    - Job description analysis → interviewer persona + tailored question bank
    - Per-answer evaluation with grades, feedback, and learning resources
    - Ideal answer generation using STAR framework
    - End-of-session report with readiness assessment and study plan
    - SQLite-backed session history for long-term progress tracking
"""

import os
import json
import sqlite3
import datetime
import google.generativeai as genai
import streamlit as st
from typing import Dict, Any, List, Optional

# ---------------------------------------------------------------------------
# Model Fallback Chain (mirrors rag_engine)
# ---------------------------------------------------------------------------
MODEL_CHAIN = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
]

# ---------------------------------------------------------------------------
# Database Path
# ---------------------------------------------------------------------------
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DATA_DIR, "interview_history.db")


def _call_gemini(prompt: str, api_key: str, temperature: float = 0.7, max_tokens: int = 4096) -> str:
    """Call Gemini with automatic model fallback. Returns raw text response."""
    genai.configure(api_key=api_key)
    gen_config = genai.types.GenerationConfig(
        temperature=temperature,
        max_output_tokens=max_tokens,
    )

    last_error = None
    for model_name in MODEL_CHAIN:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt, generation_config=gen_config)
            if response and response.candidates:
                return response.text
        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            if "429" in str(e) or "quota" in error_str or "rate" in error_str or "not found" in error_str:
                continue
            raise

    raise Exception(f"All models exhausted. Last error: {last_error}")


def _parse_json_response(text: str) -> dict:
    """Extract JSON from an LLM response that may include markdown fences."""
    # Strip markdown code fences if present
    cleaned = text.strip()
    if cleaned.startswith("```"):
        # Remove first line (```json) and last line (```)
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:])
        if cleaned.strip().endswith("```"):
            cleaned = cleaned.strip()[:-3]
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to find JSON object in the text
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(text[start:end])
        raise


# ---------------------------------------------------------------------------
# JD Analysis
# ---------------------------------------------------------------------------
def analyze_job_description(jd_text: str, api_key: str) -> Dict[str, Any]:
    """
    Analyze a job description and generate an interviewer persona + question bank.

    Returns dict with keys:
        persona: {name, title, company_style, industry}
        role_level: str
        skill_domains: list[str]
        questions: list[{question, type, domain}]
    """
    prompt = f"""You are an expert interview coach. Analyze this job description and create a realistic mock interview setup.

JOB DESCRIPTION:
{jd_text}

Return a JSON object with this EXACT structure (no markdown, just raw JSON):
{{
    "persona": {{
        "name": "A realistic interviewer first name",
        "title": "Their job title (e.g., Senior Engineering Manager)",
        "company_style": "Brief description of how top companies in this industry interview (e.g., 'FAANG-style with system design focus')",
        "industry": "The industry this role is in"
    }},
    "role_level": "One of: Junior, Mid-Level, Senior, Staff, Principal, Director",
    "skill_domains": ["List of 5-8 key skill areas from the JD"],
    "questions": [
        {{
            "question": "The full interview question text",
            "type": "One of: Technical, Behavioral, System Design, Scenario, Leadership",
            "domain": "Which skill domain this tests"
        }}
    ]
}}

Generate exactly 8 questions with this mix:
- 2 Behavioral questions (using STAR-framework expectations)
- 3 Technical questions (deep-dive on skills from the JD)
- 1 System Design question (architecture/scale)
- 1 Scenario question (real-world problem solving)
- 1 Leadership question (team dynamics, decision making)

Calibrate difficulty to how top companies in this industry would interview for this role level. Questions should be specific to the JD, not generic.
"""
    raw = _call_gemini(prompt, api_key, temperature=0.4)
    return _parse_json_response(raw)


# ---------------------------------------------------------------------------
# Answer Evaluation
# ---------------------------------------------------------------------------
def evaluate_answer(
    question: str,
    answer: str,
    jd_text: str,
    question_type: str,
    api_key: str,
) -> Dict[str, Any]:
    """
    Evaluate a candidate's answer and provide detailed coaching feedback.

    Returns dict with keys:
        grade: str (A/B/C/D/F)
        score: int (0-100)
        strengths: list[str]
        improvements: list[str]
        missing_keywords: list[str]
        resources: list[{title, url, type}]
    """
    prompt = f"""You are a senior interview coach evaluating a candidate's response.

JOB DESCRIPTION CONTEXT:
{jd_text[:2000]}

INTERVIEW QUESTION ({question_type}):
{question}

CANDIDATE'S ANSWER:
{answer if answer.strip() else "(Candidate did not provide an answer)"}

Evaluate this answer as a top-tier interviewer would. Return a JSON object with this EXACT structure:
{{
    "grade": "A letter grade: A (excellent), B (good), C (average), D (below average), F (poor/no answer)",
    "score": 85,
    "strengths": ["What the candidate did well - be specific"],
    "improvements": ["Specific, actionable improvements"],
    "missing_keywords": ["Technical terms or concepts they should have mentioned"],
    "resources": [
        {{
            "title": "Resource name",
            "url": "https://actual-url-to-resource",
            "type": "One of: Course, Documentation, Book, Video, Practice Platform, Article"
        }}
    ]
}}

For resources, provide 2-3 REAL, currently accessible learning resources directly relevant to the skill gaps identified. These can be:
- Official documentation (AWS docs, GCP docs, Kubernetes docs, etc.)
- Free courses (Coursera, edX, freeCodeCamp, AWS Skill Builder)
- Books (with Amazon/publisher links)
- YouTube channels/videos (specific technical channels)
- Practice platforms (LeetCode, HackerRank, Pramp, etc.)

{"For behavioral questions, evaluate STAR framework usage (Situation, Task, Action, Result)." if question_type == "Behavioral" else ""}
{"For system design questions, evaluate trade-off analysis, scalability thinking, and component selection." if question_type == "System Design" else ""}
"""
    raw = _call_gemini(prompt, api_key, temperature=0.3)
    return _parse_json_response(raw)


# ---------------------------------------------------------------------------
# Best Answer Generation
# ---------------------------------------------------------------------------
def get_best_answer(
    question: str,
    jd_text: str,
    question_type: str,
    api_key: str,
    user_answer: Optional[str] = None,
) -> str:
    """Generate an expert-level ideal answer and a polished version of the user's answer."""
    framework_hint = ""
    if question_type == "Behavioral":
        framework_hint = "\nUse the STAR framework (Situation, Task, Action, Result). Label each section clearly."
    elif question_type == "System Design":
        framework_hint = "\nStructure: Requirements → High-Level Design → Components → Trade-offs → Scalability."
    elif question_type == "Leadership":
        framework_hint = "\nDemonstrate strategic thinking, stakeholder management, and team empowerment."

    user_context = ""
    instructions = """Provide the IDEAL answer a top candidate would give. This should be:
- Specific and detailed (not vague or generic)
- Demonstrate deep expertise relevant to the JD
- Show real-world experience (use realistic examples)
- Be the kind of answer that would get a "strong hire" signal
""" + framework_hint + """

After the ideal answer, add a section titled "💡 WHY THIS ANSWER WORKS:" explaining what makes this answer effective.
"""

    if user_answer and user_answer.strip():
        user_context = f"\nCANDIDATE'S ORIGINAL ANSWER:\n{user_answer}\n"
        instructions = """You must provide TWO versions of the answer:

### 🌟 1. The Perfect Example
Provide a generalized, top-tier ideal answer to this question. Demonstrate deep expertise and use realistic examples.
""" + framework_hint + """

### 🛠️ 2. Your Answer, Polished
Take the CANDIDATE'S ORIGINAL ANSWER and rewrite it to be a top-tier "strong hire" response. 
Keep their core scenario, context, and points, but improve the delivery, technical depth, and structure.
Make them sound like an absolute expert while staying true to their original story.

### 💡 Why These Work
Briefly explain what makes these answers effective.
"""

    prompt = f"""You are a career coach helping a candidate prepare for a top-tier interview.

JOB DESCRIPTION CONTEXT:
{jd_text[:2000]}

INTERVIEW QUESTION ({question_type}):
{question}
{user_context}
{instructions}
"""
    return _call_gemini(prompt, api_key, temperature=0.5)


# ---------------------------------------------------------------------------
# End-of-Interview Report
# ---------------------------------------------------------------------------
def generate_interview_report(
    session_data: Dict[str, Any],
    api_key: str,
) -> str:
    """
    Generate a comprehensive end-of-interview coaching report.

    session_data should contain:
        jd_text, persona, questions_asked, answers, evaluations, skipped_count
    """
    # Build a summary of all Q&A with grades
    qa_summary = ""
    for i, q in enumerate(session_data.get("questions_asked", [])):
        answer = session_data.get("answers", {}).get(str(i), "(skipped)")
        eval_data = session_data.get("evaluations", {}).get(str(i), {})
        grade = eval_data.get("grade", "N/A")
        score = eval_data.get("score", 0)
        qa_summary += f"\nQ{i+1} [{q.get('type', 'Unknown')}]: {q['question']}\n"
        qa_summary += f"Answer: {answer[:300]}...\n" if len(answer) > 300 else f"Answer: {answer}\n"
        qa_summary += f"Grade: {grade} ({score}/100)\n"

    total_questions = len(session_data.get("questions_asked", []))
    answered = len(session_data.get("answers", {}))
    skipped = session_data.get("skipped_count", 0)
    helped = session_data.get("help_count", 0)

    prompt = f"""You are a senior career coach providing a comprehensive interview debrief.

JOB DESCRIPTION:
{session_data.get('jd_text', '')[:1500]}

INTERVIEW PERFORMANCE SUMMARY:
- Questions asked: {total_questions}
- Questions answered: {answered}
- Questions skipped: {skipped}
- Times candidate asked for help: {helped}

DETAILED Q&A:
{qa_summary}

Provide a thorough coaching report in markdown format with these sections:

## 📊 Overall Assessment
- Overall readiness: One of "✅ Ready to Interview", "🟡 Almost There — Needs Polish", or "🔴 Needs More Preparation"
- Overall score (average of individual scores)
- Brief summary of performance

## 💪 Top Strengths
- 3-4 specific things the candidate did well across all answers

## 🎯 Priority Improvements
- Top 3-4 areas that need the most work, with specific action items

## 📚 Personalized Study Plan
For each improvement area, provide:
- What to study
- Specific resources (courses, docs, books, videos — use REAL URLs)
- Estimated time to improve (e.g., "2-3 hours of focused practice")

## 🏢 Industry Tips
- 2-3 tips specific to how top companies in this industry evaluate candidates
- What differentiates a "hire" from "strong hire" at these companies

## 🔄 Recommended Next Steps
- Specific actions the candidate should take before their real interview
- Suggest how often to practice and what to focus on next session

Be direct, honest, and encouraging. The goal is to help this person land the job.
"""
    return _call_gemini(prompt, api_key, temperature=0.5, max_tokens=4096)


# ---------------------------------------------------------------------------
# SQLite Persistence — Long-Term Progress Tracking
# ---------------------------------------------------------------------------
def _init_db():
    """Initialize the SQLite database for interview history."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            jd_title TEXT,
            jd_text TEXT,
            role_level TEXT,
            industry TEXT,
            questions_count INTEGER,
            answered_count INTEGER,
            skipped_count INTEGER,
            help_count INTEGER,
            overall_score REAL,
            overall_grade TEXT,
            readiness TEXT,
            evaluations_json TEXT,
            report_text TEXT
        )
    """)
    
    # Check for new columns to support session resumption
    c.execute("PRAGMA table_info(sessions)")
    columns = [row[1] for row in c.fetchall()]
    if "status" not in columns:
        c.execute("ALTER TABLE sessions ADD COLUMN status TEXT DEFAULT 'completed'")
    if "session_state_json" not in columns:
        c.execute("ALTER TABLE sessions ADD COLUMN session_state_json TEXT")
        
    conn.commit()
    conn.close()


def save_session(session_data: Dict[str, Any], report_text: str) -> int:
    """Save a completed interview session to the database. Returns the session ID."""
    _init_db()

    # Calculate overall score
    evals = session_data.get("evaluations", {})
    scores = [e.get("score", 0) for e in evals.values() if isinstance(e, dict)]
    overall_score = sum(scores) / len(scores) if scores else 0

    # Determine overall grade
    if overall_score >= 90:
        overall_grade = "A"
    elif overall_score >= 80:
        overall_grade = "B"
    elif overall_score >= 70:
        overall_grade = "C"
    elif overall_score >= 60:
        overall_grade = "D"
    else:
        overall_grade = "F"

    # Extract readiness from report
    readiness = "Unknown"
    if "✅ Ready" in report_text:
        readiness = "Ready"
    elif "🟡 Almost" in report_text:
        readiness = "Almost There"
    elif "🔴 Needs" in report_text:
        readiness = "Needs Work"

    # Extract a short JD title (first line or first 80 chars)
    jd_text = session_data.get("jd_text", "")
    jd_title = jd_text.split("\n")[0][:80] if jd_text else "Untitled"

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Check if this session was previously saved as incomplete
    session_id = session_data.get("session_id")
    
    if session_id:
        c.execute("""
            UPDATE sessions SET 
                timestamp = ?, answered_count = ?, skipped_count = ?, help_count = ?,
                overall_score = ?, overall_grade = ?, readiness = ?, evaluations_json = ?, 
                report_text = ?, status = 'completed', session_state_json = ?
            WHERE id = ?
        """, (
            datetime.datetime.now().isoformat(),
            len(session_data.get("answers", {})),
            session_data.get("skipped_count", 0),
            session_data.get("help_count", 0),
            overall_score,
            overall_grade,
            readiness,
            json.dumps(evals),
            report_text,
            json.dumps(session_data.get("full_state", {})),
            session_id
        ))
    else:
        c.execute("""
            INSERT INTO sessions (
                timestamp, jd_title, jd_text, role_level, industry,
                questions_count, answered_count, skipped_count, help_count,
                overall_score, overall_grade, readiness,
                evaluations_json, report_text, status, session_state_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'completed', ?)
        """, (
            datetime.datetime.now().isoformat(),
            jd_title,
            jd_text,
            session_data.get("role_level", ""),
            session_data.get("industry", ""),
            len(session_data.get("questions_asked", [])),
            len(session_data.get("answers", {})),
            session_data.get("skipped_count", 0),
            session_data.get("help_count", 0),
            overall_score,
            overall_grade,
            readiness,
            json.dumps(evals),
            report_text,
            json.dumps(session_data.get("full_state", {}))
        ))
        session_id = c.lastrowid
        
    conn.commit()
    conn.close()
    return session_id


def save_incomplete_session(session_data: Dict[str, Any], full_state: Dict[str, Any]) -> int:
    """Save an incomplete session mid-interview to allow resuming later."""
    _init_db()
    
    jd_text = session_data.get("jd_text", "")
    jd_title = jd_text.split("\n")[0][:80] if jd_text else "Untitled"
    session_id = session_data.get("session_id")
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    if session_id:
        c.execute("""
            UPDATE sessions SET 
                timestamp = ?, answered_count = ?, skipped_count = ?, help_count = ?,
                evaluations_json = ?, session_state_json = ?
            WHERE id = ?
        """, (
            datetime.datetime.now().isoformat(),
            len(session_data.get("answers", {})),
            session_data.get("skipped_count", 0),
            session_data.get("help_count", 0),
            json.dumps(session_data.get("evaluations", {})),
            json.dumps(full_state),
            session_id
        ))
    else:
        c.execute("""
            INSERT INTO sessions (
                timestamp, jd_title, jd_text, role_level, industry,
                questions_count, answered_count, skipped_count, help_count,
                status, session_state_json, evaluations_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'incomplete', ?, ?)
        """, (
            datetime.datetime.now().isoformat(),
            jd_title,
            jd_text,
            session_data.get("role_level", ""),
            session_data.get("industry", ""),
            len(session_data.get("questions_asked", [])),
            len(session_data.get("answers", {})),
            session_data.get("skipped_count", 0),
            session_data.get("help_count", 0),
            json.dumps(full_state),
            json.dumps(session_data.get("evaluations", {}))
        ))
        session_id = c.lastrowid
        
    conn.commit()
    conn.close()
    return session_id


def get_session_history() -> List[Dict[str, Any]]:
    """Load all past interview sessions for progress tracking."""
    _init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM sessions ORDER BY timestamp DESC")
    rows = [dict(row) for row in c.fetchall()]
    conn.close()
    return rows


def get_progress_summary() -> Dict[str, Any]:
    """Calculate progress metrics across all sessions."""
    sessions = get_session_history()
    if not sessions:
        return {"total_sessions": 0}

    scores = [s["overall_score"] for s in sessions if s["overall_score"]]
    return {
        "total_sessions": len(sessions),
        "average_score": sum(scores) / len(scores) if scores else 0,
        "best_score": max(scores) if scores else 0,
        "latest_score": scores[0] if scores else 0,
        "latest_readiness": sessions[0].get("readiness", "Unknown"),
        "improvement": scores[0] - scores[-1] if len(scores) > 1 else 0,
        "sessions": sessions,
    }


def get_recent_jds(limit: int = 5) -> List[Dict[str, Any]]:
    """Fetch the most recent unique Job Descriptions for quick resume/restart."""
    _init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Get the latest session for each unique JD
    c.execute("""
        SELECT id, timestamp, jd_title, jd_text, status, role_level, industry, answered_count, questions_count, session_state_json
        FROM sessions
        GROUP BY jd_text
        ORDER BY timestamp DESC
        LIMIT ?
    """, (limit,))
    
    rows = [dict(row) for row in c.fetchall()]
    conn.close()
    return rows
