import asyncio
import json
import logging
import time
from typing import List, Dict, Any
from app.config import settings

# I did this to setup the logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ad_event_publisher")

class AsyncBatchPublisher:
    def __init__(self):
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=settings.MAX_QUEUE_SIZE)
        self.worker_task: asyncio.Task = None
        self.is_running = False
        
        # I did this to define lazy GCP Pub/Sub client handles
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
        self.is_running = True
        self.initialize_real_client()
        self.worker_task = asyncio.create_task(self._batch_processor_loop())
        logger.info("Background Async Batch Publisher started.")

    async def stop(self):
        logger.info("Stopping Async Batch Publisher, flushing remaining events...")
        self.is_running = False
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        
        # I did this to drain whatever is left in the queue
        await self._flush_remaining()
        logger.info("Async Batch Publisher stopped successfully.")

    async def enqueue_event(self, event_data: Dict[str, Any]) -> bool:
        try:
            self.queue.put_nowait(event_data)
            return True
        except asyncio.QueueFull:
            logger.warning("Event queue is full. Backpressure threshold reached.")
            return False

    async def _batch_processor_loop(self):
        timeout = settings.BATCH_TIMEOUT_MS / 1000.0
        
        while self.is_running:
            batch = []
            try:
                # I did this to block until at least one event is available
                event = await self.queue.get()
                batch.append(event)
                self.queue.task_done()
                
                # I did this to accumulate events up to batch size or timeout
                start_time = time.time()
                while len(batch) < settings.BATCH_SIZE:
                    elapsed = time.time() - start_time
                    if elapsed >= timeout:
                        break
                        
                    # I did this to drain the queue without blocking
                    try:
                        event = self.queue.get_nowait()
                        batch.append(event)
                        self.queue.task_done()
                    except asyncio.QueueEmpty:
                        # I did this to yield control if the queue is empty
                        await asyncio.sleep(0.005)
            except asyncio.CancelledError:
                return
            except Exception as e:
                logger.error(f"Error in processor loop: {e}")
                continue

            if batch:
                await self._publish_batch(batch)

    async def _publish_batch(self, batch: List[Dict[str, Any]]):
        batch_size = len(batch)
        if settings.MOCK_PUBSUB:
            # I did this to simulate network latency for mock mode
            await asyncio.sleep(0.005)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Mock published batch of {batch_size} events.")
        else:
            # I did this to publish events using GCP Pub/Sub client
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._sync_publish_batch, batch)

    def _sync_publish_batch(self, batch: List[Dict[str, Any]]):
        if not self.pubsub_client:
            return
        
        futures = []
        for event in batch:
            data_bytes = json.dumps(event).encode("utf-8")
            # I did this to publish events asynchronously
            future = self.pubsub_client.publish(self.topic_path, data_bytes)
            futures.append(future)
            
        # I did this to wait for all batch futures to resolve
        for future in futures:
            try:
                future.result(timeout=5.0)
            except Exception as e:
                logger.error(f"Failed to publish event to Pub/Sub: {e}")

    async def _flush_remaining(self):
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

# I did this to expose a publisher singleton
publisher = AsyncBatchPublisher()
