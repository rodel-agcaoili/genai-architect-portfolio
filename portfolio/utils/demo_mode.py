"""
Demo Mode Engine — serves pre-baked responses for all 5 projects
so recruiters can experience the full portfolio without AWS credentials.
"""
import json
import time
import os
import streamlit as st


@st.cache_data
def load_demo_data():
    """Load demo responses from JSON file."""
    data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "demo_responses.json")
    with open(data_path, "r") as f:
        return json.load(f)


def simulate_delay(seconds=1.0):
    """Simulate processing time for demo realism."""
    time.sleep(seconds)


def run_demo_secure_rag(mode="upload"):
    """Render demo for Project 1: Secure RAG Pipeline."""
    data = load_demo_data()["secure_rag"]

    if mode == "upload":
        st.markdown("#### Demo: Document Upload & Vectorization")
        doc_text = st.text_area(
            "Document Content (demo)",
            value="Rodel Agcaoili is a Senior Cloud Engineer and AI Infrastructure expert specializing in AWS Bedrock, Terraform, and GenAI security architectures.",
            height=100,
            key="demo_rag_doc"
        )
        if st.button("▶ Run Upload Demo", key="demo_rag_upload_btn"):
            for step in data["upload"]["steps"]:
                with st.spinner(step["label"]):
                    simulate_delay(step["delay"])
                st.success(f"**{step['label']}** — {step['message']}")

            metrics = data["upload"]["metrics"]
            c1, c2, c3 = st.columns(3)
            c1.metric("Document Size", metrics["doc_size"])
            c2.metric("Embedding Dims", metrics["embedding_dims"])
            c3.metric("Total Vectors", metrics["total_vectors"])

    elif mode == "query":
        st.markdown("#### Demo: RAG Query")
        query = st.text_input("Ask a question", value=data["query"]["question"], key="demo_rag_query")
        if st.button("▶ Run Query Demo", key="demo_rag_query_btn"):
            with st.spinner("Embedding query via Bedrock Titan..."):
                simulate_delay(1.0)
            st.caption(data["query"]["context_note"])
            with st.spinner("Generating RAG response via Bedrock Claude..."):
                simulate_delay(1.5)
            st.markdown(f"**RAG Response:**\n\n{data['query']['answer']}")


def run_demo_sentinel_ai():
    """Render demo for Project 2: SentinelAI."""
    data = load_demo_data()["sentinel_ai"]

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### S3 Bucket Audit")
        if st.button("▶ Run Audit Demo", key="demo_sentinel_audit"):
            with st.spinner("Scanning buckets..."):
                simulate_delay(1.5)
            for bucket in data["audit"]["buckets"]:
                if bucket["has_public_access_block"]:
                    st.markdown(f'`{bucket["name"]}` — <span style="color: #4ade80; font-weight: 600;">SECURE</span>', unsafe_allow_html=True)
                else:
                    st.markdown(f'`{bucket["name"]}` — <span style="color: #f87171; font-weight: 600;">{bucket["status"]}</span>', unsafe_allow_html=True)
            s = data["audit"]["summary"]
            st.markdown(f"**Summary:** {s['secure']} secure, {s['vulnerable']} vulnerable out of {s['total']} total")

    with col2:
        st.markdown("#### Remediate Bucket")
        if st.button("▶ Run Remediation Demo", key="demo_sentinel_remediate"):
            with st.spinner(f"Applying security block to `{data['remediate']['bucket']}`..."):
                simulate_delay(1.5)
            st.success(f"Remediated `{data['remediate']['bucket']}`!")
            st.code(data["remediate"]["result"], language="text")


