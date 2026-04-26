import json
import boto3

bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

# -------------------------------------------------------------------------
# JUDGE MODEL CONFIGURATION
# We use Claude 3 Haiku: low-cost, high-speed, deterministic grader.
# -------------------------------------------------------------------------

def invoke_judge(system_prompt, user_prompt):
    try:
        response = bedrock.invoke_model(
            modelId="anthropic.claude-3-haiku-20240307-v1:0",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 500,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}]
            })
        )
        return json.loads(response['body'].read())['content'][0]['text']
    except Exception as e:
        return f"ERROR: {str(e)}"

# -------------------------------------------------------------------------
# METRIC 1: FAITHFULNESS (Hallucination Detection)
# -------------------------------------------------------------------------

def evaluate_faithfulness(context, answer):
    system = """You are a strict MLOps Faithfulness Evaluator. 
    Given a [SOURCE CONTEXT] and a [GENERATED ANSWER], determine if every claim in the answer 
    is strictly derivable from the source context. 
    
    Respond ONLY with valid JSON in this exact format:
    {"score": <float 0.0 to 1.0>, "reasoning": "<one sentence explanation>"}
    
    Rules:
    - 1.0 = Every claim in the answer is directly supported by the context.
    - 0.5 = Some claims are supported, but some are fabricated or unverifiable.
    - 0.0 = The answer contains mostly hallucinated information not in the context."""
    
    user = f"[SOURCE CONTEXT]: {context}\n\n[GENERATED ANSWER]: {answer}"
    return invoke_judge(system, user)

# -------------------------------------------------------------------------
# METRIC 2: ANSWER RELEVANCY
# -------------------------------------------------------------------------

def evaluate_relevancy(question, answer):
    system = """You are a strict MLOps Relevancy Evaluator.
    Given a [USER QUESTION] and a [GENERATED ANSWER], determine if the answer directly
    and completely addresses what the user asked.
    
    Respond ONLY with valid JSON in this exact format:
    {"score": <float 0.0 to 1.0>, "reasoning": "<one sentence explanation>"}
    
    Rules:
    - 1.0 = The answer directly and completely addresses the question.
    - 0.5 = The answer partially addresses the question but includes irrelevant tangents.
    - 0.0 = The answer completely avoids or fails to address the question."""
    
    user = f"[USER QUESTION]: {question}\n\n[GENERATED ANSWER]: {answer}"
    return invoke_judge(system, user)

# -------------------------------------------------------------------------
# SYNTHETIC RAG TEST PAYLOADS
# -------------------------------------------------------------------------

TEST_CASES = [
    {
        "name": "Perfect RAG Output",
        "question": "What is Amazon Bedrock?",
        "context": "Amazon Bedrock is a fully managed service that offers leading foundation models from AI companies like Anthropic, Meta, and Amazon via a single API.",
        "answer": "Amazon Bedrock is a fully managed AWS service providing access to foundation models from companies like Anthropic, Meta, and Amazon through a unified API."
    },
    {
        "name": "Hallucinated RAG Output",
        "question": "What is Amazon Bedrock?",
        "context": "Amazon Bedrock is a fully managed service that offers leading foundation models from AI companies like Anthropic, Meta, and Amazon via a single API.",
        "answer": "Amazon Bedrock is an open-source container orchestration platform similar to Kubernetes that was acquired by Google in 2019 for $4.7 billion."
    },
    {
        "name": "Evasive / Irrelevant RAG Output",
        "question": "What is Amazon Bedrock?",
        "context": "Amazon Bedrock is a fully managed service that offers leading foundation models from AI companies like Anthropic, Meta, and Amazon via a single API.",
        "answer": "That's a great question! I think the weather today is quite nice. Have you considered trying a new restaurant for lunch?"
    }
]

# -------------------------------------------------------------------------
# EXECUTION PIPELINE
# -------------------------------------------------------------------------

def run_eval():
    print("Project 5: The Drift Evaluator (MLOps)")
    print("Native LLM-as-a-Judge Pipeline (RAGAS-equivalent, zero framework dependencies)")
    print("Judge Model: Claude 3 Haiku | Target: Synthetic RAG traces\n")
    
    for i, test in enumerate(TEST_CASES, 1):
        print(f"{'='*60}")
        print(f"[EVAL {i}]: {test['name']}")
        print(f"{'='*60}")
        print(f"  Question: {test['question']}")
        print(f"  Context:  {test['context'][:80]}...")
        print(f"  Answer:   {test['answer'][:80]}...")
        
        # Run both evaluation dimensions
        faith_raw = evaluate_faithfulness(test['context'], test['answer'])
        relev_raw = evaluate_relevancy(test['question'], test['answer'])
        
        # Parse JSON scores
        try:
            faith = json.loads(faith_raw)
            relev = json.loads(relev_raw)
        except json.JSONDecodeError:
            faith = {"score": "PARSE_ERROR", "reasoning": faith_raw}
            relev = {"score": "PARSE_ERROR", "reasoning": relev_raw}
        
        print(f"\n  [Faithfulness Score]: {faith.get('score', 'N/A')}")
        print(f"    Reasoning: {faith.get('reasoning', 'N/A')}")
        print(f"  [Relevancy Score]:   {relev.get('score', 'N/A')}")
        print(f"    Reasoning: {relev.get('reasoning', 'N/A')}")
        
        # Quality Gate simulation
        f_score = faith.get('score', 0)
        r_score = relev.get('score', 0)
        if isinstance(f_score, (int, float)) and isinstance(r_score, (int, float)):
            if f_score >= 0.8 and r_score >= 0.8:
                print(f"  [QUALITY GATE]: PASSED")
            else:
                print(f"  [QUALITY GATE]: FAILED (Drift Detected)")
        else:
            print(f"  [QUALITY GATE]: MANUAL REVIEW REQUIRED")
        print()

if __name__ == "__main__":
    run_eval()
