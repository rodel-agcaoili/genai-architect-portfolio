import streamlit as st
import json
import os

# -------------------------------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------------------------------
st.set_page_config(
    page_title="Rodel Agcaoili — GenAI Architect Portfolio",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------------------------------------------------
# GLOBAL CSS
# -------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* Hero header */
    .hero {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        padding: 2.5rem 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        display: flex;
        align-items: center;
        gap: 2rem;
    }
    .hero-photo {
        width: 140px;
        height: 140px;
        border-radius: 50%;
        border: 3px solid #7c83ff;
        object-fit: cover;
        flex-shrink: 0;
    }
    .hero-text h1 {
        color: #e0e0ff;
        margin: 0;
        font-weight: 700;
        font-size: 2rem;
    }
    .hero-text .subtitle {
        color: #7c83ff;
        font-size: 1.1rem;
        font-weight: 500;
        margin: 0.3rem 0;
    }
    .hero-text .tagline {
        color: #a0a0d0;
        font-size: 0.9rem;
        margin: 0.5rem 0 0 0;
    }

    /* Contact links */
    .contact-links {
        display: flex;
        gap: 1rem;
        margin-top: 0.8rem;
    }
    .contact-links a {
        color: #7c83ff;
        text-decoration: none;
        font-size: 0.85rem;
        font-weight: 500;
        padding: 0.3rem 0.8rem;
        border: 1px solid #7c83ff;
        border-radius: 20px;
        transition: all 0.3s;
    }
    .contact-links a:hover {
        background: #7c83ff;
        color: #0a0a1a;
    }

    /* Section card */
    .section-card {
        background: linear-gradient(135deg, #111128, #161640);
        border: 1px solid #2a2a4a;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    .section-card h3 {
        color: #7c83ff;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin: 0 0 1rem 0;
    }

    /* Skill badge */
    .skill-badge {
        display: inline-block;
        background: rgba(124, 131, 255, 0.15);
        color: #b0b4ff;
        padding: 0.3rem 0.7rem;
        border-radius: 6px;
        font-size: 0.8rem;
        margin: 0.2rem;
        border: 1px solid rgba(124, 131, 255, 0.25);
    }

    /* Skill bar */
    .skill-category {
        color: #e0e0ff;
        font-weight: 600;
        font-size: 0.9rem;
        margin: 0.8rem 0 0.4rem 0;
    }

    /* About text */
    .about-text {
        color: #c0c0e0;
        font-size: 0.95rem;
        line-height: 1.7;
    }

    /* Sidebar */
    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0c29, #1a1a2e);
    }
    div[data-testid="stSidebar"] .stMarkdown h1,
    div[data-testid="stSidebar"] .stMarkdown h2,
    div[data-testid="stSidebar"] .stMarkdown h3 { color: #e0e0ff; }
    div[data-testid="stSidebar"] .stMarkdown p { color: #a0a0d0; }

    /* Metric card */
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border: 1px solid #2a2a4a;
        border-radius: 10px;
        padding: 1.2rem;
        margin: 0.5rem 0;
    }
    .metric-card h3 { color: #7c83ff; margin: 0 0 0.5rem 0; font-size: 0.9rem; }
    .metric-card .value { color: #e0e0ff; font-size: 1.8rem; font-weight: 700; }

    .status-pass { color: #4ade80; font-weight: 600; }
    .status-fail { color: #f87171; font-weight: 600; }
    .status-block { color: #fbbf24; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------------------
# SESSION STATE INIT
# -------------------------------------------------------------------------
if "aws_configured" not in st.session_state:
    st.session_state.aws_configured = False
if "aws_creds" not in st.session_state:
    st.session_state.aws_creds = {}

# -------------------------------------------------------------------------
# LOAD PROFILE DATA
# -------------------------------------------------------------------------
@st.cache_data
def load_profile():
    profile_path = os.path.join(os.path.dirname(__file__), "data", "profile_data.json")
    with open(profile_path, "r") as f:
        return json.load(f)

profile = load_profile()

# -------------------------------------------------------------------------
# SIDEBAR
# -------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## ⚡ Portfolio")
    st.markdown(f"*{profile['name']}*")
    st.divider()

    if st.session_state.aws_configured:
        st.success("🔗 AWS Lab: Connected")
    else:
        st.info("☁️ AWS Lab: Not Connected")

    st.divider()
    st.markdown("##### Quick Links")
    links = profile.get("links", {})
    if links.get("github"):
        st.markdown(f"[📂 GitHub Repo]({links['github']})")
    if links.get("linkedin") and not links["linkedin"].startswith("UPDATE"):
        st.markdown(f"[💼 LinkedIn]({links['linkedin']})")
    if links.get("email") and not links["email"].startswith("UPDATE"):
        st.markdown(f"[✉️ {links['email']}](mailto:{links['email']})")

# -------------------------------------------------------------------------
# PROFILE PAGE (HOME)
# -------------------------------------------------------------------------

# Hero Section
profile_pic_path = os.path.join(os.path.dirname(__file__), "assets", "profile.jpg")
has_photo = os.path.exists(profile_pic_path)

if has_photo:
    import base64
    with open(profile_pic_path, "rb") as f:
        photo_b64 = base64.b64encode(f.read()).decode()
    photo_html = f'<img src="data:image/jpeg;base64,{photo_b64}" class="hero-photo" alt="Profile Photo">'
else:
    photo_html = '<div class="hero-photo" style="background: #302b63; display: flex; align-items: center; justify-content: center; color: #7c83ff; font-size: 2.5rem;">RA</div>'

contact_html = '<div class="contact-links">'
if links.get("linkedin") and not links["linkedin"].startswith("UPDATE"):
    contact_html += f'<a href="{links["linkedin"]}" target="_blank">💼 LinkedIn</a>'
if links.get("email") and not links["email"].startswith("UPDATE"):
    contact_html += f'<a href="mailto:{links["email"]}">✉️ Email</a>'
if links.get("github"):
    contact_html += f'<a href="{links["github"]}" target="_blank">📂 GitHub</a>'
contact_html += '</div>'

st.markdown(f"""
<div class="hero">
    {photo_html}
    <div class="hero-text">
        <h1>{profile['name']}</h1>
        <div class="subtitle">{profile['title']}</div>
        <div class="tagline">{profile['tagline']}</div>
        {contact_html}
    </div>
</div>
""", unsafe_allow_html=True)

# -------------------------------------------------------------------------
# TECHNICAL CAPABILITIES ROADMAP
# -------------------------------------------------------------------------
st.markdown("""
<div style="background: linear-gradient(135deg, #1a1a3e, #2d2b6b); border: 1px solid #7c83ff; border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem;">
    <h3 style="color: #e0e0ff; margin-top: 0; display: flex; align-items: center; gap: 0.5rem;">
        🧭 Technical Capabilities Roadmap
    </h3>
    <p style="color: #c0c0e0; font-size: 0.95rem; line-height: 1.5;">
        This ecosystem demonstrates three distinct pillars of my engineering work. Select a pathway below to explore 
        live technical implementations in specific domains:
    </p>
</div>
""", unsafe_allow_html=True)

tour_cols = st.columns(3)

with tour_cols[0]:
    st.markdown("#### 🏗️ Cloud & Security")
    st.caption("Advanced infrastructure automation and security remediation.")
    st.markdown("*Focus: IaC, Automated Remediation, and Cloud Governance.*")
    st.page_link("pages/1_🚀_Projects.py", label="Explore Infrastructure Lab", icon="🚀")

with tour_cols[1]:
    st.markdown("#### 🤖 RAG & Conversational AI")
    st.caption("Expert systems powered by Retrieval Augmented Generation.")
    st.markdown("*Focus: Context-grounded chat and conversational UX for professional profiles.*")
    st.page_link("pages/2_💬_Ask_Rodel.py", label="Interact with AI Twin", icon="💬")

with tour_cols[2]:
    st.markdown("#### 🎯 AI Application Engineering")
    st.caption("End-to-end applications built for professional development.")
    st.markdown("*Focus: Complex multi-agent logic, voice integration, and data persistence.*")
    st.page_link("pages/4_🎯_Interview_Prep.py", label="View AI Practice Engine", icon="🎯")

st.markdown("<br>", unsafe_allow_html=True)

# About Section
st.markdown(f"""
<div class="section-card">
    <h3>About Me</h3>
    <div class="about-text">{profile['about']}</div>
</div>
""", unsafe_allow_html=True)

# Skills Section
st.markdown("---")
skills = profile.get("skills", {})
cols = st.columns(len(skills))
for col, (category, skill_list) in zip(cols, skills.items()):
    with col:
        badges = "".join(f'<span class="skill-badge">{s}</span>' for s in skill_list)
        st.markdown(f"""
        <div class="section-card">
            <h3>{category}</h3>
            {badges}
        </div>
        """, unsafe_allow_html=True)

# Projects Quick Overview
st.markdown("---")
st.markdown("### 🚀 Featured Projects")

projects = profile.get("projects_summary", [])
proj_cols = st.columns(len(projects))
for col, proj in zip(proj_cols, projects):
    with col:
        tech_badges = " ".join(f'<span class="skill-badge">{t}</span>' for t in proj.get("tech", [])[:3])
        st.markdown(f"""
        <div class="section-card" style="min-height: 200px;">
            <h3>Project {proj['number']}</h3>
            <div style="color: #e0e0ff; font-weight: 600; font-size: 0.95rem; margin-bottom: 0.3rem;">{proj['name']}</div>
            <div style="color: #a0a0d0; font-size: 0.8rem; margin-bottom: 0.8rem;">{proj['subtitle']}</div>
            {tech_badges}
        </div>
        """, unsafe_allow_html=True)

# Experience & Certifications
st.markdown("---")
exp_col, cert_col = st.columns(2)

with exp_col:
    st.markdown("### 💼 Experience")
    experience = profile.get("experience", [])
    for exp in experience:
        if exp.get("role", "").startswith("UPDATE"):
            st.info("📝 Update `portfolio/data/profile_data.json` with your work experience.")
            break
        st.markdown(f"""
        <div class="section-card">
            <div style="color: #e0e0ff; font-weight: 600;">{exp['role']}</div>
            <div style="color: #7c83ff; font-size: 0.85rem;">{exp['company']} • {exp['period']}</div>
        </div>
        """, unsafe_allow_html=True)
        for h in exp.get("highlights", []):
            st.markdown(f"- {h}")

with cert_col:
    st.markdown("### 🏆 Certifications")
    certs = profile.get("certifications", [])
    if certs and certs[0].startswith("UPDATE"):
        st.info("📝 Update `portfolio/data/profile_data.json` with your certifications.")
    else:
        for cert in certs:
            st.markdown(f"""
            <div class="section-card">
                <div style="color: #e0e0ff; font-weight: 500;">{cert}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("### 🎓 Education")
    education = profile.get("education", [])
    for edu in education:
        if edu.get("degree", "").startswith("UPDATE"):
            st.info("📝 Update `portfolio/data/profile_data.json` with your education.")
            break
        st.markdown(f"""
        <div class="section-card">
            <div style="color: #e0e0ff; font-weight: 500;">{edu['degree']}</div>
            <div style="color: #a0a0d0; font-size: 0.85rem;">{edu['school']} • {edu['year']}</div>
        </div>
        """, unsafe_allow_html=True)

# Architecture Overview
st.markdown("---")
st.markdown("### 🏗️ Architecture Overview")
arch_path = os.path.join(os.path.dirname(__file__), "assets", "architecture.png")
if os.path.exists(arch_path):
    st.image(arch_path, use_container_width=True)
else:
    st.info("Architecture diagram not found. Ensure `portfolio/assets/architecture.png` exists.")

# Footer
st.markdown("---")
st.markdown(
    '<div style="text-align: center; color: #606080; font-size: 0.8rem; padding: 1rem;">'
    f'Built by {profile["name"]} • Powered by Streamlit, AWS Bedrock & Gemini AI'
    '</div>',
    unsafe_allow_html=True
)
