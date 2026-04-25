import json
from lambda_agent import remediator

# A synthetic event mimicking the Bedrock Action Group invocation
mock_event = {
    "messageVersion": "1.0",
    "actionGroup": "S3SecurityActionGroup",
    "function": "auditS3Buckets",
    "parameters": []
}

class MockContext:
    pass

print("=== Running Synthetic Test for auditS3Buckets ===")
try:
    response = remediator.lambda_handler(mock_event, MockContext())
    print("Response JSON Envelope:")
    print(json.dumps(response, indent=2))
except Exception as e:
    print(f"Failed: {e}")