def run_demo_governance_shield():
    """Render demo for Project 3: Governance Shield."""
    data = load_demo_data()["governance_shield"]

    scenario = st.selectbox("Select test scenario:", [
        "Clean Input (should PASS both layers)",
        "PII + Denied Topic (SSN + Project Zeus + Q3 Revenue)",
        "Prompt Injection Attack"
    ], key="demo_gov_scenario")

    scenario_map = {
        "Clean Input (should PASS both layers)": "clean_input",
        "PII + Denied Topic (SSN + Project Zeus + Q3 Revenue)": "pii_input",
        "Prompt Injection Attack": "injection_input"
    }
    case = data[scenario_map[scenario]]

    st.text_area("Input Prompt", value=case["input"], height=80, disabled=True, key="demo_gov_input")

    if st.button("▶ Submit to Shield Demo", key="demo_gov_btn"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Outer Layer (Regex PII)")
            with st.spinner("Scanning for PII patterns..."):
                simulate_delay(0.8)
            if case["outer_layer"]["pii_detected"]:
                st.warning("⚠️ PII Detected and Scrubbed!")
            else:
                st.success("✅ No PII Detected")
            st.code(case["outer_layer"]["scrubbed"])

        with col2:
            st.markdown("#### Inner Layer (LLM Guardrail)")
            with st.spinner("Evaluating through Bedrock Guardrails..."):
                simulate_delay(1.5)
            if case["inner_layer"]["blocked"]:
                st.error("🛑 BLOCKED BY GUARDRAIL")
                st.code(case["inner_layer"]["response"])
            else:
                st.success("✅ PASSED")
                st.markdown(case["inner_layer"]["response"])


def run_demo_incident_responder():
    """Render demo for Project 4: Incident Responder."""
    data = load_demo_data()["incident_responder"]

    scenario = st.selectbox("Select incident:", [
        "HTTP 503 Timeout → Triage → Runbook → Resolved",
        "Kernel Panic → Triage → Runbook (fail) → Escalation → Jira"
    ], key="demo_incident_scenario")

    case = data["known_incident"] if "503" in scenario else data["unknown_incident"]
    st.text_area("Alert", value=case["alert"], height=60, disabled=True, key="demo_incident_alert")

    if st.button("▶ Fire Alert Demo", key="demo_incident_btn"):
        st.markdown("---")
        st.markdown("### Agent Execution Trace")
        for step in case["trace"]:
            is_error = step.get("decision") == "ESCALATE" or "Failed" in step.get("result", "")
            state = "error" if is_error else "complete"
            label = f"{step['agent']}: {step.get('decision', 'Done')}" if step.get("decision") else step["agent"]

            with st.status(f"{step['agent']} executing...", expanded=True) as status:
                st.write(step["action"])
                simulate_delay(step["delay"])
                if "result" in step:
                    if is_error:
                        st.warning(step["result"])
                    else:
                        st.success(step["result"])
                if step.get("decision"):
                    color = "color: #4ade80" if step["decision"] in ("KNOWN", "RESOLVED") else "color: #f87171"
                    st.markdown(f'Decision: <span style="{color}; font-weight: 600;">{step["decision"]}</span>', unsafe_allow_html=True)
                status.update(label=label, state=state)


def run_demo_drift_evaluator():
    """Render demo for Project 5: Drift Evaluator."""
    data = load_demo_data()["drift_evaluator"]

    if st.button("▶ Run Evaluation Pipeline Demo", key="demo_drift_btn"):
        for i, test in enumerate(data["test_cases"], 1):
            st.markdown(f"### Eval {i}: {test['name']}")
            with st.expander("View Test Payload", expanded=True):
                st.markdown(f"**Question:** {test['question']}")
                st.markdown(f"**Source Context:** {test['context']}")
                st.markdown(f"**Generated Answer:** {test['answer']}")

            with st.spinner(f"Judge evaluating: {test['name']}..."):
                simulate_delay(1.5)

            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Faithfulness", test["faithfulness"]["score"])
                st.caption(test["faithfulness"]["reasoning"])
            with c2:
                st.metric("Relevancy", test["relevancy"]["score"])
                st.caption(test["relevancy"]["reasoning"])
            with c3:
                if test["gate"] == "PASSED":
                    st.markdown(
                        '<div style="background: linear-gradient(135deg, #1a1a2e, #16213e); border: 1px solid #2a2a4a; border-radius: 10px; padding: 1.2rem; text-align: center;">'
                        '<h4 style="color: #7c83ff; margin: 0;">Quality Gate</h4>'
                        '<div style="color: #4ade80; font-size: 1.5rem; font-weight: 700;">PASSED</div></div>',
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        '<div style="background: linear-gradient(135deg, #1a1a2e, #16213e); border: 1px solid #2a2a4a; border-radius: 10px; padding: 1.2rem; text-align: center;">'
                        '<h4 style="color: #7c83ff; margin: 0;">Quality Gate</h4>'
                        '<div style="color: #f87171; font-size: 1.5rem; font-weight: 700;">DRIFT DETECTED</div></div>',
                        unsafe_allow_html=True
                    )
            st.divider()
