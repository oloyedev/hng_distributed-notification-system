# template_service/app/schemas/template.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class TemplateCreate(BaseModel):
    template_code: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    subject: str = Field(..., min_length=1, max_length=500)
    body: str = Field(..., min_length=1)
    language: str = Field(default="en", min_length=2, max_length=10)
    created_by: Optional[str] = None


class TemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    subject: Optional[str] = Field(None, min_length=1, max_length=500)
    body: Optional[str] = Field(None, min_length=1)


class TemplateResponse(BaseModel):
    id: int
    template_code: str
    name: str
    description: Optional[str]
    subject: str
    body: str
    language: str
    version: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    
    class Config:
        from_attributes = True


class TemplateRenderRequest(BaseModel):
    template_code: str
    variables: Dict[str, Any]
    language: str = "en"
    version: Optional[int] = None


class TemplateRenderResponse(BaseModel):
    template_code: str
    subject: str
    body: str
    language: str
    version: int
    rendered_at: datetime


class PaginationMeta(BaseModel):
    total: int
    limit: int
    page: int
    total_pages: int
    has_next: bool
    has_previous: bool


class APIResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    message: str
    meta: Optional[PaginationMeta] = None