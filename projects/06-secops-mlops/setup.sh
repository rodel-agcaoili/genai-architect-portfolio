#!/bin/bash
set -e

echo "=== Initializing SecOps-MLOps Pipeline ==="

# 1. Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# 2. Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# 3. Upgrade pip and install dependencies
echo "Installing python dependencies..."
pip install --upgrade pip
pip install fastapi uvicorn "feast[redis]" qdrant-client pandas pyarrow scikit-learn joblib

# 4. Generate mock telemetry data
echo "Generating mock telemetry data..."
python data/generate_mock_data.py

# 5. Start Docker containers (Redis and Qdrant)
echo "Starting Redis and Qdrant Docker containers..."
docker compose up -d

# 6. Wait for Redis & Qdrant to be fully healthy
echo "Waiting for backend services to become healthy..."
sleep 5

# 7. Apply Feast definitions to generate registry
echo "Applying Feast feature store registry..."
feast apply

# 8. Train the ML model on the Feast offline features
echo "Training ML Model (Isolation Forest Anomaly Detector)..."
python train.py

# 9. Materialize data from Parquet (Offline) to Redis (Online)
CURRENT_TIME=$(date -u +"%Y-%m-%dT%H:%M:%S")
echo "Materializing telemetry features to Redis online store up to $CURRENT_TIME..."
feast materialize 2026-06-01T00:00:00 "$CURRENT_TIME"

# 10. Vectorize and ingest unstructured logs into Qdrant
echo "Vectorizing security logs and populating Qdrant Vector Store..."
python qdrant_service.py

echo "Pipeline Initialized successfully!"
echo "You can now run: source venv/bin/activate"
