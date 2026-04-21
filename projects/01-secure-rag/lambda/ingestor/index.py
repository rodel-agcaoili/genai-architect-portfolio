import boto3
import faiss
import numpy as np
import pickle
import json
import os

s3 = boto3.client('s3')
bedrock = boto3.client('bedrock-runtime')

# Environment variables to set in Terraform
VECTOR_BUCKET = os.environ['VECTOR_BUCKET_NAME']
INDEX_KEY = "indices/my_vector_index.faiss"
METADATA_KEY = "indices/metadata.pkl"

def lambda_handler(event, context):
    # Sample Text (Will come from 'event')
    text_content = "Hawaii No Ka Oi! Rodel specializing in AI Infrastructure."

    # Generate Embedding
    body = json.dumps({"inputText": text_content})
    response = bedrock.invoke_model(
        modelId="amazon.titan-embed-text-v2:0",
        contentType="application/json",
        accept="application/json",
        body=body
    )
    embedding = json.loads(response['body'].read())['embedding']
    
    # Initialize or Load FAISS Index
    # Convert the list to a numpy array for FAISS
    dim = len(embedding) 
    vector_np = np.array([embedding]).astype('float32')
    index = faiss.IndexFlatL2(dim) # L2 is Euclidean distance
    index.add(vector_np)

    # Save index to S3
    # Save the index to a temporary local file first
    faiss.write_index(index, "/tmp/index.faiss")
    
    # Upload to S3
    s3.upload_file("/tmp/index.faiss", VECTOR_BUCKET, INDEX_KEY)
    
    return {
        "statusCode": 200,
        "body": json.dumps("Vector index successfully updated and stored in S3!")
    }
    