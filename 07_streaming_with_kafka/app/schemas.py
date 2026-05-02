from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class LogEvent(BaseModel):
    """Schema for activity log events"""
    user_id: str = Field(..., min_length=1)
    action: str = Field(..., min_length=1)
    resource: Optional[str] = None
    details: Optional[dict] = None
    timestamp: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "action": "create_note",
                "resource": "note_abc",
                "details": {"title": "My Note"}
            }
        }
