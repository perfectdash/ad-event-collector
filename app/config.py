import os

class Settings:

    # I did this to define GCP configurations
    PROJECT_ID: str = os.getenv("GCP_PROJECT_ID", "google-ads-testing")
    TOPIC_ID: str = os.getenv("PUBSUB_TOPIC_ID", "ad-events-raw")
    
    # I did this to define batching parameters
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "100"))
    BATCH_TIMEOUT_MS: int = int(os.getenv("BATCH_TIMEOUT_MS", "100"))
    
    # I did this to define the maximum queue size to avoid OOM
    MAX_QUEUE_SIZE: int = int(os.getenv("MAX_QUEUE_SIZE", "100000"))
    
    # I did this to configure mock mode for local development
    MOCK_PUBSUB: bool = os.getenv("MOCK_PUBSUB", "True").lower() == "true"

settings = Settings()

