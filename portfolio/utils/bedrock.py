"""
Shared Amazon Bedrock helper functions for the Live Lab.
Handles credential management via Streamlit session state.
"""
import json
import boto3
import streamlit as st


def get_creds_kwargs():
    """Return explicit credential kwargs for boto3 clients from session state."""
    c = st.session_state.get("aws_creds", {})
    if not c:
        return {"region_name": "us-east-1"}
    kwargs = {
        "region_name": "us-east-1",
        "aws_access_key_id": c.get("access_key"),
        "aws_secret_access_key": c.get("secret_key"),
    }
    if c.get("session_token"):
        kwargs["aws_session_token"] = c["session_token"]
    return kwargs


def get_bedrock_client():
    """Create a Bedrock Runtime client with session credentials."""
    return boto3.client("bedrock-runtime", **get_creds_kwargs())


def get_s3_client():
    """Create an S3 client with session credentials."""
    return boto3.client("s3", **get_creds_kwargs())


def get_sts_client():
    """Create an STS client with session credentials."""
    return boto3.client("sts", **get_creds_kwargs())


def invoke_bedrock(prompt, system, model="anthropic.claude-3-haiku-20240307-v1:0"):
    """Invoke a Bedrock model with the given prompt and system instruction."""
    try:
        client = get_bedrock_client()
        response = client.invoke_model(
            modelId=model,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "system": system,
                "messages": [{"role": "user", "content": prompt}]
            })
        )
        return json.loads(response["body"].read())["content"][0]["text"]
    except Exception as e:
        return f"ERROR: {str(e)}"


def is_aws_configured():
    """Check if AWS credentials are set in session state."""
    return st.session_state.get("aws_configured", False)
