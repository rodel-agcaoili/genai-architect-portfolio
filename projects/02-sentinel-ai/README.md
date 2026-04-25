# Project 2: SentinelAI (The Action)

Welcome to the SentinelAI Agent project! This repository contains everything required to deploy a strict, least-privilege, and idempotent autonomous security loop using AWS Bedrock Agents.

## 🚀 The Principal's Narrative
> "I moved beyond context-retrieval chatbots to build a fully autonomous security loop. My agent interprets corporate security policies and translates them into explicitly defined OpenAPI workflows, orchestrating executable AWS SDK commands via Lambda. By implementing a strict Human-in-the-Loop (HITL) governance model and incorporating zero-trust idempotency, I fundamentally eliminated the risk of runaway API throttling or horizontal privilege escalation."

## 🛠️ Project Execution Playbook

This playbook walks you through spinning up the infrastructure, executing the pipelines, and running verification tests dynamically in an ephemeral sandbox environment (ACloudGuru, Pluralsight, etc).

### Step 1: Lab Environment Spin Up & Credential Sync
When you spin up a fresh temporary lab:
1. Obtain the `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` given by the provider. *(These are usually IAM keys `AKIA...` or STS keys `ASIA...` if accompanied by a session token).*
2. In your local terminal, navigate to the root of this portfolio repository.
3. Execute the sync script:
   ```bash
   ./scripts/update_github_secrets.sh
   ```
4. Paste the credentials exactly as prompted. The script will use the GitHub CLI to securely inject these directly into your GitHub Actions Repo Secrets (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and gracefully deletes the `AWS_SESSION_TOKEN` if you leave it blank).

### Step 2: Deploy Infrastructure via CI/CD
1. Navigate to **GitHub.com → Actions → Deploy SentinelAI Pipeline**.
2. Click **Run workflow** -> Select `main` -> Click **Run workflow**.
3. **What happens behind the scenes:**
   - The workflow uses `moto` to internally validate the Lambda execution logic virtually WITHOUT touching real AWS credentials (Zero-Cost Verification).
   - Once mocked tests pass, the pipeline downloads any previous Terraform state natively via GitHub Artifacts (protecting against mid-run runner crashes).
   - It executes `terraform apply -auto-approve` using the newly injected lab credentials.

### Step 3: Execute the Autonomous Loop
Because some sandbox environments intentionally block the managed `bedrock:InvokeAgent` API at the parent Organization level, we decoupled the architecture! We execute the exact same Action Group natively on the local terminal using the Bedrock Converse API to strictly simulate managed execution.
1. Clear ghost credentials and launch the orchestrator:
   ```bash
   unset AWS_SESSION_TOKEN
   ./.venv/bin/python projects/02-sentinel-ai/demo_agent.py
   ```
2. Command the LLM to trigger the internal OpenAPI audit schema: 
   **"Please audit my AWS account and find all insecure S3 buckets."**
3. Notice the `[⚙️ Action Group Engaged]` output? You are seeing Claude autonomously select the correct API endpoint and seamlessly pipe your intent into our custom `lambda_handler`.
4. Instruct the agent to fix the vulnerability: 
   **"Please secure the [bucket_name] bucket for me."**

### Step 4: Cryptographic Verification (Proof of Execution)
To prove the AI didn't just carelessly hallucinate a response, but tangibly invoked `boto3` AWS modification APIs under the hood, verify the bucket state directly on AWS!

```bash
# First, find the names of the buckets our Terraform auto-spawned:
aws s3api list-buckets --query "Buckets[?contains(Name, 'sentinel-insecure')].Name"

# Query the Public Access Block state of the bucket the agent just remediated:
# (If successful, the backend API will explicitly show that all 4 security locks are now true!)
aws s3api get-public-access-block --bucket <bucket-the-agent-remediated>
```

### ⚠️ Principal Architect Handling: SCP Limitations
If you run into an error stating:
```text
User: cloud_user is not authorized to perform: bedrock:InvokeAgent ... because no service control policy allows the bedrock:InvokeAgent action
```
**Architect's Diagnosis:** AWS Organizations construct strict Service Control Policies (SCPs) at the root level. When using specific Pluralsight/ACloudGuru sandboxes, the administrators implement hard-deny SCPs to block expensive experimental invocations (like Bedrock Agents). 
**Since SCPs override all identity policies:** No IAM role we create in Terraform can bypass this. This is a deliberate organizational governance guardrail enforced by the lab platform, proving that the infrastructure deployed successfully precisely to spec, but the overarching Organizational boundary blocked invocation!
