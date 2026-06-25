import streamlit as st
import requests
import pandas as pd

# Define Local Backend URL
BACKEND_URL = "http://localhost:8000"

def get_backend_status():
    """Checks if the local FastAPI backend is active and reachable."""
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=0.5)
        return response.status_code == 200
    except Exception:
        return False

# Mock data dictionary for Simulation Mode (Fallback for public hosted site)
MOCK_TELEMETRY = {
    "192.168.1.15": {
        "source_ip": "192.168.1.15",
        "failed_login_attempts_30m": 12,
        "outbound_bytes_transferred_1h": 209715200,  # 200 MB
        "unique_iam_roles_assumed_5m": 1,
        "risk_score": 0.90,
        "status": "CRITICAL: Immediate Investigation Required",
        "inference_type": "Simulation Mode (Local Backend Offline)"
    },
    "203.0.113.50": {
        "source_ip": "203.0.113.50",
        "failed_login_attempts_30m": 1,
        "outbound_bytes_transferred_1h": 2147483648,  # 2 GB
        "unique_iam_roles_assumed_5m": 0,
        "risk_score": 0.85,
        "status": "CRITICAL: Immediate Investigation Required",
        "inference_type": "Simulation Mode (Local Backend Offline)"
    },
    "10.0.2.14": {
        "source_ip": "10.0.2.14",
        "failed_login_attempts_30m": 0,
        "outbound_bytes_transferred_1h": 5242880,  # 5 MB
        "unique_iam_roles_assumed_5m": 4,
        "risk_score": 0.65,
        "status": "WARNING: Anomalous Behavior Detected",
        "inference_type": "Simulation Mode (Local Backend Offline)"
    },
    "192.168.1.99": {
        "source_ip": "192.168.1.99",
        "failed_login_attempts_30m": 0,
        "outbound_bytes_transferred_1h": 10240,  # 10 KB
        "unique_iam_roles_assumed_5m": 0,
        "risk_score": 0.75,
        "status": "CRITICAL: Immediate Investigation Required",
        "inference_type": "Simulation Mode (Local Backend Offline)"
    },
    "10.0.0.5": {
        "source_ip": "10.0.0.5",
        "failed_login_attempts_30m": 0,
        "outbound_bytes_transferred_1h": 1024,
        "unique_iam_roles_assumed_5m": 0,
        "risk_score": 0.05,
        "status": "BENIGN: Normal Operations",
        "inference_type": "Simulation Mode (Local Backend Offline)"
    }
}

MOCK_LOGS = [
    {"score": 0.9421, "log": "Brute force SSH attack detected on admin account from IP 192.168.1.15", "source_ip": "192.168.1.15", "severity": "HIGH", "timestamp": "2026-06-25T00:00:00Z"},
    {"score": 0.9654, "log": "Data exfiltration: Outbound connection established to external IP 203.0.113.50 transferring 2GB of sensitive customer data", "source_ip": "203.0.113.50", "severity": "CRITICAL", "timestamp": "2026-06-25T00:00:00Z"},
    {"score": 0.8841, "log": "IAM Role escalation: User svc-billing assumed Admin privileges without MFA", "source_ip": "10.0.2.14", "severity": "HIGH", "timestamp": "2026-06-25T00:00:00Z"},
    {"score": 0.5412, "log": "Normal HTTP GET request to /index.html from IP 10.0.0.5", "source_ip": "10.0.0.5", "severity": "INFO", "timestamp": "2026-06-25T00:00:00Z"},
    {"score": 0.9242, "log": "SQL injection attempt detected in query parameter: 'SELECT * FROM users;'", "source_ip": "192.168.1.99", "severity": "CRITICAL", "timestamp": "2026-06-25T00:00:00Z"},
    {"score": 0.7123, "log": "Successful SSH login on admin account from corporate VPN IP 10.0.5.50", "source_ip": "10.0.5.50", "severity": "INFO", "timestamp": "2026-06-25T00:00:00Z"},
    {"score": 0.8242, "log": "Port scanning activity detected from IP 192.168.1.15 scanning ports 22, 80, 443, 8080", "source_ip": "192.168.1.15", "severity": "MEDIUM", "timestamp": "2026-06-25T00:00:00Z"}
]

