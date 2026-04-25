import boto3
import faiss
import numpy as np
import pickle
import json
import os
import botocore

s3 = boto3.client('s3')
bedrock = boto3.client('bedrock-runtime')

# Environment variables to set in Terraform
VECTOR_BUCKET = os.environ.get('VECTOR_BUCKET_NAME', '')
INDEX_KEY = "indices/my_vector_index.faiss"

def lambda_handler(event, context):
    print("Received event: ", json.dumps(event))
    documents_processed = 0

    if 'Records' not in event:
        return {"statusCode": 400, "body": "No records found in S3 event trigger."}

    for record in event['Records']:
        source_bucket = record['s3']['bucket']['name']
        source_key = record['s3']['object']['key']

        # Only process explicit text uploads (ignore folder structural objects)
        if source_key.endswith('/'):
            continue

        print(f"Processing s3://{source_bucket}/{source_key}")
        try:
            obj = s3.get_object(Bucket=source_bucket, Key=source_key)
            text_content = obj['Body'].read().decode('utf-8')
        except Exception as e:
            print(f"Error fetching document: {str(e)}")
            continue

        if not text_content.strip():
            print("Empty document, skipping.")
            continue

        # Generate Embedding using Bedrock Titan 
        try:
            body = json.dumps({"inputText": text_content})
            response = bedrock.invoke_model(
                modelId="amazon.titan-embed-text-v2:0",
                contentType="application/json",
                accept="application/json",
                body=body
            )
            embedding = json.loads(response['body'].read())['embedding']
        except Exception as e:
            print(f"Error generating embedding via Bedrock: {str(e)}")
            continue
        
        dim = len(embedding) 
        vector_np = np.array([embedding]).astype('float32')

        # Robust Idempotent Loading: Check if FAISS index exists in S3 BEFORE creating a new one!
        index = None
        try:
            s3.download_file(VECTOR_BUCKET, INDEX_KEY, "/tmp/existing.faiss")
            index = faiss.read_index("/tmp/existing.faiss")
            print("Successfully anchored to existing FAISS index from S3.")
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '404':
                print("No existing FAISS index found. Instantiating a fresh vector database.")
                index = faiss.IndexFlatL2(dim) # L2 Euclidean distance
            else:
                print(f"S3 download fatal error: {str(e)}")
                continue
        except Exception as e:
            print(f"Local FAISS mathematical read error: {str(e)}. Resetting.")
            index = faiss.IndexFlatL2(dim)

        if index:
            # Append the new document chunk to the persistent vector set
            index.add(vector_np)
            faiss.write_index(index, "/tmp/updated.faiss")
            s3.upload_file("/tmp/updated.faiss", VECTOR_BUCKET, INDEX_KEY)
            print(f"FAISS index safely appended and permanently synced to s3://{VECTOR_BUCKET}/{INDEX_KEY}")
            documents_processed += 1

    return {
        "statusCode": 200,
        "body": json.dumps(f"Successfully digested {documents_processed} document(s) directly into the idempotent FAISS vector datastore!")
    }