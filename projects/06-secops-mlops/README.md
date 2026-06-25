# 🛡️ SecOps-MLOps: Real-Time Telemetry Feature Store & Semantic Search Pipeline

This project demonstrates a production-grade, decoupled security telemetry processing and machine learning inference pipeline. It bridges the gap between high-velocity network metadata and ML models, resolving training-serving skew via a feature store while offering advanced threat intelligence hunting via a semantic vector search space.

## 🛠️ Technology Stack

*   **Feature Store / In-Memory Database**: [Feast](https://feast.dev/) backed by **Redis** (Local Docker instance)
*   **Vector Database**: [Qdrant](https://qdrant.tech/) (Local Docker instance) for HNSW-indexed vector search
*   **Inference Server**: **FastAPI** serving predictions and queries via REST endpoints
*   **Machine Learning Model**: **Scikit-Learn Isolation Forest** (Unsupervised anomaly detection)
*   **Embedding Model**: HuggingFace `sentence-transformers/all-MiniLM-L6-v2` (384-dimensional dense vectors)
*   **Orchestration / Automation**: Shell scripts and Docker Compose
*   **User Interface**: Streamlit Dashboard (Dual-mode: connected / simulation fallback)

---

## ⚡ Architecture Topology

```
    graph TD
        A[Raw Security Logs<br/>CloudTrail, VPC Flows] -->|Streaming| B(PySpark/Flink Processing)
        B -->|Aggregated Metrics| C[(Feast Store<br/>Redis + S3)]
        B -->|Embeddings| D[(Qdrant Vector DB)]
        
        C -->|Feature Vector| E{FastAPI Inference}
        D -->|Semantic Context| E
        E -->|Threat Score| F[SecOps Dashboard]
```

1.  **Ingestion & Aggregation**: Telemetry logs are compiled into time-series records (failed logins, outbound bytes, IAM role assumptions).
2.  **Feast Schema Mapping**: Features are written to an offline Parquet registry and materialized to an online Redis cluster for sub-millisecond querying.
3.  **Model Training**: An `IsolationForest` model is trained on Feast offline features to recognize outlier profiles (attack behaviors) and serialized.
4.  **Vector Store indexing**: Unstructured security logs are embedded into a dense semantic coordinate space and indexed in Qdrant with JSON payloads.
5.  **Serving Gateway**: FastAPI loads the model, retrieves real-time features from Redis, predicts threat anomalies, and routes semantic search queries to Qdrant.

---

## 🚀 How to Run the Live Pipeline Locally

### Prerequisites
*   Docker & Docker Compose installed
*   Python 3.9+ installed

### Step 1: Run the Automated Setup
Clone the repository, navigate to this directory, and execute the setup script:
```bash
chmod +x setup.sh
./setup.sh
```
**What this does**:
1. Creates a Python virtual environment (`venv`) and installs dependencies (`feast`, `qdrant-client`, `scikit-learn`, etc.).
2. Generates mock dataset of 5,000 security telemetry records.
3. Boots up Redis and Qdrant containers in detached mode.
4. Initializes the Feast repository and applies schema definitions.
5. Runs `train.py` to extract offline features, train the anomaly detection model, and save it as `model.joblib`.
6. Materializes the telemetry features to the online Redis store.
7. Vectorizes and ingests simulated threat intel logs into Qdrant.

### Step 2: Launch the FastAPI Gateway
Activate the virtual environment and start the Uvicorn server:
```bash
source venv/bin/activate
uvicorn main:app --reload
```
The REST API is now alive at `http://localhost:8000`. You can inspect the interactive docs at `http://localhost:8000/docs`.

### Step 3: Run the Streamlit Dashboard
From the **root directory** of the repository:
```bash
pip install -r requirements.txt  # If running Streamlit dependencies first time
streamlit run capstone/app.py
```
Navigate to **Project 6: SecOps-MLOps** in the sidebar. The UI will automatically detect the local backend and transition to **🟢 Live Mode**, enabling real-time ML inference and vector searches.

---

## 🧹 Cleanup & Shutdown

To stop and remove all Docker containers and clean local temp directories, run:
```bash
chmod +x cleanup.sh
./cleanup.sh
```
