import boto3
import faiss
import numpy as np
import json
import os

s3 = boto3.client('s3')
bedrock = boto3.client('bedrock-runtime')

# Environment Variables
VECTOR_BUCKET = os.environ['VECTOR_BUCKET_NAME']
INDEX_KEY = "indices/my_vector_index.faiss"
MODEL_ID = "anthropic.claude-3-7-sonnet-20250219-v1:0"


def lambda_handler(event, context):
    # Extract Query
    user_query = event.get('query', 'What does Rodel do?')
    
    # Embed the Query
    # Must use the SAME model used during ingestion for mathematical alignment
    body = json.dumps({"inputText": user_query})
    embed_response = bedrock.invoke_model(
        modelId="amazon.titan-embed-text-v2:0",
        body=body
    )
    query_vector = json.loads(embed_response['body'].read())['embedding']
    
    # Load Index from S3 into /tmp
    if not os.path.exists("/tmp/index.faiss"):
        s3.download_file(VECTOR_BUCKET, INDEX_KEY, "/tmp/index.faiss")
    
    index = faiss.read_index("/tmp/index.faiss")
    
    # Search for Context
    k = 3 # Retrieve top 3 most relevant "chunks"
    distances, indices = index.search(np.array([query_vector]).astype('float32'), k)
    
    # For now, let's assume a static context to demonstrate the 'Augmentation'
    mock_context = "Rodel Agcaoili is a Senior Cloud Engineer and AI Infrastructure expert."

    # Augmented Generation - The RAG Prompt
    system_prompt = "You are a helpful AI assistant. Use the provided context to answer questions. If the answer isn't in the context, say you don't know."
    
    prompt = f"""
    Context: {mock_context}
    
    Question: {user_query}
    
    Answer:"""

    response = bedrock.invoke_model(
        modelId=MODEL_ID,
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 512,
            "messages": [{"role": "user", "content": prompt}],
            "system": system_prompt
        })
    )
    
    result = json.loads(response['body'].read())
    
    return {
        "statusCode": 200,
        "answer": result['content'][0]['text']
    }
