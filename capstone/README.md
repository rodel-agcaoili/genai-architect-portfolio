# Capstone: Central Command Dashboard

A unified Streamlit orchestrator consolidating all 5 AWS Generative AI Architecture projects into a single interactive demo interface with live credential management.

## Quick Start

```bash
# 1. Install dependencies (one-time)
./.venv/bin/pip install -r capstone/requirements.txt

# 2. Launch the dashboard
./.venv/bin/streamlit run capstone/app.py
```

Open **http://localhost:8501** in your browser.

## Authentication

1. Navigate to **AWS Credentials** in the sidebar.
2. Paste your temporary ACloudGuru/Pluralsight lab credentials.
3. Click **Authenticate** — the dashboard validates via `sts.get_caller_identity()`.
4. The sidebar indicator will flip to **AWS: Connected**.

Credentials are stored exclusively in your local Python process memory. They are never persisted to disk or transmitted externally.

## Dashboard Pages

### Home
Portfolio overview with 5 project summary cards and a generated architecture diagram showing all projects connected through Amazon Bedrock.

### 1: Secure RAG
- **Upload & Ingest:** Paste document text, choose a filename, and upload directly to the S3 Data Landing Zone. The dashboard waits for Lambda ingestion and then queries the FAISS index byte size to prove vector compilation.
- **Query RAG:** Type a question and invoke the backend Query Lambda to generate a live RAG response.

### 2: SentinelAI
- **S3 Bucket Audit:** One-click scan of all S3 buckets in the account. Each bucket is labeled SECURE or VULNERABLE based on its Public Access Block configuration.
- **Remediate Bucket:** Enter a bucket name and instantly apply full Public Access Blocks.

### 3: Governance Shield
- Type any prompt into the text area.
- **Left panel (Outer Layer):** Shows the Regex PII scrubbing result. SSNs, Credit Cards, and internal project codenames are masked.
- **Right panel (Inner Layer):** Shows the LLM System Guardrail response. Prompt injection attacks and denied topics are blocked with `[BEDROCK GUARDRAIL EXECUTED] ACCESS DENIED`.

### 4: Incident Responder
- Select a preset server alert or type a custom one.
- Watch the LangGraph multi-agent state machine execute live with expandable status indicators:
  - **Triage Agent** classifies the incident as KNOWN or UNKNOWN.
  - **Runbook Agent** attempts a tool lookup. If it fails, it cyclically re-routes to Escalation.
  - **Escalation Agent** drafts a P1 Jira ticket using Bedrock.

### 5: Drift Evaluator
- **Preset Tests:** Run 3 synthetic RAG traces (Perfect, Hallucinated, Evasive) through the LLM-as-a-Judge pipeline.
- **Custom Evaluation:** Provide your own question, context, and answer to evaluate.
- Each test displays Faithfulness and Relevancy scores as Streamlit metrics, with an automated Quality Gate (PASSED / DRIFT DETECTED).

## Why Local-Only

| Factor | Local Streamlit | Cloud EC2 |
|--------|----------------|-----------|
| Startup | `streamlit run` — 3 seconds | Full EC2 + SG + deploy cycle |
| Credential Safety | Session memory only | Requires env vars on instance |
| Sandbox Volatility | Immune | Instance destroyed every 4 hours |
| Cost | $0 | EC2 hourly charges |

Running locally proves credential isolation discipline — secrets never leave your controlled environment.
