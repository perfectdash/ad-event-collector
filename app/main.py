from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from app.schemas import AdEvent
from app.publisher import publisher
from app.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start background batching worker
    await publisher.start()
    yield
    # Shutdown: Stop worker and flush queue
    await publisher.stop()

app = FastAPI(
    title="Low-Latency Ad Event Collector & Gateway",
    description="High-throughput asynchronous gateway for ad click, impression, and conversion events.",
    version="1.0.0",
    lifespan=lifespan
)

@app.post("/api/v1/events", status_code=status.HTTP_202_ACCEPTED)
async def collect_event(event: AdEvent):
    """
    Accepts, validates, and enqueues an ad event for asynchronous batch publishing.
    Returns 202 Accepted immediately if enqueued successfully.
    """
    event_dict = event.model_dump()
    
    # Enqueue event (non-blocking)
    enqueued = await publisher.enqueue_event(event_dict)
    
    if not enqueued:
        # Queue is full, handle backpressure
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Server is experiencing heavy load. Queue is full, please retry shortly."
        )
        
    return {
        "status": "Accepted",
        "event_id": event.event_id
    }

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Simple service health and queue status endpoint."""
    return {
        "status": "healthy",
        "queue_size": publisher.queue.qsize(),
        "max_queue_size": settings.MAX_QUEUE_SIZE,
        "mock_mode": settings.MOCK_PUBSUB
    }
