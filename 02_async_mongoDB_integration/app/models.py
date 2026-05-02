from pydantic import Field, BaseModel
from typing import Optional
from datetime import datetime



class NoteCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=250, description="Note title")
    content: str = Field(..., min_length=10, max_length=5000, description="Note Content")
    tags: Optional[list[str]] = Field(default=[], description="Optional tags for catagorization")

    class Config:
        json_schema_extra={
            "example": {
                "title": "FastAPI Fundamentals",
                "content": "The Description of the FastAPI tools and technologies.",
                "tags": ["FastAPI", "Pydantic", "Schema", "alembic"]
            } 
        }


class NoteResponse(BaseModel):
    id: str = Field(..., description="Unique identifier (MongoDB ObjectId)")
    title: str
    content: str
    tags: list[str]
    created_at: datetime = Field(..., description="Timestamp when note was created")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "title": "Learn FastAPI",
                "content": "FastAPI is a modern web framework",
                "tags": ["python", "fastapi"],
                "created_at": "2024-01-15T10:30:00Z"
            }
        }


class NoteUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    tags: Optional[list[str]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Updated Title",
                "tags": ["python", "fastapi", "mongodb"]
            }
        }