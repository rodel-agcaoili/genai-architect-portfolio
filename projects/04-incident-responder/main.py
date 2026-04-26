from typing import TypedDict
from langgraph.graph import StateGraph, END
import json
import boto3

# 1. GRAPH STATE DEFINITION
# This TypedDict defines the explicit memory shared across all autonomous agents in the loop.
# This structure proves why LangGraph operates better than stateless step functions.
class IncidentState(TypedDict):
    incident: str
    route_decision: str
    resolution: str

# Helper to natively invoke Amazon Bedrock
def invoke_bedrock(prompt, system):
    bedrock = boto3.client('bedrock-runtime', region_name="us-east-1")
    try:
        response = bedrock.invoke_model(
            modelId="anthropic.claude-3-haiku-20240307-v1:0",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "system": system,
                "messages": [{"role": "user", "content": prompt}]
            })
        )
        return json.loads(response['body'].read())['content'][0]['text']
    except Exception as e:
        return f"ERROR: {str(e)}"

# -------------------------------------------------------------------------
# 2. AGENT DEFINITIONS (Nodes)
# -------------------------------------------------------------------------

def triage_agent(state: IncidentState):
    print("\n🤖 [Triage Agent]: Analyzing incident severity telemetry...")
    system = """You are an autonomous incident router. Read the user's server error. 
    If it is a predictable generic timeout, 500 error, or basic gateway failure, output exclusively the word: KNOWN. 
    If it is abstract, unique, undocumented, or mentions kernel panics/memory leaks, output exclusively the word: UNKNOWN."""
    
    decision = invoke_bedrock(state['incident'], system).strip().upper()
    
    # We strictly enforce the output string to control the graph state edge
    if "KNOWN" in decision:
        state['route_decision'] = "KNOWN"
    else:
        state['route_decision'] = "UNKNOWN"
        
    print(f"   -> Decision Matrix concluded: {state['route_decision']}")
    return state

def runbook_agent(state: IncidentState):
    print("📚 [Runbook Agent]: Executing VectorDB_Search tool across corporate databases...")
    
    # Simulating the action of hitting an organizational Vector Runbook
    if "KNOWN" in state['route_decision']:
        print("   -> Runbook Tool Found: 'Restart the Payment API ECS container via Terraform.'")
        state['resolution'] = "Issue mitigated automatically via Runbook automation."
        state['route_decision'] = "RESOLVED"
    else:
        print("   -> Runbook Tool Failed: 'No documentation found for this specific anomaly.'")
        print("   -> Initiating dynamic fallback routing...")
        state['route_decision'] = "ESCALATE"
        
    return state

def escalation_agent(state: IncidentState):
    print("🚨 [Escalation Agent]: Executing create_jira_ticket API tool...")
    system = """You are an automated Jira engineering bot. Draft a brief, 3-sentence P1 Jira Ticket detailing the user's incident. 
    Explicitly detail that the autonomous Runbook sweep was executed by the L1 Agents but completely failed."""
    
    ticket = invoke_bedrock(state['incident'], system)
    print(f"\n=============================================\n[JIRA TICKET DRAFTED]\n{ticket}\n=============================================\n")
    state['resolution'] = "Escalated to human engineering via Jira."
    return state

# -------------------------------------------------------------------------
# 3. MULTI-AGENT STATE GRAPH ORCHESTRATION (The Decoupled Routing)
# -------------------------------------------------------------------------

def route_from_triage(state: IncidentState):
    # Autonomous edge routing: The state machine decides where to branch based on Triage's LLM logic
    if state['route_decision'] == "KNOWN":
        return "runbook_agent"
    return "escalation_agent"

def route_from_runbook(state: IncidentState):
    # Cyclical fallback logic: If Runbook agent fails, it routes BACK down to Escalation
    if state['route_decision'] == "RESOLVED":
        return END
    return "escalation_agent"

print("Compiling Architecture: Python LangGraph Orchestrator (Bypassing AWS Step Functions)")
workflow = StateGraph(IncidentState)

# Binds the physical functions to the Graph Nodes
workflow.add_node("triage_agent", triage_agent)
workflow.add_node("runbook_agent", runbook_agent)
workflow.add_node("escalation_agent", escalation_agent)

# Binds the logical decision vectors
workflow.set_entry_point("triage_agent")
workflow.add_conditional_edges("triage_agent", route_from_triage)
workflow.add_conditional_edges("runbook_agent", route_from_runbook)
workflow.add_edge("escalation_agent", END)

# Finalizes the mathematical memory map into an execution application
app = workflow.compile()


def simulate_incident(incident_text):
    print(f"\n=============================================")
    print(f"🔥 INCOMING ALERT: {incident_text}")
    print(f"=============================================")
    # Fire the LangGraph pipeline
    app.invoke({"incident": incident_text, "route_decision": "", "resolution": ""})


if __name__ == "__main__":
    # Test 1: Simple known issue (Triaged -> Runbook search succeeds -> Terminate cleanly)
    simulate_incident("HTTP 503 Timeout on the US-East Payment Gateway Container. Expected traffic spike.")
    
    # Test 2: Unrecognized severe issue (Triaged -> Pivot directly to Jira Escalate OR Runbook fails -> Jira Escalate)
    simulate_incident("Unrecognized kernel panic memory leak at Node 9 corrupting massive disk structures.")
