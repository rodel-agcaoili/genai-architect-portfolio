from datetime import timedelta
from feast import Entity, FeatureView, Field, FileSource
from feast.types import Int64

# Define the local offline file data source (Parquet file)
telemetry_source = FileSource(
    name="aggregated_metrics_source",
    path="data/aggregated_metrics.parquet",
    timestamp_field="event_timestamp",
    created_timestamp_column="created_timestamp",
)

# Define the primary key Entity (IP Address)
source_ip = Entity(
    name="source_ip",
    join_keys=["source_ip"],
    description="The source IP address of the telemetry event",
)

# Define the Feature View mapping schema to features
ip_telemetry_features_fv = FeatureView(
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
    tags={"domain": "security", "team": "secops"},
)
