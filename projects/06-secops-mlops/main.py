import os
from fastapi import FastAPI, HTTPException
from feast import FeatureStore
from pydantic import BaseModel

# Initialize FastAPI App
app = FastAPI(
    title="🛡️ SecOps-MLOps Inference Service",
    description="Real-time security threat scoring powered by Feast & Redis",
    version="1.0.0"
)

# Initialize Feast Feature Store
# We point it to the directory containing feature_store.yaml
try:
    # Get the directory of the current file to resolve paths correctly
    repo_path = os.path.dirname(os.path.abspath(__file__))
    store = FeatureStore(repo_path=repo_path)
except Exception as e:
    print(f"Error initializing Feast Feature Store: {e}")
    store = None


class ThreatPredictionResponse(BaseModel):
    source_ip: str
    failed_login_attempts_30m: int
    outbound_bytes_transferred_1h: int
    unique_iam_roles_assumed_5m: int
    risk_score: float
    status: str


@app.get("/")
def read_root():
    return {
        "status": "online",
        "feast_connected": store is not None,
        "message": "Welcome to the SecOps Threat Inference API. Use /predict_threat/{source_ip} to evaluate threat levels."
    }


@app.post("/predict_threat/{source_ip}", response_model=ThreatPredictionResponse)
async def predict_threat(source_ip: str):
    if store is None:
        raise HTTPException(
            status_code=500,
            detail="Feast Feature Store is not configured or initialized."
        )

    try:
        # Define the entity row we want to query
        entity_rows = [{"source_ip": source_ip}]

        # Define the exact features we want to pull from Redis (Online Store)
        features_to_fetch = [
            "ip_telemetry_features:failed_login_attempts_30m",
            "ip_telemetry_features:outbound_bytes_transferred_1h",
            "ip_telemetry_features:unique_iam_roles_assumed_5m",
        ]

        # Retrieve features from Redis
        response = store.get_online_features(
            features=features_to_fetch,
            entity_rows=entity_rows
        )

        # Convert Feast response response to a dictionary
        response_dict = response.to_dict()

        # Extract features (Feast returns them as lists matching the input entity rows)
        failed_logins = response_dict["failed_login_attempts_30m"][0]
        outbound_bytes = response_dict["outbound_bytes_transferred_1h"][0]
        iam_roles = response_dict["unique_iam_roles_assumed_5m"][0]

        # Handle None cases (if IP doesn't exist in the feature store yet)
        failed_logins = failed_logins if failed_logins is not None else 0
        outbound_bytes = outbound_bytes if outbound_bytes is not None else 0
        iam_roles = iam_roles if iam_roles is not None else 0

        # Calculate a threat heuristic (simulating a Machine Learning classifier)
        risk_score = 0.0
        
        # 1. Failed login logic (heavy indicator)
        if failed_logins > 5:
            risk_score += 0.4
        elif failed_logins > 2:
            risk_score += 0.15
            
        # 2. Outbound bytes logic (data exfiltration indicator: > 100MB)
        if outbound_bytes > 100 * 1024 * 1024:
            risk_score += 0.35
        elif outbound_bytes > 10 * 1024 * 1024:
            risk_score += 0.1
            
        # 3. IAM Role assumption logic (privilege escalation indicator)
        if iam_roles > 3:
            risk_score += 0.25
        elif iam_roles > 1:
            risk_score += 0.10

        # Cap the risk score at 1.0
        risk_score = min(risk_score, 1.0)

        # Determine status
        if risk_score >= 0.7:
            status = "CRITICAL: Immediate Investigation Required"
        elif risk_score >= 0.3:
            status = "WARNING: Anomalous Behavior Detected"
        else:
            status = "BENIGN: Normal Operations"

        return ThreatPredictionResponse(
            source_ip=source_ip,
            failed_login_attempts_30m=failed_logins,
            outbound_bytes_transferred_1h=outbound_bytes,
            unique_iam_roles_assumed_5m=iam_roles,
            risk_score=round(risk_score, 2),
            status=status
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve features: {str(e)}"
        )
