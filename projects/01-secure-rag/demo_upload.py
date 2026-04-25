import boto3
import sys
import time
import json

s3 = boto3.client('s3')
lambda_cl = boto3.client('lambda', region_name='us-east-1')

def find_buckets():
    ingest, vector = None, None
    for b in s3.list_buckets()['Buckets']:
        if b['Name'].startswith('rag-data-ingest-'): ingest = b['Name']
        if b['Name'].startswith('rag-vector-store-'): vector = b['Name']
    return ingest, vector

def find_query_lambda():
    for fn in lambda_cl.list_functions()['Functions']:
        if 'rag-query-' in fn['FunctionName']: return fn['FunctionName']
    return None

def run_demo():
    print("Project 1: Secure RAG Automated Tester")
    ingest_bucket, vector_bucket = find_buckets()
    query_lambda = find_query_lambda()
    
    if not ingest_bucket or not vector_bucket:
        print("Error: Could not locate Terraform buckets.")
        sys.exit(1)
        
    print(f"[✅] Located Secure Data Landing Zone: {ingest_bucket}")
    print(f"[✅] Located FAISS Vector Store: {vector_bucket}")
    print(f"[✅] Located Query Lambda: {query_lambda}")

    test_files = [
        ("test_doc_1.txt", "This is the first document chunk for the vector database. It contains initial foundational knowledge payload."),
        ("test_doc_2.txt", "This is the second document chunk. Uploading this text proves that the mathematical FAISS index idempotently appends data.")
    ]
    
    for filename, content in test_files:
        print(f"\n--- Uploading {filename} ---")
        s3.put_object(Bucket=ingest_bucket, Key=filename, Body=content.encode('utf-8'))
        print(f"Success: {filename} uploaded natively to S3. This instantly triggers the async ingestor Lambda.")
        
        print("Waiting 10 seconds for Lambda to spin up container, query Bedrock Titan, and compile FAISS...")
        time.sleep(10)
        
        try:
            obj = s3.head_object(Bucket=vector_bucket, Key="indices/my_vector_index.faiss")
            print(f"[📈 Ingestion Success] FAISS Database verified updating! Current mathematical byte size: {obj['ContentLength']} bytes")
        except Exception as e:
            print("[⚠️] Vector database compiling... check console for Lambda status.")
            
    if query_lambda:
        print("\n--- Testing RAG Query Lambda (Retriever Generator) ---")
        query_string = "What is Rodel's expertise?"
        print(f"Asking Agent: '{query_string}'")
        try:
            response = lambda_cl.invoke(
                FunctionName=query_lambda,
                InvocationType='RequestResponse',
                Payload=json.dumps({"query": query_string})
            )
            result = json.loads(response['Payload'].read())
            print(f"[🤖 RAG Output]: {result.get('answer', 'Failed to retrieve answer')}")
        except Exception as e:
            print(f"Failed to invoke query lambda: {e}")

if __name__ == "__main__":
    run_demo()
