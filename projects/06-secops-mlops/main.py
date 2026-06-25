import os
import joblib
from fastapi import FastAPI, HTTPException
from feast import FeatureStore
from pydantic import BaseModel

# Initialize FastAPI App
app = FastAPI(
    title="SecOps-MLOps Inference Service",
    description="Real-time security threat scoring powered by Feast & Redis",
    version="1.0.0"
)

# Resolve paths relative to the current file
repo_path = os.path.dirname(os.path.abspath(__file__))

# Initialize Feast Feature Store
try:
    store = FeatureStore(repo_path=repo_path)
except Exception as e:
    print(f"Error initializing Feast Feature Store: {e}")
    store = None

# Load the pre-trained ML model if it exists
model_path = os.path.join(repo_path, "model.joblib")
if os.path.exists(model_path):
    try:
        model = joblib.load(model_path)
        print(f"Loaded Machine Learning model from {model_path}")
    except Exception as e:
        print(f"Error loading model from {model_path}: {e}")
        model = None
else:
    print(f"No ML model found at {model_path}. Falling back to rule-based heuristics.")
    model = None


class ThreatPredictionResponse(BaseModel):
    source_ip: str
    failed_login_attempts_30m: int
    outbound_bytes_transferred_1h: int
    unique_iam_roles_assumed_5m: int
    risk_score: float
    status: str
    inference_type: str


@app.get("/")
def read_root():
    return {
        "status": "online",
        "feast_connected": store is not None,
        "ml_model_loaded": model is not None,
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
        # Define the entity row to query
        entity_rows = [{"source_ip": source_ip}]

        # Define the exact features to pull from Redis (Online Store)
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

        response_dict = response.to_dict()

        # Extract features (Feast returns them as lists matching the input entity rows)
        failed_logins = response_dict["failed_login_attempts_30m"][0]
        outbound_bytes = response_dict["outbound_bytes_transferred_1h"][0]
        iam_roles = response_dict["unique_iam_roles_assumed_5m"][0]

        # Handle None cases (if IP doesn't exist in the feature store yet)
        failed_logins = failed_logins if failed_logins is not None else 0
        outbound_bytes = outbound_bytes if outbound_bytes is not None else 0
        iam_roles = iam_roles if iam_roles is not None else 0

        # Run Inference
        if model is not None:
            # Format inputs as a 2D array for scikit-learn [[f1, f2, f3]]
            X = [[failed_logins, outbound_bytes, iam_roles]]
            
            # Predict anomaly (-1 is an anomaly, 1 is normal)
            prediction = model.predict(X)[0]
            
            # score_samples outputs the negative anomaly score. Lower is more anomalous.
            raw_score = model.score_samples(X)[0]
            
            # Normalize to 0-1 scale for risk representation
            # Isolation Forest anomaly threshold is model.offset_ (normally ~ -0.5)
            threshold = getattr(model, "offset_", -0.5)
            
            if prediction == -1:
                # Anomaly detected: Map risk score between 0.70 and 1.0 based on anomaly severity
                risk_score = min(0.7 + abs(raw_score - threshold) * 0.5, 1.0)
                status = "CRITICAL: Immediate Investigation Required"
            else:
                # Normal behavior: Map risk score between 0.0 and 0.69
                risk_score = max(0.0, 0.3 - (raw_score - threshold) * 0.5)
                if risk_score >= 0.3:
                    status = "WARNING: Anomalous Behavior Detected"
                else:
                    status = "BENIGN: Normal Operations"
            
            inference_type = "Machine Learning (Isolation Forest Model)"
        else:
            # Fallback heuristic calculation if model.joblib is not loaded
            risk_score = 0.0
            
            # Failed login logic (heavy indicator)
            if failed_logins > 5:
                risk_score += 0.4
            elif failed_logins > 2:
                risk_score += 0.15
                
            # Outbound bytes logic (data exfiltration indicator)
            if outbound_bytes > 100 * 1024 * 1024:
                risk_score += 0.35
            elif outbound_bytes > 10 * 1024 * 1024:
                risk_score += 0.1
                
            # IAM Role assumption logic (privilege escalation)
            if iam_roles > 3:
                risk_score += 0.25
            elif iam_roles > 1:
                risk_score += 0.10

            risk_score = min(risk_score, 1.0)

            if risk_score >= 0.7:
                status = "CRITICAL: Immediate Investigation Required"
            elif risk_score >= 0.3:
                status = "WARNING: Anomalous Behavior Detected"
            else:
                status = "BENIGN: Normal Operations"
            
            inference_type = "Fallback Rule-Based Heuristics"

        return ThreatPredictionResponse(
            source_ip=source_ip,
            failed_login_attempts_30m=failed_logins,
            outbound_bytes_transferred_1h=outbound_bytes,
            unique_iam_roles_assumed_5m=iam_roles,
            risk_score=round(risk_score, 2),
            status=status,
            inference_type=inference_type
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve features: {str(e)}"
        )
