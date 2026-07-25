import asyncio
import json
import logging
import time
from typing import List, Dict, Any
from app.config import settings

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ad_event_publisher")

class AsyncBatchPublisher:
    def __init__(self):
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=settings.MAX_QUEUE_SIZE)
        self.worker_task: asyncio.Task = None
        self.is_running = False
        
        # Real Google Cloud Pub/Sub clients (initialized lazily)
        self.pubsub_client = None
        self.topic_path = None

    def initialize_real_client(self):
        if not settings.MOCK_PUBSUB and not self.pubsub_client:
            try:
                from google.cloud import pubsub_v1
                self.pubsub_client = pubsub_v1.PublisherClient()
                self.topic_path = self.pubsub_client.topic_path(settings.PROJECT_ID, settings.TOPIC_ID)
                logger.info(f"Initialized real Pub/Sub client. Topic: {self.topic_path}")
            except Exception as e:
                logger.error(f"Failed to initialize real Pub/Sub client: {e}. Falling back to mock mode.")
                settings.MOCK_PUBSUB = True

    async def start(self):
        """Start the background worker task to drain the queue and publish batches."""
        self.is_running = True
        self.initialize_real_client()
        self.worker_task = asyncio.create_task(self._batch_processor_loop())
        logger.info("Background Async Batch Publisher started.")

    async def stop(self):
        """Stop the worker task and flush any remaining events in the queue."""
        logger.info("Stopping Async Batch Publisher, flushing remaining events...")
        self.is_running = False
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        
        # Drain whatever is left in the queue
        await self._flush_remaining()
        logger.info("Async Batch Publisher stopped successfully.")

    async def enqueue_event(self, event_data: Dict[str, Any]) -> bool:
        """Enqueue an event to be published in a batch. Non-blocking."""
        try:
            self.queue.put_nowait(event_data)
            return True
        except asyncio.QueueFull:
            logger.warning("Event queue is full. Backpressure threshold reached.")
            return False

    async def _batch_processor_loop(self):
        """Background loop that pools events and flushes them in batches or on timeouts."""
        timeout = settings.BATCH_TIMEOUT_MS / 1000.0
        
        while self.is_running:
            batch = []
            try:
                # 1. Block until at least one event is available (no CPU usage when idle)
                event = await self.queue.get()
                batch.append(event)
                self.queue.task_done()
                
                # 2. Accumulate more events until batch size is reached or timeout expires
                start_time = time.time()
                while len(batch) < settings.BATCH_SIZE:
                    elapsed = time.time() - start_time
                    if elapsed >= timeout:
                        break
                        
                    # Try to drain what's currently in the queue without blocking
                    try:
                        event = self.queue.get_nowait()
                        batch.append(event)
                        self.queue.task_done()
                    except asyncio.QueueEmpty:
                        # Queue is currently empty, yield control for a tiny slice
                        await asyncio.sleep(0.005) # Sleep for 5ms
            except asyncio.CancelledError:
                return
            except Exception as e:
                logger.error(f"Error in processor loop: {e}")
                continue

            if batch:
                await self._publish_batch(batch)

    async def _publish_batch(self, batch: List[Dict[str, Any]]):
        """Publishes a batch of events to Pub/Sub (mock or real)."""
        batch_size = len(batch)
        if settings.MOCK_PUBSUB:
            # Simulate tiny network latency (e.g. 5ms) for publishing
            await asyncio.sleep(0.005)
            # Occasional logging (in production this would be debug or metric counters)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Mock published batch of {batch_size} events.")
        else:
            # Publish using GCP Pub/Sub client
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._sync_publish_batch, batch)

    def _sync_publish_batch(self, batch: List[Dict[str, Any]]):
        """Synchronous helper for run_in_executor to execute blocking Pub/Sub network calls."""
        if not self.pubsub_client:
            return
        
        futures = []
        for event in batch:
            data_bytes = json.dumps(event).encode("utf-8")
            # Publish asynchronously (Pub/Sub client handles internally using threads)
            future = self.pubsub_client.publish(self.topic_path, data_bytes)
            futures.append(future)
            
        # Wait for all futures in the current batch to resolve to ensure delivery
        for future in futures:
            try:
                future.result(timeout=5.0)
            except Exception as e:
                logger.error(f"Failed to publish event to Pub/Sub: {e}")

    async def _flush_remaining(self):
        """Drains the queue entirely and publishes the final elements."""
        batch = []
        while not self.queue.empty():
            try:
                event = self.queue.get_nowait()
                batch.append(event)
                self.queue.task_done()
            except asyncio.QueueEmpty:
                break
                
        if batch:
            await self._publish_batch(batch)
            logger.info(f"Flushed final {len(batch)} events during shutdown.")

# Singleton instance of the publisher
publisher = AsyncBatchPublisher()
