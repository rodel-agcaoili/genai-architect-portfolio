# Project 3: The Governance Shield

This project implements a Defense-in-Depth architectural strategy for Generative AI applications. It natively blocks malicious prompts, filters highly toxic responses, and mathematically scrubs Personally Identifiable Information (PII) before the payload ever reaches an external AI provider.

## Technical Architecture

The Governance Shield is built using two distinct boundaries:
1.  **Outer Boundary (Custom Lambda Proxy):** A serverless Python interceptor that leverages deterministic Regex logic to explicitly mask SSNs, Credit Cards, and proprietary internal code names (`Project Zeus`). This represents a zero-latency, strict compliance safety net that acts completely independent of external APIs.
2.  **Inner Boundary (Amazon Bedrock Guardrails):** A native AWS cloud configuration deeply tied to the foundational model. It evaluates parsed text for Prompt Injections, toxicity, and explicitly denied semantic topics (such as `InternalFinancials`).

### Key Differentiator
While Bedrock Guardrails natively supports PII Masking, this project purposefully separates the two boundaries. In highly secure enterprise environments (such as Defense or Financial sectors), compliance teams strictly require that raw PII never leaves the isolated corporate VPC boundary. By engineering a custom Regex Lambda, we guarantee data sovereignty prior to external invocation.

## Project Playbook

### Step 1: Automated Pipeline Deployment
Deploy the Terraform infrastructure instantly by executing the dedicated CI/CD pipeline directly via GitHub Actions:
```bash
gh workflow run governance-shield-ci.yml --ref main
```

### Step 2: Testing the Shield
Once deployed, run the local `demo_shield.py` script. The script is designed to bypass standard CLI tooling and natively invoke the backend Serverless proxy using four distinct payload attacks:
1. A Clean Baseline Query
2. A PII Exfiltration Attempt (SSNs and Internal Codes)
3. A Topic Deny-List Evasion (Corporate Financials)
4. A Direct Prompt Injection Attack

```bash
unset AWS_SESSION_TOKEN
./.venv/bin/python projects/03-governance-shield/demo_shield.py
```

### Step 3: Analysis
During execution, physically observe the mathematical stripping of the Social Security Numbers `[REDACTED SSN]` handled locally by the Python wrapper vs the `ValidationException` blocking explicitly handled by the native AWS Guardrail. This definitively proves the separation of security tier contexts!
