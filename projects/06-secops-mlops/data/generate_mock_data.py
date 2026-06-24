import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

def generate_telemetry_data(num_records: int = 1000) -> pd.DataFrame:
    """Generates realistic cybersecurity telemetry data for the Feast feature store."""
    print(f"Generating {num_records} mock telemetry records...")
    
    # Generate timestamps (last 24 hours)
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=24)
    timestamps = [start_time + timedelta(seconds=np.random.randint(0, 86400)) for _ in range(num_records)]
    
    # IP Addresses (simulating some internal and some external)
    ips = [f"10.0.{np.random.randint(0, 255)}.{np.random.randint(1, 255)}" if np.random.random() > 0.3 
           else f"{np.random.randint(1, 255)}.{np.random.randint(0, 255)}.{np.random.randint(0, 255)}.{np.random.randint(1, 255)}"
           for _ in range(num_records)]

    data = {
        'source_ip': ips,
        'event_timestamp': timestamps,
        'created_timestamp': [datetime.utcnow() for _ in range(num_records)],
        'failed_login_attempts_30m': np.random.poisson(lam=0.5, size=num_records).clip(0, 100),
        'outbound_bytes_transferred_1h': np.random.lognormal(mean=10, sigma=2, size=num_records).astype(int),
        'unique_iam_roles_assumed_5m': np.random.poisson(lam=0.1, size=num_records).clip(0, 20)
    }
    
    # Inject some anomalies (simulated attacks)
    anomaly_indices = np.random.choice(num_records, size=int(num_records * 0.02), replace=False)
    for idx in anomaly_indices:
        data['failed_login_attempts_30m'][idx] = np.random.randint(15, 50)
        data['outbound_bytes_transferred_1h'][idx] = np.random.randint(500000000, 2000000000)
        data['unique_iam_roles_assumed_5m'][idx] = np.random.randint(5, 15)

    df = pd.DataFrame(data)
    # Feast requires timezone-aware datetime
    df['event_timestamp'] = pd.to_datetime(df['event_timestamp'], utc=True)
    df['created_timestamp'] = pd.to_datetime(df['created_timestamp'], utc=True)
    return df

def main():
    # Ensure data directory exists
    data_dir = Path(__file__).parent
    data_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = data_dir / "aggregated_metrics.parquet"
    
    df = generate_telemetry_data(5000)
    df.to_parquet(output_path, engine="pyarrow", index=False)
    
    print(f"✅ Successfully generated mock data at {output_path}")
    print(f"Data Schema:\n{df.dtypes}")
    print(f"\nSample Data:\n{df.head(3)}")

if __name__ == "__main__":
    main()
