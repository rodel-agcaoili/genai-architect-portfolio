# Project 1: Secure FAISS RAG Pipeline

This project demonstrates a fully serverless, highly secure Retrieval-Augmented Generation (RAG) ingestion pipeline using AWS Bedrock (Titan Embeddings), AWS Lambda, and an isolated S3 landing zone. The architecture explicitly handles dynamic scaling by enforcing idempotent FAISS database updates.

## Technical Architecture
When a user or system drops a text file into the internal Data Landing Zone bucket, it natively triggers the Ingestion Lambda. The Lambda downloads the file, calls AWS Bedrock to mathematically convert the text into floating-point vectors, and anchors those vectors into an authoritative FAISS index.

### Key Features Designed for Enterprise Realities:
*   **Idempotent Vector Insertion:** The architecture natively downloads any existing pre-compiled FAISS databases before appending new data, ensuring no knowledge payload is destructively overwritten.
*   **Strict Ephemeral Sandboxing:** The pipeline explicitly hooks into GitHub Actions Artifacts to natively map Terraform states across workflow runs. It utilizes a `fresh_lab` trigger override to circumvent State contamination when completely changing AWS accounts.
*   **Decoupled S3 Design:** Separates the unparsed raw document ingestion bucket from the strict compiled index delivery bucket.

## Project Playbook

### Step 1: Environment Hydration
Ensure your temporary local AWS credentials are securely ported to your GitHub Actions by running the central sync script:
```bash
./scripts/update_github_secrets.sh
```

### Step 2: Infrastructure Pipeline
Navigate to GitHub Actions, locate the "Hydrate AWS Portfolio" workflow, and selectively deploy it using the Run workflow toggle.
*Note: If you have migrated to a completely fresh ephemeral Sandbox, check the Fresh Lab Mode box to firmly reset the internal runner state.*

### Step 3: Run the Ingestion Demo
To explicitly test the autonomous ingestion, trigger the custom Python testing script:
```bash
unset AWS_SESSION_TOKEN
./.venv/bin/python projects/01-secure-rag/demo_upload.py
```

### Step 4: Verification
The python script will automatically locate your deployed S3 landing zone, physically upload two independent text documents in sequential order, and inherently trigger the Lambda orchestrator twice.

To definitively verify success mechanically, execute the following AWS CLI commands to ensure the `my_vector_index.faiss` database expanded natively without overwriting:
```bash
# Locate your vector store bucket
aws s3api list-buckets --query "Buckets[?starts_with(Name, 'rag-vector-store-')].Name"

# List the size of the compiled index to confirm mathematical byte expansion
aws s3api list-objects-v2 --bucket <your-vector-bucket-name> --prefix "indices/my_vector_index.faiss" --query "Contents[].Size"
```
