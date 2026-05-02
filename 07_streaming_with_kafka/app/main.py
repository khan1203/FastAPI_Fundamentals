import os
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager

from .mongodb import connect_to_mongodb, close_mongodb_connection, get_mongodb
from .kafka_producer import start_kafka_producer, stop_kafka_producer, publish_log, get_topic_name
from .schemas import LogEvent

load_dotenv()

# 1. Define the lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup Logic ---
    await connect_to_mongodb()
    await start_kafka_producer()
    print("Application started and working...")
    
    yield  # This is where the application "lives" and handles requests
    
    # --- Shutdown Logic ---
    await close_mongodb_connection()
    await stop_kafka_producer()
    print("Application terminated.")


app = FastAPI(
    title=os.getenv("APP_NAME"),
    description="Kafka Event Streaming with FastAPI",
    version="1.0.0",
    lifespan=lifespan
)

### ------------------------------ Routes --------------------------------

@app.get("/ping")
def ping():
    return {"status": "ok", "message": "pong"}


@app.post("/log", status_code=202)
async def create_log(log: LogEvent):
    """
    Publish activity log to Kafka

    Returns 202 Accepted because event is queued, not processed yet
    """
    # Add timestamp if not provided
    log_data = log.dict()
    if not log_data.get("timestamp"):
        log_data["timestamp"] = datetime.utcnow().isoformat()

    try:
        # Publish to Kafka (fast, async operation)
        await publish_log(log_data)

        return {
            "status": "accepted",
            "message": "Log event published to Kafka",
            "topic": get_topic_name(),
            "event": log_data
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to publish event: {str(e)}"
        )


@app.get("/logs")
async def get_logs(limit: int = 10):
    """
    Retrieve processed logs from MongoDB

    These are logs that have been consumed and saved by the consumer
    """
    mongodb = get_mongodb()

    logs = await mongodb.logs.find().sort("timestamp", -1).limit(limit).to_list(length=limit)

    # Convert ObjectId to string
    for log in logs:
        log["_id"] = str(log["_id"])

    return {
        "count": len(logs),
        "logs": logs
    }


@app.get("/stats")
async def get_stats():
    """Get statistics about logged events"""
    mongodb = get_mongodb()

    total_logs = await mongodb.logs.count_documents({})

    # Count by action type
    pipeline = [
        {"$group": {"_id": "$action", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    action_stats = await mongodb.logs.aggregate(pipeline).to_list(length=100)

    return {
        "total_logs": total_logs,
        "by_action": action_stats
    }
