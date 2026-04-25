import boto3
import json
import logging
from botocore.exceptions import ClientError

# -----------------------------------------------------------------------------------------
# "To ensure 'Security-by-Design', I architected the Lambda handler with clear Idempotency loops. 
# Instead of blindly executing PUT operations on every S3 bucket, the logic checks current 
# state first. This prevents unnecessary API throttling and provides deterministic outcomes. 
# Additionally, explicit ClientError handling ensures we log least-privilege KMS/IAM failures 
# gracefully without crashing the Bedrock Action Group loop."
# -----------------------------------------------------------------------------------------

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    logger.info(f"Received Bedrock Agent Action execution: {json.dumps(event)}")
    
    action_group = event.get('actionGroup')
    function = event.get('function')
    parameters = {p['name']: p['value'] for p in event.get('parameters', [])}
    
    result = ""

    try:
        # Route logic strictly based on parsed OpenAPI specs from Bedrock Action Group
        if function == "auditS3Buckets":
            result = audit_s3_buckets()
        
        elif function == "secureBucket":
            bucket_name = parameters.get('bucketName')
            if not bucket_name:
                raise ValueError("Missing bucketName parameter required for secureBucket function.")
            result = secure_s3_bucket(bucket_name)
        
        else:
            result = f"Error: Function {function} not recognized by Action Group {action_group}"

    except ClientError as e:
        logger.error(f"AWS API Error during {function}: {str(e)}")
        result = f"AWS API Error: {e.response['Error']['Code']} - {e.response['Error']['Message']}"
    except Exception as e:
        logger.error(f"Validation/System Error executing {function}: {str(e)}")
        result = f"Execution Error: {str(e)}"

    # Format the exact response envelope expected by the Bedrock Agent
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": action_group,
            "function": function,
            "functionResponse": {
                "responseBody": {
                    "TEXT": {
                        "body": json.dumps(result)
                    }
                }
            }
        }
    }

def audit_s3_buckets():
    """Identifies all buckets and analyzes their Public Access Block status."""
    buckets_response = s3_client.list_buckets()
    buckets = buckets_response.get('Buckets', [])
    audit_results = []
    
    for bucket in buckets:
        name = bucket['Name']
        try:
            pab_response = s3_client.get_public_access_block(Bucket=name)
            config = pab_response.get('PublicAccessBlockConfiguration', {})
            
            # Ensure it is STRICTLY secure
            if all(config.values()):
                status = "Secure Context Verified"
            else:
                status = "INSECURE - Partial Public Access Blocks"
                
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchPublicAccessBlockConfiguration':
                status = "INSECURE - Missing Public Access Block"
            else:
                status = f"AccessDenied / Error checking status: {e.response['Error']['Code']}"
        
        audit_results.append({"bucketName": name, "securityStatus": status})
    
    return audit_results

def secure_s3_bucket(bucket_name):
    """Applies high-security Public Access Block to a specific bucket idempotently."""
    
    # IDEMPOTENCY CHECK
    try:
        current_pab = s3_client.get_public_access_block(Bucket=bucket_name)
        config = current_pab.get('PublicAccessBlockConfiguration', {})
        if all(config.values()):
            return f"Bucket '{bucket_name}' is already secure. Idempotency loop bypassed update."
    except ClientError as e:
        if e.response['Error']['Code'] != 'NoSuchPublicAccessBlockConfiguration':
            raise e

    # Apply remediation
    s3_client.put_public_access_block(
        Bucket=bucket_name,
        PublicAccessBlockConfiguration={
            'BlockPublicAcls': True,
            'IgnorePublicAcls': True,
            'BlockPublicPolicy': True,
            'RestrictPublicBuckets': True
        }
    )
    
    return f"REMEDIATION SUCCESS: Successfully applied strict Public Access Block to {bucket_name}."
