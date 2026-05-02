"""
FastAPI Lab 3 - Async MongoDB Integration

This application demonstrates:
- Connecting to MongoDB using Motor (async driver)
- Creating async CRUD operations
- Storing and retrieving JSON documents
- Working with MongoDB ObjectId
"""

import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from app.database import connect_to_mongodb, close_mongodb_connection, get_database
from app.models import NoteCreate, NoteResponse, NoteUpdate
from bson import ObjectId
from datetime import datetime, timezone

from contextlib import asynccontextmanager

load_dotenv()

# Old Version of db Connection ----------------------------
"""

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    await connect_to_mongodb()


@app.on_event("shutdown")
async def shutdown_event():
    await close_mongodb_connection()
"""

# New Version of db Connection ----------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Everything BEFORE yield runs on startup
    await connect_to_mongodb()
    print("Connected to MongoDB")
    
    yield  # App is running and handling requests here
    
    # Everything AFTER yield runs on shutdown
    await close_mongodb_connection()
    print("Disconnected from MongoDB")


# Create FastAPI application
app = FastAPI(
    title=os.getenv("APP_NAME"),
    description="Async MongoDB Integration with FastAPI",
    version="1.0.0",
    lifespan=lifespan
)


# Helper function to convert MongoDB document to response format
def note_helper(note) -> dict:
    """
    Convert MongoDB document to API response format.

    Converts ObjectId to string and structures data according to NoteResponse schema.
    """
    return {
        "id": str(note["_id"]),
        "title": note["title"],
        "content": note["content"],
        "tags": note.get("tags", []),
        "created_at": note["created_at"]
    }


@app.get("/")
async def root():
    return {
        "message": "Welcome to FastAPI Lab 3 - MongoDB Integration",
        "endpoints": {
            "create_note": "POST /notes",
            "get_all_notes": "GET /notes",
            "get_note": "GET /notes/{id}",
            "update_note": "PUT /notes/{id}",
            "delete_note": "DELETE /notes/{id}"
        }
    }


@app.post("/notes", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(note: NoteCreate):
    db = get_database()

    # Prepare note document
    note_dict = note.model_dump()
    note_dict["created_at"] = datetime.now(timezone.utc)

    # Insert into MongoDB
    result = await db.notes.insert_one(note_dict)

    # Retrieve the created note
    created_note = await db.notes.find_one({"_id": result.inserted_id})

    return note_helper(created_note)


@app.get("/notes", response_model=list[NoteResponse])
async def get_all_notes():
    db = get_database()

    # Find all notes, sort by creation time (newest first)
    notes = await db.notes.find().sort("created_at", -1).to_list(length=100)

    return [note_helper(note) for note in notes]


@app.get("/notes/{note_id}", response_model=NoteResponse)
async def get_note(note_id: str):
    # Validate ObjectId format
    if not ObjectId.is_valid(note_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid note ID format"
        )

    db = get_database()
    note = await db.notes.find_one({"_id": ObjectId(note_id)})

    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note with id {note_id} not found"
        )

    return note_helper(note)


@app.put("/notes/{note_id}", response_model=NoteResponse)
async def update_note(note_id: str, note_update: NoteUpdate):
    # Validate ObjectId format
    if not ObjectId.is_valid(note_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid note ID format"
        )

    db = get_database()

    # Only include fields that were provided
    update_data = note_update.model_dump(exclude_unset=True)
    """
    Without 'exclude_unset=True', updating just the 'title' would accidentally 
    wipe out content and tags in MongoDB. like: { "title": "New Title", "content": None, "tags": None }
    """

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )

    # Update the note
    result = await db.notes.update_one(
        {"_id": ObjectId(note_id)},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note with id {note_id} not found"
        )

    # Retrieve and return updated note
    updated_note = await db.notes.find_one({"_id": ObjectId(note_id)})
    return note_helper(updated_note)


@app.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(note_id: str):
    # Validate ObjectId format
    if not ObjectId.is_valid(note_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid note ID format"
        )

    db = get_database()
    result = await db.notes.delete_one({"_id": ObjectId(note_id)})

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note with id {note_id} not found"
        )

    return None
