
import httpx
from typing import Dict, Optional, Callable
from functools import reduce
import asyncio

from app.core.config import get_settings
from ..services.template import fetch_and_render_template
from ..services.email_sender import send_email_smtp, send_email_sendgrid
from ..services.status import update_notification_status
from app.utils.logger import setup_logger

settings = get_settings()
logger = setup_logger(__name__)


async def process_email_message(message: Dict) -> Dict:
    """
    Main email processing pipeline
    Functional composition: fetch template -> render -> send -> update status
    
    Returns:
        Dict with success status and data/error
    """
    try:
        # Extract message components
        notification_id = message.get("notification_id")
        template_code = message.get("template_code")
        variables = message.get("variables", {})
        recipient = message.get("recipient")
        
        # Validate required fields
        validation_result = validate_message(message)
        if not validation_result["valid"]:
            return create_error_result(validation_result["error"])
        
        # Pipeline: fetch template -> render -> send -> update status
        pipeline_result = await execute_pipeline([
            lambda msg: fetch_template_step(msg),
            lambda result: render_template_step(result),
            lambda result: send_email_step(result),
            lambda result: update_status_step(result)
        ], message)
        
        return pipeline_result
        
    except Exception as e:
        logger.error(f"Error processing email message: {e}", exc_info=True)
        return create_error_result(str(e))


def validate_message(message: Dict) -> Dict:
    """
    Validate message has all required fields
    Pure function
    """
    required_fields = ["notification_id", "template_code", "recipient", "variables"]
    
    missing_fields = [
        field for field in required_fields 
        if field not in message or not message[field]
    ]
    
    if missing_fields:
        return {
            "valid": False,
            "error": f"Missing required fields: {', '.join(missing_fields)}"
        }
    
    return {"valid": True, "error": None}


async def execute_pipeline(steps: list[Callable], initial_data: any) -> Dict:
    """
    Execute async pipeline of functions
    Functional composition with error handling
    """
    try:
        result = {"success": True, "data": initial_data, "error": None}
        
        for step in steps:
            if not result["success"]:
                break
            
            result = await step(result["data"])
        
        return result
        
    except Exception as e:
        logger.error(f"Pipeline execution error: {e}")
        return create_error_result(str(e))


async def fetch_template_step(message: Dict) -> Dict:
    """
    Step 1: Fetch template from Template Service
    """
    try:
        template_code = message.get("template_code")
        
        logger.info(f"Fetching template: {template_code}")
        
        template_result = await fetch_and_render_template(
            template_code=template_code,
            variables=message.get("variables", {}),
            language=message.get("metadata", {}).get("language", "en")
        )
        
        if not template_result["success"]:
            return create_error_result(
                f"Failed to fetch template: {template_result['error']}"
            )
        
        # Merge template into message
        enriched_message = {
            **message,
            "template_content": template_result["data"]
        }
        
        return create_success_result(enriched_message)
        
    except Exception as e:
        logger.error(f"Template fetch step error: {e}")
        return create_error_result(str(e))


async def render_template_step(message: Dict) -> Dict:
    """
    Step 2: Render template with variables
    Template already rendered by template service
    """
    try:
        template_content = message.get("template_content", {})
        
        # Extract rendered content
        subject = template_content.get("subject", "")
        body = template_content.get("body", "")
        
        if not subject or not body:
            return create_error_result("Template content is empty")
        
        # Prepare email data
        email_data = {
            **message,
            "email_subject": subject,
            "email_body": body
        }
        
        return create_success_result(email_data)
        
    except Exception as e:
        logger.error(f"Template render step error: {e}")
        return create_error_result(str(e))


async def send_email_step(message: Dict) -> Dict:
    """
    Step 3: Send email via SMTP or SendGrid
    """
    try:
        recipient = message.get("recipient")
        subject = message.get("email_subject")
        body = message.get("email_body")
        
        logger.info(f"Sending email to: {recipient}")
        
        # Choose email sending method
        send_function = (
            send_email_sendgrid if settings.USE_SENDGRID 
            else send_email_smtp
        )
        
        send_result = await send_function(
            to_email=recipient,
            subject=subject,
            body=body
        )
        
        if not send_result["success"]:
            return create_error_result(
                f"Failed to send email: {send_result['error']}"
            )
        
        # Add delivery info to message
        message_with_delivery = {
            **message,
            "delivery_info": send_result["data"]
        }
        
        return create_success_result(message_with_delivery)
        
    except Exception as e:
        logger.error(f"Email send step error: {e}")
        return create_error_result(str(e))


async def update_status_step(message: Dict) -> Dict:
    """
    Step 4: Update notification status in API Gateway
    """
    try:
        notification_id = message.get("notification_id")
        
        logger.info(f"Updating status for: {notification_id}")
        
        status_result = await update_notification_status(
            notification_id=notification_id,
            status="delivered",
            metadata=message.get("delivery_info")
        )
        
        if not status_result["success"]:
            logger.warning(
                f"Failed to update status (email was sent): {status_result['error']}"
            )
            # Don't fail the whole pipeline if status update fails
        
        return create_success_result({
            "notification_id": notification_id,
            "status": "delivered",
            "recipient": message.get("recipient")
        })
        
    except Exception as e:
        logger.error(f"Status update step error: {e}")
        # Don't fail if status update fails, email was sent
        return create_success_result({
            "notification_id": message.get("notification_id"),
            "status": "delivered",
            "status_update_error": str(e)
        })


def create_success_result(data: any) -> Dict:
    """
    Create success result dictionary
    Pure function
    """
    return {
        "success": True,
        "data": data,
        "error": None
    }


def create_error_result(error: str) -> Dict:
    """
    Create error result dictionary
    Pure function
    """
    return {
        "success": False,
        "data": None,
        "error": error
    }


# Higher-order functions for composability

def compose(*functions):
    """
    Compose functions right to left
    Pure functional composition
    """
    return reduce(lambda f, g: lambda x: f(g(x)), functions, lambda x: x)


async def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    base_delay: int = 1
) -> any:
    """
    Retry function with exponential backoff
    Higher-order function
    """
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            
            delay = base_delay * (2 ** attempt)
            logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s: {e}")
            await asyncio.sleep(delay)