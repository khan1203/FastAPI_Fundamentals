import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from datetime import datetime
from bson import ObjectId
from typing import List

from .mongodb import connect_to_mongodb, close_mongodb_connection, get_mongodb
from .elasticsearch import connect_to_elasticsearch, close_elasticsearch_connection, get_elasticsearch, ELASTICSEARCH_INDEX
from .schemas import NoteCreate, NoteOut, SearchResult

load_dotenv()

app = FastAPI(
    title=os.getenv("APP_NAME"),
    description="Full-Text Search with Elasticsearch",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    await connect_to_mongodb()
    await connect_to_elasticsearch()


@app.on_event("shutdown")
async def shutdown_event():
    await close_mongodb_connection()
    await close_elasticsearch_connection()


@app.get("/ping")
def ping():
    return {"status": "ok", "message": "pong"}


@app.post("/notes", response_model=NoteOut, status_code=201)
async def create_note(note: NoteCreate):
    mongodb = get_mongodb()
    es = get_elasticsearch()

    # Create note document
    note_doc = {
        "title": note.title,
        "content": note.content,
        "tags": note.tags,
        "created_at": datetime.utcnow()
    }

    # Insert into MongoDB
    result = await mongodb.notes.insert_one(note_doc)
    note_id = str(result.inserted_id)

    # Index in Elasticsearch
    await es.index(
        index=ELASTICSEARCH_INDEX,
        id=note_id,
        document={
            "title": note.title,
            "content": note.content,
            "tags": note.tags,
            "created_at": note_doc["created_at"].isoformat()
        }
    )

    # Return created note
    note_doc["_id"] = note_id
    return note_doc


@app.get("/notes", response_model=List[NoteOut])
async def get_notes(limit: int = Query(default=10, le=100)):
    mongodb = get_mongodb()

    cursor = mongodb.notes.find().sort("created_at", -1).limit(limit)
    notes = await cursor.to_list(length=limit)

    for note in notes:
        note["_id"] = str(note["_id"])

    return notes


@app.get("/notes/{note_id}", response_model=NoteOut)
async def get_note(note_id: str):
    mongodb = get_mongodb()

    # Validate ObjectId
    if not ObjectId.is_valid(note_id):
        raise HTTPException(status_code=400, detail="Invalid note ID")

    note = await mongodb.notes.find_one({"_id": ObjectId(note_id)})

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    note["_id"] = str(note["_id"])
    return note


@app.get("/search", response_model=List[SearchResult])
async def search_notes(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(default=10, le=100)
):
    es = get_elasticsearch()

    # Build Elasticsearch query
    search_body = {
        "query": {
            "multi_match": {
                "query": q,
                "fields": ["title^3", "content"],
                "fuzziness": "AUTO"
            }
        },
        "highlight": {
            "fields": {
                "title": {},
                "content": {"fragment_size": 150}
            }
        },
        "size": limit
    }

    # Execute search
    response = await es.search(
        index=ELASTICSEARCH_INDEX,
        body=search_body
    )

    # Format results
    results = []
    for hit in response["hits"]["hits"]:
        result = SearchResult(
            id=hit["_id"],
            title=hit["_source"]["title"],
            content=hit["_source"]["content"],
            tags=hit["_source"]["tags"],
            score=hit["_score"],
            highlight=hit.get("highlight")
        )
        results.append(result)

    return results


@app.delete("/notes/{note_id}", status_code=204)
async def delete_note(note_id: str):
    mongodb = get_mongodb()
    es = get_elasticsearch()

    # Validate ObjectId
    if not ObjectId.is_valid(note_id):
        raise HTTPException(status_code=400, detail="Invalid note ID")

    # Delete from MongoDB
    result = await mongodb.notes.delete_one({"_id": ObjectId(note_id)})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Note not found")

    # Delete from Elasticsearch
    try:
        await es.delete(index=ELASTICSEARCH_INDEX, id=note_id)
    except Exception as e:
        print(f"Failed to delete from Elasticsearch: {e}")

    return None
