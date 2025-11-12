from pydantic import BaseModel
from datetime import datetime

class TemplateCreate(BaseModel):
    name: str
    content: str

class TemplateUpdate(BaseModel):
    content: str

class TemplateResponse(BaseModel):
    id: str
    name: str
    content: str
    version: int
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True

