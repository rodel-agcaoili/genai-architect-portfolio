#!/bin/bash
set -e

echo "=== Initializing SecOps-MLOps Pipeline ==="

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip and install dependencies
echo "Installing python dependencies..."
pip install --upgrade pip
pip install fastapi uvicorn "feast[redis]" qdrant-client pandas pyarrow sentence-transformers

# Generate mock telemetry data
echo "Generating mock telemetry data..."
python data/generate_mock_data.py

# Start Docker containers (Redis and Qdrant)
echo "Starting Redis and Qdrant Docker containers..."
docker-compose up -d

# Wait for Redis to be fully healthy
echo "Waiting for Redis to become healthy..."
sleep 5

# Apply Feast definitions to generate registry
echo "Applying Feast feature store registry..."
feast apply

# Materialize data from Parquet (Offline) to Redis (Online)
CURRENT_TIME=$(date -u +"%Y-%m-%dT%H:%M:%S")
echo "Materializing telemetry features to Redis online store up to $CURRENT_TIME..."
feast materialize 2026-06-01T00:00:00 "$CURRENT_TIME"

echo "Pipeline Initialized successfully!"
echo "You can now run: source venv/bin/activate"
