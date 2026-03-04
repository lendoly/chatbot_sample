from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional

class ChatMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str
    sender: str
    text: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
