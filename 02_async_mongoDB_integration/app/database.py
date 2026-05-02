import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME")

client: AsyncIOMotorClient = None
database = None

async def connect_to_mongodb():
    global client, database

    client  = AsyncIOMotorClient(MONGODB_URL)
    database = client[DATABASE_NAME]

    print(f"Connected to mongodb at {MONGODB_URL}")
    print(f"Using db: {DATABASE_NAME}")

async def close_mongodb_connection():
    global client

    if client:
        client.close()
        print(f"MongoDB connection is closed.")

def get_database():
    return database