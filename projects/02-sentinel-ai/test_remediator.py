import sys
import os
import json
import boto3
from moto import mock_aws

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'lambda', 'agent')))
import remediator

@mock_aws
def test_audit_s3_buckets():
    print("=== Running Mocked Test for auditS3Buckets ===")
    
    # Set up mock S3 environment
    s3 = boto3.client('s3', region_name='us-east-1')
    s3.create_bucket(Bucket='test-insecure-bucket')
    
    s3.create_bucket(Bucket='test-secure-bucket')
    s3.put_public_access_block(
        Bucket='test-secure-bucket',
        PublicAccessBlockConfiguration={
            'BlockPublicAcls': True,
            'IgnorePublicAcls': True,
            'BlockPublicPolicy': True,
            'RestrictPublicBuckets': True
        }
    )

    mock_event = {
        "messageVersion": "1.0",
        "actionGroup": "S3SecurityActionGroup",
        "function": "auditS3Buckets",
        "parameters": []
    }

    class MockContext:
        pass

    # Note: re-initialize the s3 client inside the remediator to hook into Moto
    remediator.s3_client = boto3.client('s3', region_name='us-east-1')
    
    response = remediator.lambda_handler(mock_event, MockContext())
    print("Audit Response JSON Envelope:")
    print(json.dumps(response, indent=2))

if __name__ == "__main__":
    test_audit_s3_buckets()
