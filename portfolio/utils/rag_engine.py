"""
RAG Engine for the AI Chat — "Ask Rodel"
Uses Gemini API for both embeddings and generation.
Ingests profile data, knowledge.txt, and project READMEs at startup.
"""
import os
import json
import numpy as np
import streamlit as st

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PORTFOLIO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
PORTFOLIO_DIR = os.path.dirname(os.path.dirname(__file__))

KNOWLEDGE_SOURCES = [
    # (label, path)
    ("knowledge", os.path.join(PORTFOLIO_ROOT, "knowledge.txt")),
    ("profile", os.path.join(PORTFOLIO_DIR, "data", "profile_data.json")),
    ("readme_root", os.path.join(PORTFOLIO_ROOT, "README.md")),
    ("readme_project1", os.path.join(PORTFOLIO_ROOT, "projects", "01-secure-rag", "README.md")),
    ("readme_project2", os.path.join(PORTFOLIO_ROOT, "projects", "02-sentinel-ai", "README.md")),
    ("readme_project3", os.path.join(PORTFOLIO_ROOT, "projects", "03-governance-shield", "README.md")),
    ("readme_project4", os.path.join(PORTFOLIO_ROOT, "projects", "04-incident-responder", "README.md")),
    ("readme_project5", os.path.join(PORTFOLIO_ROOT, "projects", "05-drift-evaluator", "README.md")),
]

SYSTEM_PROMPT = """You are Rodel Agcaoili, a Senior Cloud Engineer and GenAI Architect. You are speaking directly with a recruiter or hiring manager who is evaluating your portfolio.

RULES:
- Answer in first person ("I", "my", "I've built...")
- Be professional but personable — keep the conversation engaging
- Ground ALL answers strictly in the provided context from your profile and project documentation
- If asked something not covered in your context, say: "That's a great question — I'd love to discuss that further. Feel free to reach out to me directly via the contact info on my profile page."
- NEVER fabricate experience, certifications, skills, or accomplishments not present in the context
- Provide detailed technical answers when asked about specific projects or skills, but stay concise for general questions
- When discussing projects, reference specific technical details from the project documentation
- Be honest and genuine — don't oversell, but don't undersell either
- If asked about salary, compensation, or reasons for leaving a role, politely redirect: "I'd prefer to discuss that in a live conversation."
"""

