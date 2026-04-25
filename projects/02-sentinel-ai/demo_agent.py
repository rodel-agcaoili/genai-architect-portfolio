import boto3
import json
import sys
import os

# Ensure the lambda logic is accessible without breaking paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'lambda', 'agent')))
import remediator

bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

# -----------------------------------------------------------------------------------------
# PRINCIPAL's NARRATIVE (Workaround):
# "When my ACloudGuru Lab environment SCP blocked 'bedrock:InvokeAgent', I didn't abandon 
# the architecture. Instead, I decoupled the orchestration layer. I utilized the 
# Bedrock Converse API to manually bind the OpenAPI Tool specification directly to Claude 3.7. 
# This simulated the managed Bedrock Agent locally in Python, routing the AI's tool decisions 
# natively back into our Action Group Lambda, seamlessly bypassing the sandbox constraint."
# -----------------------------------------------------------------------------------------

# Define the tools exactly as they are in the OpenAPI schema
tool_config = {
    "tools": [
        {
            "toolSpec": {
                "name": "auditS3Buckets",
                "description": "Lists all S3 buckets and their public access status.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {}
                    }
                }
            }
        },
        {
            "toolSpec": {
                "name": "secureBucket",
                "description": "Enables strict Block Public Access constraints on a specific S3 bucket.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "bucketName": {
                                "type": "string",
                                "description": "The exact name of the S3 bucket to secure."
                            }
                        },
                        "required": ["bucketName"]
                    }
                }
            }
        }
    ]
}

def execute_tool(tool_name, tool_input):
    """Bridges the Converse API Tool Request directly into our Lambda Remediator payload"""
    print(f"\n[⚙️ Action Group Engaged] Executing: {tool_name} with params: {tool_input}")
    
    # Map to the format our remediator lambda expects from Bedrock Action Groups
    parameters = [{"name": k, "value": v} for k, v in tool_input.items()]
    
    mock_event = {
        "messageVersion": "1.0",
        "actionGroup": "S3SecurityActionGroup",
        "function": tool_name,
        "parameters": parameters
    }
    
    class MockContext: pass
    
    response = remediator.lambda_handler(mock_event, MockContext())
    # Extract the TEXT result from our lambda's highly nested response envelope
    result_str = json.loads(
        response['response']['functionResponse']['responseBody']['TEXT']['body']
    )
    return result_str

def run_agent():
    print("🤖 SentinelAI Local Orchestrator Initialize. Type 'exit' to quit.")
    
    # Store conversation history
    messages = []
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == 'exit':
            break
            
        messages.append({"role": "user", "content": [{"text": user_input}]})
        
        try:
            print("\n[🧠 Thinking...]")
            response = bedrock.converse(
                modelId="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
                messages=messages,
                toolConfig=tool_config
            )
            
            output_message = response['output']['message']
            messages.append(output_message)
            
            # Check if Claude decided to use a tool
            for content_block in output_message['content']:
                if 'text' in content_block:
                    print(f"SentinelAI: {content_block['text']}")
                    
                if 'toolUse' in content_block:
                    tool_use = content_block['toolUse']
                    tool_name = tool_use['name']
                    tool_input = tool_use['input']
                    tool_id = tool_use['toolUseId']
                    
                    # Execute local lambda bypass logic
                    tool_result = execute_tool(tool_name, tool_input)
                    print(f"[✅ Action Group Result]: {tool_result}")
                    
                    # Pass the tool result back into Claude so it can answer the user
                    messages.append({
                        "role": "user",
                        "content": [
                            {
                                "toolResult": {
                                    "toolUseId": tool_id,
                                    "content": [{"json": {"result": tool_result}}]
                                }
                            }
                        ]
                    })
                    
                    print("\n[🧠 Analyzing Action Results...]")
                    final_response = bedrock.converse(
                        modelId="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
                        messages=messages,
                        toolConfig=tool_config
                    )
                    
                    final_msg = final_response['output']['message']
                    messages.append(final_msg)
                    for block in final_msg['content']:
                        if 'text' in block:
                            print(f"SentinelAI: {block['text']}")

        except Exception as e:
            print(f"Error communicating with Bedrock Converse: {e}")

if __name__ == "__main__":
    run_agent()
