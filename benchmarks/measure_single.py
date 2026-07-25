import urllib.request
import json
import time

url = "http://127.0.0.1:8000/api/v1/events"
payload = {
    "event_id": "a4d33458-1be2-4b2a-bf3a-9f5b24479e02",
    "timestamp": "2026-07-25T12:00:00Z",
    "campaign_id": "camp-98765",
    "advertiser_id": "adv-12345",
    "event_type": "click",
    "cost": 1.25
}

data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

latencies = []
for i in range(5):
    start = time.perf_counter()
    with urllib.request.urlopen(req) as response:
        response.read()
    elapsed = (time.perf_counter() - start) * 1000.0
    latencies.append(elapsed)

print("Single request latencies (ms):", [round(l, 2) for l in latencies])
print("Average latency:", round(sum(latencies)/len(latencies), 2), "ms")
