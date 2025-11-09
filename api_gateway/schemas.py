from pydantic import BaseModel
from typing import Any, Optional

# Pagination Meta
class PaginationMeta(BaseModel):
    total: int = 0
    limit: int = 10
    page: int = 1
    total_pages: int = 1
    has_next: bool = False
    has_previous: bool = False

# Standard Response
class StandardResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    message: str
    meta: PaginationMeta = PaginationMeta()

# Notification Request Models
class EmailNotification(BaseModel):
    user_id: int
    template_id: str
    variables: dict

class PushNotification(BaseModel):
    user_id: int
    title: str
    message: str
    image_url: Optional[str] = None
    link: Optional[str] = None
