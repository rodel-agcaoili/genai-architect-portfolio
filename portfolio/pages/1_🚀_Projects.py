import streamlit as st
import json
import os
import sys

# Add portfolio root to path for utils imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.demo_mode import (
    run_demo_secure_rag,
    run_demo_sentinel_ai,
    run_demo_governance_shield,
    run_demo_incident_responder,
    run_demo_drift_evaluator,
)

# -------------------------------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------------------------------
st.set_page_config(
    page_title="Projects — Rodel Agcaoili",
    page_icon="🚀",
    layout="wide"
)

# -------------------------------------------------------------------------
# LOAD DATA
# -------------------------------------------------------------------------
@st.cache_data
def load_profile():
    profile_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "profile_data.json")
    with open(profile_path, "r") as f:
        return json.load(f)

profile = load_profile()
projects = profile.get("projects_summary", [])
repo_url = profile.get("links", {}).get("github", "#")

# -------------------------------------------------------------------------
# HEADER
# -------------------------------------------------------------------------
st.markdown("""
<div style="background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); padding: 2rem; border-radius: 12px; margin-bottom: 2rem; text-align: center;">
    <h1 style="color: #e0e0ff; margin: 0; font-weight: 700;">🚀 Project Portfolio</h1>
    <p style="color: #a0a0d0; margin: 0.5rem 0 0 0;">5 AWS GenAI Architecture Projects — Interactive Demos & Source Code</p>
</div>
""", unsafe_allow_html=True)

# Mode selector
st.markdown("""
> **💡 Demo Mode** shows pre-recorded realistic outputs so you can experience each project without AWS credentials.
> Switch to the **🔧 Live Lab** page to run projects against a real AWS account.
""")

st.divider()

# -------------------------------------------------------------------------
# PROJECT CARDS
# -------------------------------------------------------------------------
for proj in projects:
    with st.container():
        # Project header
        col_title, col_links = st.columns([3, 1])
        with col_title:
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 0.5rem;">
                <div style="background: linear-gradient(135deg, #7c83ff, #5b5fbf); color: white; font-weight: 700;
                    width: 36px; height: 36px; border-radius: 8px; display: flex; align-items: center;
                    justify-content: center; font-size: 1.1rem; flex-shrink: 0;">{proj['number']}</div>
                <div>
                    <div style="color: #e0e0ff; font-weight: 700; font-size: 1.3rem;">{proj['name']}</div>
                    <div style="color: #7c83ff; font-size: 0.9rem;">{proj['subtitle']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col_links:
            st.markdown(
                f'<a href="{repo_url}/tree/main/{proj["github_path"]}" target="_blank" '
                f'style="color: #7c83ff; text-decoration: none; font-size: 0.85rem; border: 1px solid #7c83ff; '
                f'padding: 0.3rem 0.8rem; border-radius: 20px;">📂 View Source Code</a>',
                unsafe_allow_html=True
            )

        # Tech badges
        tech_html = " ".join(
            f'<span style="display:inline-block; background: rgba(124,131,255,0.15); color: #b0b4ff; '
            f'padding: 0.25rem 0.6rem; border-radius: 5px; font-size: 0.75rem; margin: 0.15rem; '
            f'border: 1px solid rgba(124,131,255,0.25);">{t}</span>'
            for t in proj.get("tech", [])
        )
        st.markdown(tech_html, unsafe_allow_html=True)

        # JD Alignment
        if "jd_alignment" in proj:
            st.markdown(
                f'<div style="margin-top: 0.5rem; display: flex; align-items: center; gap: 0.5rem;">'
                f'<span style="background: linear-gradient(90deg, #4ade80, #34d399); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 700; font-size: 0.8rem;">🎯 SIE JD ALIGNMENT:</span>'
                f'<span style="color: #e0e0ff; font-weight: 600; font-size: 0.85rem; border-bottom: 1px dashed #4ade80;">{proj["jd_alignment"]}</span>'
                f'</div>',
                unsafe_allow_html=True
            )

        # Description
        st.markdown(f'<p style="color: #c0c0e0; font-size: 0.9rem; line-height: 1.6; margin: 0.8rem 0;">{proj["description"]}</p>', unsafe_allow_html=True)

        # Architecture image (for projects that have one)
        assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
        if proj["id"] == "secure-rag" or proj["number"] == 1:
            arch = os.path.join(assets_dir, "architecture.png")
            if os.path.exists(arch):
                with st.expander("🏗️ Architecture Diagram"):
                    st.image(arch, use_container_width=True)
        elif proj["id"] == "incident-responder" or proj["number"] == 4:
            lg = os.path.join(assets_dir, "langgraph.png")
            if os.path.exists(lg):
                with st.expander("🏗️ LangGraph State Machine Diagram"):
                    st.image(lg, use_container_width=True)

        # Demo section
        with st.expander(f"▶ Interactive Demo — {proj['name']}", expanded=False):
            if proj["id"] == "secure-rag":
                tab1, tab2 = st.tabs(["Upload & Vectorize", "Query RAG"])
                with tab1:
                    run_demo_secure_rag(mode="upload")
                with tab2:
                    run_demo_secure_rag(mode="query")

            elif proj["id"] == "sentinel-ai":
                run_demo_sentinel_ai()

            elif proj["id"] == "governance-shield":
                run_demo_governance_shield()

            elif proj["id"] == "incident-responder":
                run_demo_incident_responder()

            elif proj["id"] == "drift-evaluator":
                run_demo_drift_evaluator()

        st.divider()

# Footer
st.markdown(
    '<div style="text-align: center; color: #606080; font-size: 0.8rem; padding: 1rem;">'
    f'All projects use Terraform for IaC • Full source code at <a href="{repo_url}" style="color: #7c83ff;">{repo_url}</a>'
    '</div>',
    unsafe_allow_html=True
)