def simulate_search(query: str, severity: str = None):
    query = query.lower()
    results = []
    for log in MOCK_LOGS:
        match = False
        if "exfiltr" in query or "transfer" in query or "data" in query:
            if "exfiltration" in log["log"].lower() or "data" in log["log"].lower():
                match = True
        elif "ssh" in query or "login" in query or "brute" in query:
            if "ssh" in log["log"].lower() or "login" in log["log"].lower():
                match = True
        elif "role" in query or "escal" in query or "iam" in query:
            if "role" in log["log"].lower() or "escalation" in log["log"].lower():
                match = True
        elif "sql" in query or "inject" in query:
            if "sql" in log["log"].lower() or "injection" in log["log"].lower():
                match = True
        elif "scan" in query or "port" in query:
            if "scanning" in log["log"].lower() or "ports" in log["log"].lower():
                match = True
        else:
            if any(word in log["log"].lower() for word in query.split()):
                match = True
        
        if match:
            if not severity or severity == "All" or log["severity"] == severity:
                results.append(log)
                
    results = sorted(results, key=lambda x: x["score"], reverse=True)
    if not results:
        # Default fallback if no query match
        results = [l for l in MOCK_LOGS if not severity or severity == "All" or l["severity"] == severity][:2]
    return results

def render_secops_mlops_page():
    st.set_page_config(page_title="SecOps-MLOps Pipeline", page_icon="🛡️", layout="wide")
    
    # 1. Executive Summary & Status
    st.title("🛡️ SecOps-MLOps: Real-Time Telemetry Feature Store & Semantic Search")
    
    # Check if backend is alive
    is_live = get_backend_status()
    
    if is_live:
        st.success("🟢 Connected to Live Local Backend (FastAPI + Feast + Redis + Qdrant)")
    else:
        st.info("🔵 Demonstration Mode: Running offline simulation. (Start the local backend API to activate live lookups)")

    st.markdown("""
    **Executive Summary:**  
    This project bridges the gap between high-velocity security telemetry and machine learning by implementing a decoupled, real-time feature store architecture. By combining **Feast** backed by **Redis** for sub-millisecond serving, and **Qdrant** for semantic anomaly search, this pipeline eradicates training-serving skew while enabling automated, high-fidelity threat hunting at enterprise scale.
    """)
    
    st.divider()

    # 2. Architectural Flow Diagram
    st.subheader("Architecture Topology")
    import streamlit.components.v1 as components
    components.html("""
        <div class="mermaid" style="display: flex; justify-content: center; width: 100%; margin-top: 20px;">
            graph TD
                A[Raw Security Logs<br/>CloudTrail, VPC Flows] -->|Streaming| B(PySpark/Flink Processing)
                B -->|Aggregated Metrics| C[(Feast Store<br/>Redis + S3)]
                B -->|Embeddings| D[(Qdrant Vector DB)]
                
                C -->|Feature Vector| E{FastAPI Inference}
                D -->|Semantic Context| E
                E -->|Threat Score| F[SecOps Dashboard]
                
                classDef default fill:#111128,stroke:#7c83ff,stroke-width:2px,color:#e0e0ff;
                classDef db fill:#302b63,stroke:#7c83ff,stroke-width:2px,color:#fff;
                class C,D db;
        </div>
        <script type="module">
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
            mermaid.initialize({ startOnLoad: true, theme: 'dark' });
        </script>
    """, height=380)
    
    st.divider()

    # 3. Interactive Demo Console
    st.subheader("🔮 Live Interactive Operational Command Center")
    st.markdown("Test the telemetry lookup and semantic search functions below. If you run the project locally on your laptop, this panel connects to your active Redis and Qdrant instances.")

    demo_col1, demo_col2 = st.columns(2)

    with demo_col1:
        st.markdown("### 🖥️ Threat Vector Analysis (Feast + ML)")
        st.write("Retrieve real-time features from Redis and predict threat anomalies using the Isolation Forest model.")
        
        target_ip = st.selectbox(
            "Select Source IP to Analyze:",
            options=["192.168.1.15", "203.0.113.50", "10.0.2.14", "192.168.1.99", "10.0.0.5"],
            index=0
        )
        
        if st.button("Evaluate Threat Level", use_container_width=True):
            if is_live:
                try:
                    response = requests.post(f"{BACKEND_URL}/predict_threat/{target_ip}", timeout=2.0)
                    if response.status_code == 200:
                        data = response.json()
                        inference_type = data.get("inference_type", "Live ML Model")
                    else:
                        st.error(f"Backend API error ({response.status_code}). Falling back to simulation.")
                        data = MOCK_TELEMETRY.get(target_ip)
                        inference_type = "Fallback Simulation (API Error)"
                except Exception as e:
                    st.error(f"Failed to query backend: {e}")
                    data = MOCK_TELEMETRY.get(target_ip)
                    inference_type = "Fallback Simulation"
            else:
                data = MOCK_TELEMETRY.get(target_ip)
                inference_type = data["inference_type"]

            # Visual output of predictions
            st.markdown(f"**Inference engine:** `{inference_type}`")
            
            # Metric Columns
            m_col1, m_col2, m_col3 = st.columns(3)
            m_col1.metric("Failed Logins (30m)", f"{data['failed_login_attempts_30m']}")
            
            # Format Bytes
            mb_transferred = round(data['outbound_bytes_transferred_1h'] / (1024*1024), 2)
            m_col2.metric("Outbound Data (1h)", f"{mb_transferred} MB")
            
            m_col3.metric("IAM Roles Assumed (5m)", f"{data['unique_iam_roles_assumed_5m']}")

            # Threat Alert Card
            risk = data['risk_score']
            st.metric("Model Calculated Risk Score", f"{int(risk * 100)}%", delta=f"{'+' if risk > 0.5 else ''}{int(risk * 100) - 50}%")
            
            if "CRITICAL" in data['status']:
                st.error(f"🚨 {data['status']}")
            elif "WARNING" in data['status']:
                st.warning(f"⚠️ {data['status']}")
            else:
                st.success(f"✅ {data['status']}")

    with demo_col2:
        st.markdown("### 🔎 Threat Intelligence Semantic Search (Qdrant)")
        st.write("Search unstructured logs by semantic meaning using dense vector representations and payload filters.")
        
        search_query = st.text_input("Enter Search Term:", value="data exfiltration attempts", placeholder="e.g. brute force ssh")
        
        sev_filter = st.selectbox("Payload Severity Filter:", options=["All", "CRITICAL", "HIGH", "MEDIUM", "INFO"], index=0)
        
        if st.button("Scan Vector Store", use_container_width=True):
            if is_live:
                try:
                    params = {"query": search_query}
                    if sev_filter != "All":
                        params["severity"] = sev_filter
                    response = requests.get(f"{BACKEND_URL}/search_logs", params=params, timeout=2.0)
                    if response.status_code == 200:
                        results = response.json()
                        search_mode = "Live Qdrant Cluster"
                    else:
                        st.error(f"Search API error ({response.status_code}). Falling back to simulation.")
                        results = simulate_search(search_query, sev_filter)
                        search_mode = "Fallback Simulation (API Error)"
                except Exception as e:
                    st.error(f"Search failed: {e}")
                    results = simulate_search(search_query, sev_filter)
                    search_mode = "Fallback Simulation"
            else:
                results = simulate_search(search_query, sev_filter)
                search_mode = "Simulation Mode (Local Qdrant Offline)"

            st.markdown(f"**Index Search Source:** `{search_mode}`")
            
            for res in results:
                # Format each log result inside a nice display container
                score_pct = int(res['score'] * 100)
                
                # Determine colors based on severity
                sev_color = "red" if res['severity'] == "CRITICAL" else "orange" if res['severity'] == "HIGH" else "yellow" if res['severity'] == "MEDIUM" else "blue"
                
                st.markdown(f"""
                <div style="border: 1px solid #302b63; border-radius: 8px; padding: 12px; margin-bottom: 10px; background-color: #111128;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: bold; color: #7c83ff;">Match Score: {score_pct}%</span>
                        <span style="background-color: {sev_color}; color: black; font-size: 0.8rem; padding: 2px 6px; border-radius: 4px; font-weight: bold;">{res['severity']}</span>
                    </div>
                    <p style="margin: 8px 0; font-size: 0.95rem; color: #e0e0ff;">"{res['log']}"</p>
                    <div style="font-size: 0.8rem; color: #a0a0d0;">
                        <span>IP Address: <code>{res['source_ip']}</code></span> | <span>Timestamp: {res['timestamp'][:19]}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    st.divider()

    # 4. Implementation Details (Tabs)
    st.subheader("Implementation Details & Core Logic")
    
    tab1, tab2, tab3 = st.tabs(["Feast FeatureView", "FastAPI serving", "Qdrant Vector Storage"])
    
    with tab1:
        st.markdown("**Defining the Telemetry Feature View (`features.py`)**")
        st.code("""
from feast import Entity, FeatureView, Field, FileSource
from feast.types import Int64, Float32
from datetime import timedelta

# Define the data source
telemetry_source = FileSource(
    path="data/aggregated_metrics.parquet",
    timestamp_field="event_timestamp",
    created_timestamp_column="created_timestamp"
)

# Define the entity (Primary Key)
source_ip = Entity(name="source_ip", join_keys=["source_ip"])

# Define the Feature View
telemetry_fv = FeatureView(
    name="ip_telemetry_features",
    entities=[source_ip],
    ttl=timedelta(days=1),
    schema=[
        Field(name="failed_login_attempts_30m", dtype=Int64),
        Field(name="outbound_bytes_transferred_1h", dtype=Int64),
        Field(name="unique_iam_roles_assumed_5m", dtype=Int64),
    ],
    online=True,
    source=telemetry_source,
    tags={"domain": "security", "team": "secops"}
)
        """, language="python")

    with tab2:
        st.markdown("**Real-Time Threat Inference Endpoint (`main.py`)**")
        st.code("""
from fastapi import FastAPI, HTTPException
from feast import FeatureStore
import joblib

app = FastAPI(title="SecOps Inference Service")
store = FeatureStore(repo_path=".")
model = joblib.load("model.joblib")  # Loads Isolation Forest Model

@app.post("/predict_threat/{source_ip}")
async def predict_threat(source_ip: str):
    try:
        # 1. Fetch real-time features from Redis
        feature_vector = store.get_online_features(
            features=[
                "ip_telemetry_features:failed_login_attempts_30m",
                "ip_telemetry_features:outbound_bytes_transferred_1h",
                "ip_telemetry_features:unique_iam_roles_assumed_5m"
            ],
            entity_rows=[{"source_ip": source_ip}]
        ).to_dict()

        # Extract values
        failed_logins = feature_vector["failed_login_attempts_30m"][0] or 0
        outbound_bytes = feature_vector["outbound_bytes_transferred_1h"][0] or 0
        iam_roles = feature_vector["unique_iam_roles_assumed_5m"][0] or 0

        # 2. Run ML Model Prediction
        X = [[failed_logins, outbound_bytes, iam_roles]]
        prediction = model.predict(X)[0] # -1 is Anomaly, 1 is Normal
        raw_score = model.score_samples(X)[0]
        
        return {
            "source_ip": source_ip,
            "risk_score": float(abs(raw_score)),
            "status": "CRITICAL" if prediction == -1 else "BENIGN"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        """, language="python")

    with tab3:
        st.markdown("**Semantic Vector Search for Anomalies (`qdrant_service.py`)**")
        st.code("""
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

client = QdrantClient("localhost", port=6333)
model = SentenceTransformer('all-MiniLM-L6-v2')

# Initialize Collection
client.create_collection(
    collection_name="security_logs",
    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
)

def semantic_search(query_text: str, severity_filter: str = None):
    # Convert unstructured security log into semantic vector
    query_vector = model.encode(query_text).tolist()
    
    # Filter builder for payload
    query_filter = None
    if severity_filter:
        query_filter = Filter(must=[FieldCondition(key="severity", match=MatchValue(value=severity_filter))])

    # Search Qdrant with filter
    return client.search(
        collection_name="security_logs",
        query_vector=query_vector,
        query_filter=query_filter,
        limit=3
    )
        """, language="python")

    st.divider()

    # 5. Call to Action
    st.subheader("Source Code & Deployment")
    st.markdown("The complete infrastructure-as-code, pipeline logic, and container configurations are available in my repository.")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.link_button("🔗 View Project on GitHub", "https://github.com/rodel-agcaoili/genai-architect-portfolio/tree/main/projects/06-secops-mlops", use_container_width=True)

if __name__ == "__main__":
    render_secops_mlops_page()
