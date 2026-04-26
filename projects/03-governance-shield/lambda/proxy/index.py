import json
import re
import boto3
import os

bedrock = boto3.client('bedrock-runtime', region_name=os.getenv('AWS_REGION', 'us-east-1'))

# OUTER LAYER: Custom Python Regex Patterns
# Provides zero-latency deterministic PII masking before hitting external APIs.
PII_PATTERNS = {
    "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
    "CREDIT_CARD": r"\b(?:\d[ -]*?){13,16}\b",
    "INTERNAL_PROJECT": r"\b(Project\s*Zeus|Apollo\s*V2|Titanium\s*Core)\b"
}

def scrub_pii(text):
    scrubbed_text = text
    for pii_type, pattern in PII_PATTERNS.items():
        scrubbed_text = re.sub(pattern, f"[REDACTED {pii_type}]", scrubbed_text, flags=re.IGNORECASE)
    return scrubbed_text

def lambda_handler(event, context):
    prompt = event.get('prompt', '')
    
    if not prompt:
        return {"statusCode": 400, "body": "Missing 'prompt' in request payload."}

    # 1. OUTTER SHIELD: Native Python Regex Scrubbing
    anonymized_prompt = scrub_pii(prompt)
    print(f"Original Prompt Length: {len(prompt)}")
    print(f"Scrubbed Payload: {anonymized_prompt}")

    # 2. INNER SHIELD: Amazon Bedrock Guardrail Context
    guardrail_id = os.environ.get('GUARDRAIL_ID', '')
    guardrail_version = os.environ.get('GUARDRAIL_VERSION', 'DRAFT')
    
    try:
        response = bedrock.invoke_model(
            modelId="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": anonymized_prompt}]
            }),
            # Binding the AWS Guardrail directly to the LLM interaction
            guardrailIdentifier=guardrail_id,
            guardrailVersion=guardrail_version,
            trace="ENABLED" # Emits verbose Trace events allowing us to see Block interventions
        )
        
        result = json.loads(response['body'].read())
        return {
            "statusCode": 200,
            "scrubbed_prompt": anonymized_prompt,
            "model_response": result['content'][0]['text']
        }
    except boto3.client('bedrock-runtime').exceptions.ValidationException as e:
        # If the Bedrock Guardrail explicitly intercepts and denies the payload
        return {
            "statusCode": 403,
            "guardrail_intercept": "BLOCKED",
            "error_detail": str(e)
        }
    except Exception as e:
        # Handle access denieds or other errors
        if "AccessDeniedException" in str(e):
            return {
                "statusCode": 403,
                "guardrail_intercept": "BLOCKED", 
                "error_detail": "Bedrock Guardrail Intercepted Payload."
            }
        return {
            "statusCode": 500,
            "error_detail": str(e)
        }
