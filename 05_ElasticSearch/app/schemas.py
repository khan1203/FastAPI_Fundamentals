from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class NoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    tags: List[str] = Field(default=[])

    class Config:
        json_schema_extra = {
            "example": {
                "title": "FastAPI Tutorial",
                "content": "FastAPI is a modern web framework for building APIs with Python",
                "tags": ["fastapi", "python", "tutorial"]
            }
        }


class NoteOut(BaseModel):
    id: str = Field(alias="_id")
    title: str
    content: str
    tags: List[str]
    created_at: datetime

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "title": "FastAPI Tutorial",
                "content": "FastAPI is a modern web framework",
                "tags": ["fastapi", "python"],
                "created_at": "2024-12-17T10:30:00Z"
            }
        }


class SearchResult(BaseModel):
    id: str
    title: str
    content: str
    tags: List[str]
    score: float
    highlight: Optional[dict] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "title": "FastAPI Tutorial",
                "content": "FastAPI is a modern web framework...",
                "tags": ["fastapi", "python"],
                "score": 8.5,
                "highlight": {
                    "title": ["<em>FastAPI</em> Tutorial"]
                }
            }
        }
