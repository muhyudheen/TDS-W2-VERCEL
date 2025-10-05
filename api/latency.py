# api/latency.py

import json
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import numpy as np

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

class LatencyRequest(BaseModel):
    regions: List[str]
    threshold_ms: int

data_path = os.path.join(os.path.dirname(__file__), 'vercel-latency.json')
with open(data_path, 'r') as f:
    telemetry_data = json.load(f)

@app.post("/api/latency")
async def get_latency_stats(request_data: LatencyRequest):
    regions_data = {}  # This will hold the data for each region
    regions_to_process = request_data.regions
    threshold = request_data.threshold_ms

    for region in regions_to_process:
        region_data = [d for d in telemetry_data if d.get("region") == region]

        if not region_data:
            regions_data[region] = {"error": "No data found for this region"}
            continue

        latencies = [d["latency_ms"] for d in region_data]
        uptimes = [d["uptime_percent"] for d in region_data]
        breaches = sum(1 for lat in latencies if lat > threshold)

        regions_data[region] = {
            "avg_latency": round(np.mean(latencies), 2),
            "p95_latency": round(np.percentile(latencies, 95), 2),
            "avg_uptime": round(np.mean(uptimes), 2),
            "breaches": breaches,
        }

    # Wrap the final result in a parent "regions" object
    return {"regions": regions_data}