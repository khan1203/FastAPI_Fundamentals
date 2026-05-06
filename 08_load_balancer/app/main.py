from fastapi import FastAPI, Request
import os
import socket

app = FastAPI(title="Load Balanced FastAPI")

# Get instance identifier from environment variable
INSTANCE_ID = os.getenv("INSTANCE_ID", "unknown")
HOSTNAME = socket.gethostname()

@app.get("/")
async def root(request: Request):
    return {
        "message": f"Hello from {INSTANCE_ID}!",
        "instance_id": INSTANCE_ID,
        "hostname": HOSTNAME,
        "client_ip": request.headers.get("X-Real-IP", request.client.host),
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "instance_id": INSTANCE_ID
    }

@app.get("/api/data")
async def get_data():
    return {
        "data": [
            {"id": 1, "value": "Item 1"},
            {"id": 2, "value": "Item 2"},
            {"id": 3, "value": "Item 3"}
        ],
        "served_by": INSTANCE_ID,
        "hostname": HOSTNAME
    }
