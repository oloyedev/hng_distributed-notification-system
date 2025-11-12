from pydantic import BaseModel
from typing import Dict, Optional

class EmailNotification(BaseModel):
    notification_type: str
    user_id: str
    template_code: str
    variables: Dict[str, str]
    request_id: str
    priority: int
    metadata: Optional[Dict[str, str]] = None
