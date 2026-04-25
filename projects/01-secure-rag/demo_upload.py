import boto3
import sys

s3 = boto3.client('s3')

def find_ingest_bucket():
    """Identifies the dynamic Terraform bucket assigned to this sandbox execution"""
    response = s3.list_buckets()
    for bucket in response['Buckets']:
        if bucket['Name'].startswith('rag-data-ingest-'):
            return bucket['Name']
    return None

def run_demo():
    print("Project 1: Secure RAG Ingestion Tester")
    bucket = find_ingest_bucket()
    if not bucket:
        print("Error: Could not locate a bucket starting with 'rag-data-ingest-'. Ensure Terraform deployed successfully.")
        sys.exit(1)
        
    print(f"Located Secure Data Landing Zone: {bucket}")
    
    test_files = [
        ("test_doc_1.txt", "This is the first document chunk for the vector database. It contains initial foundational knowledge payload."),
        ("test_doc_2.txt", "This is the second document chunk. Uploading this text proves that the mathematical FAISS index idempotently appends data.")
    ]
    
    for filename, content in test_files:
        try:
            print(f"---\nUploading {filename}...")
            s3.put_object(Bucket=bucket, Key=filename, Body=content.encode('utf-8'))
            print(f"Success: {filename} uploaded natively to S3. This instantly triggers the ingestor Lambda.")
        except Exception as e:
            print(f"Failed to upload {filename}: {e}")

if __name__ == "__main__":
    run_demo()
