#!/bin/bash
echo "=== Cleaning Up SecOps-MLOps Pipeline ==="

# 1. Stop and remove Docker containers (Redis & Qdrant)
echo "Stopping Docker containers..."
docker compose down

# 2. Deactivate virtual environment if active (handles cases where script is sourced)
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "Deactivating virtual environment..."
    deactivate || true
fi

# 3. Clean up cached python files and local Feast temporary registries
echo "Cleaning up local cache files..."
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
rm -f .feast/registry.db-journal 2>/dev/null || true

echo "Cleanup complete! Redis and Qdrant containers have been stopped and removed."
