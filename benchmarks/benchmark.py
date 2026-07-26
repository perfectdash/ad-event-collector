import asyncio
import time
import uuid
import random
import argparse
import sys
from datetime import datetime
from typing import List
import httpx

# I did this to pre-generate values and minimize client CPU overhead
EVENT_TYPES = ["click", "impression", "conversion"]
CAMPAIGNS = [f"camp-{random.randint(10000, 99999)}" for _ in range(50)]
ADVERTISERS = [f"adv-{random.randint(10000, 99999)}" for _ in range(20)]

def generate_event_payload() -> dict:
    return {
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "campaign_id": random.choice(CAMPAIGNS),
        "advertiser_id": random.choice(ADVERTISERS),
        "event_type": random.choice(EVENT_TYPES),
        "cost": round(random.uniform(0.01, 5.0), 4),
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "ip_address": f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
    }

async def send_request(client: httpx.AsyncClient, url: str, payload: dict, semaphore: asyncio.Semaphore, latencies: List[float], status_codes: List[int]):
    async with semaphore:
        start_time = time.perf_counter()
        try:
            response = await client.post(url, json=payload, timeout=10.0)
            latency = (time.perf_counter() - start_time) * 1000.0
            latencies.append(latency)
            status_codes.append(response.status_code)
        except Exception as e:
            latency = (time.perf_counter() - start_time) * 1000.0
            latencies.append(latency)
            # I did this to represent connection error or timeout
            status_codes.append(0)

async def run_benchmark(url: str, num_requests: int, concurrency: int):
    print("Pre-generating payloads to eliminate client CPU bottlenecks...")
    payloads = [generate_event_payload() for _ in range(num_requests)]
    
    print(f"Starting benchmark on: {url}")
    print(f"Total Requests: {num_requests} | Concurrency: {concurrency}\n")
    
    semaphore = asyncio.Semaphore(concurrency)
    latencies: List[float] = []
    status_codes: List[int] = []
    
    # I did this to configure connection pool limits for concurrency
    limits = httpx.Limits(max_keepalive_connections=concurrency, max_connections=concurrency * 2)
    
    start_wall_time = time.perf_counter()
    
    async with httpx.AsyncClient(limits=limits) as client:
        tasks = [
            send_request(client, url, payloads[i], semaphore, latencies, status_codes)
            for i in range(num_requests)
        ]
        await asyncio.gather(*tasks)
        
    end_wall_time = time.perf_counter()
    total_elapsed = end_wall_time - start_wall_time
    
    # I did this to analyze metrics and print statistics
    if not latencies:
        print("Error: No latency data was collected.")
        return
        
    latencies.sort()
    p50 = latencies[int(len(latencies) * 0.50)]
    p90 = latencies[int(len(latencies) * 0.90)]
    p95 = latencies[int(len(latencies) * 0.95)]
    p99 = latencies[int(len(latencies) * 0.99)]
    
    successful_requests = sum(1 for code in status_codes if code == 202)
    rate_limited = sum(1 for code in status_codes if code == 429)
    errors = len(status_codes) - successful_requests - rate_limited
    
    success_rate = (successful_requests / num_requests) * 100.0
    rps = num_requests / total_elapsed
    
    print("=" * 50)
    print("BENCHMARK RESULTS")
    print("=" * 50)
    print(f"Total Elapsed Time:  {total_elapsed:.4f} seconds")
    print(f"Throughput (RPS):    {rps:.2f} req/sec")
    print(f"Successful (202):    {successful_requests} ({success_rate:.2f}%)")
    if rate_limited > 0:
        print(f"Rate Limited (429):  {rate_limited} ({ (rate_limited/num_requests)*100:.2f}%)")
    if errors > 0:
        print(f"Failed/Errors:       {errors} ({ (errors/num_requests)*100:.2f}%)")
    print("-" * 50)
    print("LATENCY DISTRIBUTION")
    print("-" * 50)
    print(f"P50 (Median):        {p50:.2f} ms")
    print(f"P90:                 {p90:.2f} ms")
    print(f"P95:                 {p95:.2f} ms")
    print(f"P99 (SLA Target):    {p99:.2f} ms")
    print("=" * 50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Async Load Test Client")
    parser.add_argument("--url", default="http://127.0.0.1:8000/api/v1/events", help="Endpoint URL")
    parser.add_argument("--requests", type=int, default=10000, help="Total number of requests to send")
    parser.add_argument("--concurrency", type=int, default=100, help="Concurrency limit")
    
    args = parser.parse_args()
    
    # I did this to suppress Windows selector event loop warnings
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    asyncio.run(run_benchmark(args.url, args.requests, args.concurrency))
