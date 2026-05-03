"""
SentinelAI S3 Auditing MCP Server
Follows 2026 Anthropic Model Context Protocol (MCP) Standards.

Why:
Integrating security tools via MCP decouples the Agent from the infrastructure API.
Instead of giving an LLM direct AWS keys or complex Lambda architectures, we expose 
atomic, tightly scoped tools via FastMCP. This creates a zero-trust boundary where 
the agent can only perform explicitly permitted actions.
"""

from typing import Dict, Any, List
from mcp.server.fastmcp import FastMCP
import boto3
from botocore.exceptions import ClientError

# Initialize FastMCP Server
# FastMCP handles all the JSON-RPC boilerplate and transport layers standard in 2026.
mcp = FastMCP("SentinelAI S3 Auditor")

def get_s3_client():
    """Helper to get boto3 client (assumes IAM role or environment credentials are set)."""
    return boto3.client("s3")

@mcp.tool()
def list_buckets() -> List[str]:
    """
    Lists all S3 buckets in the AWS account.
    Returns: A list of bucket names.
    """
    try:
        s3 = get_s3_client()
        response = s3.list_buckets()
        return [bucket["Name"] for bucket in response.get("Buckets", [])]
    except ClientError as e:
        return [f"Error listing buckets: {str(e)}"]

@mcp.tool()
def check_bucket_security(bucket_name: str) -> Dict[str, Any]:
    """
    Checks if an S3 bucket has AWS PublicAccessBlock configuration fully enabled.
    This is a critical CNAPP/CSPM posture check.
    
    Args:
        bucket_name (str): The name of the S3 bucket to audit.
        
    Returns:
        Dict: Status of the PublicAccessBlock configuration.
    """
    try:
        s3 = get_s3_client()
        response = s3.get_public_access_block(Bucket=bucket_name)
        config = response.get("PublicAccessBlockConfiguration", {})
        
        # All 4 properties must be True for the bucket to be considered fully secure
        is_secure = (
            config.get("BlockPublicAcls", False) and
            config.get("IgnorePublicAcls", False) and
            config.get("BlockPublicPolicy", False) and
            config.get("RestrictPublicBuckets", False)
        )
        
        return {
            "bucket": bucket_name,
            "status": "SECURE" if is_secure else "VULNERABLE",
            "configuration": config
        }
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchPublicAccessBlockConfiguration':
            return {
                "bucket": bucket_name,
                "status": "VULNERABLE",
                "reason": "No PublicAccessBlock configuration exists."
            }
        return {"error": str(e)}

@mcp.tool()
def remediate_bucket(bucket_name: str) -> str:
    """
    Applies strict PublicAccessBlock configuration to an S3 bucket.
    Acts as the automated remediation step in the SOAR pipeline.
    
    Args:
        bucket_name (str): The name of the S3 bucket to remediate.
        
    Returns:
        str: Success or error message.
    """
    try:
        s3 = get_s3_client()
        s3.put_public_access_block(
            Bucket=bucket_name,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': True,
                'IgnorePublicAcls': True,
                'BlockPublicPolicy': True,
                'RestrictPublicBuckets': True
            }
        )
        return f"Successfully remediated {bucket_name}. Public access is now fully blocked."
    except ClientError as e:
        return f"Failed to remediate {bucket_name}: {str(e)}"

if __name__ == "__main__":
    # Runs the server using the standard stdio transport for MCP
    # Interviewers can test this locally by pointing an MCP-compatible client at this script.
    mcp.run()
