from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class NoteBase(BaseModel):
    title: str
    content: str
    color: Optional[str] = "#ffeb3b"
    x: Optional[float] = 100.0
    y: Optional[float] = 100.0

class NoteCreate(NoteBase):
    id: Optional[str] = None

class Note(NoteBase):
    id: str
    timestamp: datetime

class RelationshipBase(BaseModel):
    fromId: str
    toId: str
    type: Optional[str] = "relates"
    label: Optional[str] = ""

class RelationshipCreate(RelationshipBase):
    pass

class Relationship(RelationshipBase):
    id: str

class GenerateRequest(BaseModel):
    description: str

class PositionUpdate(BaseModel):
    id: str
    x: float
    y: float
