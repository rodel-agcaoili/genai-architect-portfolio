import os
import hashlib
from datetime import datetime
from qdrant_client import QdrantClient
from qdrant_client.http import models

COLLECTION_NAME = "security_logs"


def get_text_embedding(text: str, dimensions: int = 384) -> list[float]:
    """
    A lightweight Feature Hashing Vectorizer (Hash Trick).
    Maps text to a 384-dimensional space using MD5 hashes of words.
    Provides fast, dependency-free text matching via Qdrant Cosine similarity.
    """
    vector = [0.0] * dimensions
    # Simple clean tokenization
    words = text.lower().replace(",", " ").replace(".", " ").replace("'", "").split()
    if not words:
        return vector

    for word in words:
        # Generate MD5 hash of the word
        h = hashlib.md5(word.encode('utf-8')).hexdigest()
        val = int(h, 16)
        index = val % dimensions
        # Alternate signs to reduce collision bias
        sign = 1 if (val % 2 == 0) else -1
        vector[index] += sign

    # Normalize to L2 unit vector for Cosine similarity
    norm = sum(x**2 for x in vector) ** 0.5
    if norm > 0:
        vector = [x / norm for x in vector]
    return vector


class QdrantService:
    def __init__(self, host="localhost", port=6333):
        # Establish connection to the Qdrant container
        self.client = QdrantClient(host=host, port=port)

    def init_collection(self):
        """Initializes the security log collection if it does not exist."""
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
        except Exception as e:
            print(f"Warning: Could not connect to Qdrant. Is the Docker container running? Error: {e}")
            return False

        if COLLECTION_NAME not in collection_names:
            print(f"Creating Qdrant collection '{COLLECTION_NAME}'...")
            self.client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=models.VectorParams(
                    size=384,  # Matching our 384-dimensional Feature Hashing vector space
                    distance=models.Distance.COSINE
                )
            )
        return True

    def ingest_mock_logs(self):
        """Vectorizes and ingests mock security logs with metadata payloads."""
        if not self.init_collection():
            return

        mock_logs = [
            {
                "id": 1,
                "text": "Brute force SSH attack detected on admin account from IP 192.168.1.15",
                "ip": "192.168.1.15",
                "severity": "HIGH",
            },
            {
                "id": 2,
                "text": "Data exfiltration: Outbound connection established to external IP 203.0.113.50 transferring 2GB of sensitive customer data",
                "ip": "203.0.113.50",
                "severity": "CRITICAL",
            },
            {
                "id": 3,
                "text": "IAM Role escalation: User svc-billing assumed Admin privileges without MFA",
                "ip": "10.0.2.14",
                "severity": "HIGH",
            },
            {
                "id": 4,
                "text": "Normal HTTP GET request to /index.html from IP 10.0.0.5",
                "ip": "10.0.0.5",
                "severity": "INFO",
            },
            {
                "id": 5,
                "text": "SQL injection attempt detected in query parameter: 'SELECT * FROM users;'",
                "ip": "192.168.1.99",
                "severity": "CRITICAL",
            },
            {
                "id": 6,
                "text": "Successful SSH login on admin account from corporate VPN IP 10.0.5.50",
                "ip": "10.0.5.50",
                "severity": "INFO",
            },
            {
                "id": 7,
                "text": "Port scanning activity detected from IP 192.168.1.15 scanning ports 22, 80, 443, 8080",
                "ip": "192.168.1.15",
                "severity": "MEDIUM",
            },
        ]

        print(f"Generating embeddings for {len(mock_logs)} security logs using local Feature Hashing...")
        points = []
        for item in mock_logs:
            # Generate the vector hash
            vector = get_text_embedding(item["text"])
            points.append(
                models.PointStruct(
                    id=item["id"],
                    vector=vector,
                    payload={
                        "raw_log": item["text"],
                        "source_ip": item["ip"],
                        "severity": item["severity"],
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
            )

        # Upsert to Qdrant collection
        self.client.upsert(
            collection_name=COLLECTION_NAME,
            wait=True,
            points=points
        )
        print("✅ Qdrant semantic database populated successfully!")

    def semantic_search(self, query_text: str, severity_filter: str = None, limit: int = 3):
        """Converts query to vector and searches Qdrant with optional payload filter."""
        # Convert input query to vector using local Feature Hashing
        query_vector = get_text_embedding(query_text)

        # Build payload filter condition if requested
        query_filter = None
        if severity_filter:
            query_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="severity",
                        match=models.MatchValue(value=severity_filter)
                    )
                ]
            )

        # Query vector space
        results = self.client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            query_filter=query_filter,
            limit=limit
        )

        # Parse output
        hits = []
        for hit in results:
            hits.append({
                "score": round(hit.score, 4),
                "log": hit.payload.get("raw_log"),
                "source_ip": hit.payload.get("source_ip"),
                "severity": hit.payload.get("severity"),
                "timestamp": hit.payload.get("timestamp")
            })
        return hits


if __name__ == "__main__":
    # If executed directly, ingest the logs
    print("Initializing Qdrant Log Ingestion Engine...")
    service = QdrantService()
    service.ingest_mock_logs()
