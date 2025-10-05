# api/latency.py

import json
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import numpy as np

# Initialize the FastAPI app
app = FastAPI()

# Enable CORS (Cross-Origin Resource Sharing) to allow requests from any origin.
# This is required by the prompt.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all domains
    allow_credentials=True,
    allow_methods=["POST"], # Allows only POST requests
    allow_headers=["*"],
)

# Define a Pydantic model for the request body to ensure
# the incoming data has the correct structure.
class LatencyRequest(BaseModel):
    regions: List[str]
    threshold_ms: int

# Load the telemetry data from the JSON file.
# This path is relative to the current script, making it work on Vercel.
data_path = os.path.join(os.path.dirname(__file__), 'vercel-latency.json')
with open(data_path, 'r') as f:
    telemetry_data = json.load(f)

# Define the main endpoint. It accepts POST requests at /api/latency.
@app.post("/api/latency")
async def get_latency_stats(request_data: LatencyRequest):
    """
    Analyzes latency data for specified regions and returns key metrics.
    """
    response = {}
    regions_to_process = request_data.regions
    threshold = request_data.threshold_ms

    # Loop through each region provided in the request
    for region in regions_to_process:
        # Filter the full dataset for records matching the current region
        region_data = [d for d in telemetry_data if d.get("region") == region]

        if not region_data:
            response[region] = {"error": "No data found for this region"}
            continue

        # Extract latencies and uptimes into separate lists for calculations
        latencies = [d["latency_ms"] for d in region_data]
        uptimes = [d["uptime_percent"] for d in region_data]

        # Calculate breaches by counting how many latencies are above the threshold
        breaches = sum(1 for lat in latencies if lat > threshold)

        # Calculate the required metrics using NumPy for efficiency
        response[region] = {
            "avg_latency": round(np.mean(latencies), 2),
            "p95_latency": round(np.percentile(latencies, 95), 2),
            "avg_uptime": round(np.mean(uptimes), 2),
            "breaches": breaches,
        }

    return response