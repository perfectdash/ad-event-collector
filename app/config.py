import os

class Settings:

    # GCP Configurations
    PROJECT_ID: str = os.getenv("GCP_PROJECT_ID", "google-ads-testing")
    TOPIC_ID: str = os.getenv("PUBSUB_TOPIC_ID", "ad-events-raw")
    
    # Batching parameters
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "100"))
    BATCH_TIMEOUT_MS: int = int(os.getenv("BATCH_TIMEOUT_MS", "100"))
    
    MAX_QUEUE_SIZE: int = int(os.getenv("MAX_QUEUE_SIZE", "100000")) # will consume 512 bytes * 10000 = 50 MB Memory
    
    # Simulation mode to benchmark local speed without calling real GCP APIs
    MOCK_PUBSUB: bool = os.getenv("MOCK_PUBSUB", "True").lower() == "true"

settings = Settings()
