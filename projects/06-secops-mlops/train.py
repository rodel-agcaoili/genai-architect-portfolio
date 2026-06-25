import os
import pandas as pd
from feast import FeatureStore
from sklearn.ensemble import IsolationForest
import joblib

# Initialize Feast Feature Store
repo_path = os.path.dirname(os.path.abspath(__file__))
store = FeatureStore(repo_path=repo_path)

# Extract entities and timestamps from historical data source
data_path = os.path.join(repo_path, "data/aggregated_metrics.parquet")
if not os.path.exists(data_path):
    raise FileNotFoundError(f"Mock data not found at {data_path}. Run generate_mock_data.py first.")

df = pd.read_parquet(data_path)
entity_df = df[["source_ip", "event_timestamp"]].copy()

# Retrieve historical features from the Offline Store (Parquet)
# Feast performs a point-in-time join to gather the features as they existed at each event_timestamp
print("Retrieving historical features from Feast offline store (Parquet)...")
training_data = store.get_historical_features(
    entity_df=entity_df,
    features=[
        "ip_telemetry_features:failed_login_attempts_30m",
        "ip_telemetry_features:outbound_bytes_transferred_1h",
        "ip_telemetry_features:unique_iam_roles_assumed_5m",
    ]
).to_df()

# Clean data for training
features = [
    "failed_login_attempts_30m",
    "outbound_bytes_transferred_1h",
    "unique_iam_roles_assumed_5m"
]
X = training_data[features].fillna(0)

# Train an Isolation Forest model (standard unsupervised model for threat hunting/anomaly detection)
print("Training Isolation Forest ML model on historical features...")
# We set contamination=0.02 because our mock generator injects anomalies into 2% of the records
model = IsolationForest(n_estimators=100, contamination=0.02, random_state=42)
model.fit(X)

# Save the trained model artifact
model_path = os.path.join(repo_path, "model.joblib")
joblib.dump(model, model_path)
print(f"ML Model successfully trained and serialized to {model_path}!")
