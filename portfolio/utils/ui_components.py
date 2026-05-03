import streamlit as st
from typing import List, Dict, Any

def architect_view_trace(steps: List[Dict[str, Any]], title: str = "Architect's Trace View") -> None:
    """
    Renders a 'Staff-level' execution trace component for Bedrock/LangGraph Agents.
    
    Architectural 'Why': 
    In Enterprise GenAI systems, the 'Black Box' problem is a critical security risk. 
    Tracing is mandatory for audibility, debugging, and proving the agent's logic 
    to security stakeholders. This component visually exposes the internal reasoning 
    and routing decisions of the multi-agent state machine.
    
    Args:
        steps (List[Dict]): A list of trace steps. Each step dict should contain:
            - 'agent': Name of the agent/node (e.g., 'Triage Agent')
            - 'action': What the agent attempted to do
            - 'result': The output, reasoning, or routing decision
            - 'status': 'success', 'warning', or 'error' (affects color rendering)
        title (str): The header title for the trace section.
    """
    st.markdown(f"### 🔍 {title}")
    
    for i, step in enumerate(steps):
        status = step.get('status', 'success').lower()
        status_color = {
            'success': '#4ade80', # Pass - Green
            'warning': '#fbbf24', # Blocked/Escalated - Yellow
            'error': '#f87171'    # Failed - Red
        }.get(status, '#e0e0ff')
        
        # Staff-level UI styling for traces
        html_content = f"""
        <div style="
            border-left: 4px solid {status_color};
            background: linear-gradient(90deg, rgba(26,26,46,0.95), rgba(22,33,62,0.95));
            padding: 1.2rem 1.5rem;
            margin-bottom: 1rem;
            border-radius: 0 8px 8px 0;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            font-family: 'Inter', sans-serif;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem;">
                <span style="color: #7c83ff; font-weight: 700; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1.2px;">
                    Step {i+1} • {step.get('agent', 'System Node')}
                </span>
                <span style="color: {status_color}; font-size: 0.75rem; font-weight: 800; border: 1px solid {status_color}50; padding: 0.2rem 0.6rem; border-radius: 12px; background: {status_color}10;">
                    {status.upper()}
                </span>
            </div>
            <div style="color: #e0e0ff; font-size: 0.95rem; line-height: 1.5; margin-bottom: 0.6rem;">
                <span style="color: #a0a0d0; font-size: 0.85rem;">ACTION:</span><br/>
                {step.get('action', '')}
            </div>
            <div style="color: #c0c0e0; font-size: 0.95rem; line-height: 1.5; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 0.6rem;">
                <span style="color: #a0a0d0; font-size: 0.85rem;">REASONING / RESULT:</span><br/>
                <span style="font-family: monospace; font-size: 0.9rem; background: rgba(0,0,0,0.2); padding: 0.2rem 0.4rem; border-radius: 4px;">
                    {step.get('result', '')}
                </span>
            </div>
        </div>
        """
        st.markdown(html_content, unsafe_allow_html=True)
