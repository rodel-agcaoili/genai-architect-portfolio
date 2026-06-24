import streamlit as st

def render_secops_mlops_page():
    st.set_page_config(page_title="SecOps-MLOps Pipeline", page_icon="🛡️", layout="wide")
    
    # 1. Executive Summary
    st.title("🛡️ SecOps-MLOps: Real-Time Telemetry Feature Store & Semantic Search")
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

    # 3. Interactive UI Elements (Code Snippets)
    st.subheader("Implementation Details")
    
    tab1, tab2, tab3 = st.tabs(["Feast FeatureView", "FastAPI Serving", "Qdrant Vector Storage"])
    
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
import pandas as pd

app = FastAPI(title="SecOps Inference Service")
store = FeatureStore(repo_path=".")

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

        # 2. Run ML Model (Mock)
        # model = load_model("xgboost_threat_v1")
        # risk_score = model.predict(feature_vector)
        
        # Determine risk based on thresholds
        risk_score = 0.0
        if feature_vector["ip_telemetry_features:failed_login_attempts_30m"][0] > 10:
            risk_score += 0.6
            
        return {
            "source_ip": source_ip,
            "features": feature_vector,
            "risk_score": min(risk_score, 1.0),
            "status": "investigate" if risk_score > 0.7 else "benign"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        """, language="python")

    with tab3:
        st.markdown("**Semantic Vector Search for Anomalies (`qdrant_client.py`)**")
        st.code("""
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

client = QdrantClient("localhost", port=6333)
model = SentenceTransformer('all-MiniLM-L6-v2')

# Initialize Collection
client.recreate_collection(
    collection_name="threat_intel_logs",
    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
)

def ingest_and_embed(log_text: str, log_id: int, metadata: dict):
    # Convert unstructured security log into semantic vector
    vector = model.encode(log_text).tolist()
    
    # Store in Qdrant with payload for filtering
    client.upsert(
        collection_name="threat_intel_logs",
        points=[
            PointStruct(
                id=log_id, 
                vector=vector, 
                payload={"raw_log": log_text, **metadata}
            )
        ]
    )
        """, language="python")

    st.divider()

    # 4. Call to Action
    st.subheader("Source Code & Deployment")
    st.markdown("The complete infrastructure-as-code, pipeline logic, and container configurations are available in my repository.")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Replace with your actual GitHub URL
        st.link_button("🔗 View Project on GitHub", "https://github.com/rodel-agcaoili/genai-architect-portfolio/tree/main/projects/06-secops-mlops", use_container_width=True)

if __name__ == "__main__":
    # If run directly via Streamlit, render the page
    render_secops_mlops_page()
