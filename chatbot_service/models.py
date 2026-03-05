from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel


class ChatMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str
    sender: str
    text: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChatRequest(BaseModel):
    prompt: str = ""
    session_id: str = "default"
