import httpx
from typing import Dict, Optional
from datetime import datetime

from app.core.config import get_settings
from app.utils.logger import setup_logger

settings = get_settings()
logger = setup_logger(__name__)


async def update_notification_status(
    notification_id: str,
    status: str,
    error: Optional[str] = None,
    metadata: Optional[Dict] = None
) -> Dict:
    """
    Update notification status in API Gateway
    
    Args:
        notification_id: Notification ID
        status: Status value (delivered, failed, pending)
        error: Error message if failed
        metadata: Additional metadata
    
    Returns:
        Result dict with success status
    """
    try:
        # Prepare status update payload
        payload = create_status_payload(
            notification_id=notification_id,
            status=status,
            error=error,
            metadata=metadata
        )
        
        # Send update to API Gateway
        result = await send_status_update(payload)
        
        return result
        
    except Exception as e:
        logger.error(f"Error updating status: {e}")
        return create_status_result(
            success=False,
            error=str(e)
        )


def create_status_payload(
    notification_id: str,
    status: str,
    error: Optional[str] = None,
    metadata: Optional[Dict] = None
) -> Dict:
    """
    Create status update payload
    Pure function
    """
    payload = {
        "notification_id": notification_id,
        "status": status,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if error:
        payload["error"] = error
    
    if metadata:
        payload["metadata"] = metadata
    
    return payload


async def send_status_update(payload: Dict) -> Dict:
    """
    Send status update to API Gateway
    Side effect function
    """
    try:
        url = f"{settings.API_GATEWAY_URL}/api/v1/email/status"
        
        headers = create_service_headers()
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success"):
                    logger.info(
                        f"Status updated successfully: {payload['notification_id']} -> {payload['status']}"
                    )
                    return create_status_result(success=True, data=data.get("data"))
                else:
                    return create_status_result(
                        success=False,
                        error=data.get("error", "Unknown error")
                    )
            else:
                return create_status_result(
                    success=False,
                    error=f"API Gateway returned {response.status_code}"
                )
                
    except httpx.TimeoutException:
        logger.warning("Status update timeout (non-critical)")
        return create_status_result(
            success=False,
            error="Status update timeout"
        )
    except Exception as e:
        logger.error(f"Error sending status update: {e}")
        return create_status_result(
            success=False,
            error=str(e)
        )


def create_service_headers() -> Dict:
    """
    Create headers for service-to-service authentication
    Pure function
    """
    return {
        "Content-Type": "application/json",
        "X-Service-Token": f"{settings.SERVICE_NAME}:{settings.SERVICE_TOKEN}"
    }


def create_status_result(success: bool, data: any = None, error: str = None) -> Dict:
    """
    Create standardized status result
    Pure function
    """
    return {
        "success": success,
        "data": data,
        "error": error
    }