# ---------------------------------------------------------------------------
# Document Loading & Chunking
# ---------------------------------------------------------------------------
def _load_documents():
    """Load all knowledge source documents."""
    documents = []
    for label, path in KNOWLEDGE_SOURCES:
        if not os.path.exists(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            # For JSON files, convert to readable text
            if path.endswith(".json"):
                try:
                    data = json.loads(content)
                    content = _json_to_text(data, label)
                except json.JSONDecodeError:
                    pass

            documents.append({"label": label, "content": content, "path": path})
        except Exception:
            continue

    # Also try to load LinkedIn PDF if present
    pdf_path = os.path.join(PORTFOLIO_DIR, "data", "linkedin_profile.pdf")
    if os.path.exists(pdf_path):
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(pdf_path)
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            if text.strip():
                documents.append({"label": "linkedin", "content": text, "path": pdf_path})
        except Exception:
            pass

    return documents


def _json_to_text(data, label):
    """Convert profile JSON to readable text for embedding."""
    if label == "profile":
        parts = []
        parts.append(f"Name: {data.get('name', '')}")
        parts.append(f"Title: {data.get('title', '')}")
        parts.append(f"About: {data.get('about', '')}")

        skills = data.get("skills", {})
        for category, skill_list in skills.items():
            parts.append(f"Skills in {category}: {', '.join(skill_list)}")

        for cert in data.get("certifications", []):
            if not cert.startswith("UPDATE"):
                parts.append(f"Certification: {cert}")

        for exp in data.get("experience", []):
            if not exp.get("role", "").startswith("UPDATE"):
                parts.append(f"Experience: {exp.get('role', '')} at {exp.get('company', '')} ({exp.get('period', '')})")
                for h in exp.get("highlights", []):
                    if not h.startswith("UPDATE"):
                        parts.append(f"  - {h}")

        for proj in data.get("projects_summary", []):
            parts.append(f"Project {proj.get('number', '')}: {proj.get('name', '')} — {proj.get('description', '')}")

        return "\n".join(parts)
    return json.dumps(data, indent=2)


def _chunk_text(text, chunk_size=500, overlap=50):
    """Split text into overlapping chunks."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks


# ---------------------------------------------------------------------------
# Embedding & Index
# ---------------------------------------------------------------------------
def _get_embeddings(texts, api_key):
    """Get embeddings from Gemini API."""
    genai.configure(api_key=api_key)
    embeddings = []
    # Process in batches to respect rate limits
    for text in texts:
        try:
            result = genai.embed_content(
                model="models/gemini-embedding-001",
                content=text,
                task_type="retrieval_document"
            )
            embeddings.append(result["embedding"])
        except Exception as e:
            # Return zero vector on failure
            embeddings.append([0.0] * 768)
    return np.array(embeddings, dtype="float32")


def _get_query_embedding(text, api_key):
    """Get a single query embedding."""
    genai.configure(api_key=api_key)
    result = genai.embed_content(
        model="models/gemini-embedding-001",
        content=text,
        task_type="retrieval_query"
    )
    return np.array([result["embedding"]], dtype="float32")


# ---------------------------------------------------------------------------
# RAG Engine (cached per session)
# ---------------------------------------------------------------------------
@st.cache_resource
def build_rag_index(_api_key, _version=2):
    """Build FAISS index from all knowledge sources. Cached for the session."""
    import faiss

    documents = _load_documents()
    if not documents:
        return None, []

    # Chunk all documents
    all_chunks = []
    for doc in documents:
        chunks = _chunk_text(doc["content"])
        for chunk in chunks:
            all_chunks.append({"text": chunk, "source": doc["label"]})

    if not all_chunks:
        return None, []

    # Embed all chunks
    texts = [c["text"] for c in all_chunks]
    embeddings = _get_embeddings(texts, _api_key)

    # Build FAISS index
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    return index, all_chunks


def query_rag(question, api_key, k=5):
    """Run a RAG query: embed question, search FAISS, return context chunks."""
    index, chunks = build_rag_index(api_key, _version=2)
    if index is None or not chunks:
        return "I don't have enough context loaded to answer that question properly."

    # Embed the question
    query_vec = _get_query_embedding(question, api_key)

    # Search
    k = min(k, index.ntotal)
    distances, indices = index.search(query_vec, k)

    # Gather context
    context_parts = []
    for idx in indices[0]:
        if idx < len(chunks):
            context_parts.append(chunks[idx]["text"])

    return "\n\n---\n\n".join(context_parts)


def generate_response(question, context, api_key, chat_history=None):
    """Generate a response using Gemini with RAG context."""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")

    # Build the prompt with context
    prompt = f"""CONTEXT FROM MY PROFILE AND PROJECTS:
{context}

---

RECRUITER'S QUESTION: {question}

Respond as Rodel Agcaoili following the system instructions."""

    # Include chat history for continuity
    history_text = ""
    if chat_history:
        recent = chat_history[-6:]  # Last 3 exchanges
        for msg in recent:
            role = "Recruiter" if msg["role"] == "user" else "Rodel"
            history_text += f"{role}: {msg['content']}\n"

    if history_text:
        prompt = f"CONVERSATION HISTORY:\n{history_text}\n\n{prompt}"

    try:
        response = model.generate_content(
            f"{SYSTEM_PROMPT}\n\n{prompt}",
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=2048,
            )
        )
        
        if not response or not response.candidates:
            return "I'm sorry, I generated an empty response."

        text = response.text
        finish_reason = response.candidates[0].finish_reason
        
        # If it didn't finish normally, append a note for debugging
        if finish_reason != 1:  # 1 is STOP
            text += f"\n\n[Debug: Finish Reason: {finish_reason}]"
            
        return text
    except Exception as e:
        return f"I'm having trouble connecting right now. (Error: {str(e)})"


