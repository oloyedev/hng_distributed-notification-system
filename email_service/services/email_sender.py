
import smtplib
import httpx
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Optional
from datetime import datetime

from app.core.config import get_settings
from app.utils.logger import setup_logger

settings = get_settings()
logger = setup_logger(__name__)


async def send_email_smtp(
    to_email: str,
    subject: str,
    body: str,
    from_email: Optional[str] = None,
    from_name: Optional[str] = None
) -> Dict:
    """
    Send email using SMTP
    Functional approach with side effects isolated
    """
    try:
        # Prepare email components
        email_data = prepare_email_data(
            to_email=to_email,
            subject=subject,
            body=body,
            from_email=from_email or settings.SMTP_FROM_EMAIL,
            from_name=from_name or settings.SMTP_FROM_NAME
        )
        
        # Create MIME message
        message = create_mime_message(email_data)
        
        # Send via SMTP
        send_result = await send_via_smtp(message, to_email)
        
        return send_result
        
    except Exception as e:
        logger.error(f"SMTP send error: {e}")
        return create_send_result(
            success=False,
            error=str(e)
        )


def prepare_email_data(
    to_email: str,
    subject: str,
    body: str,
    from_email: str,
    from_name: str
) -> Dict:
    """
    Prepare email data structure
    Pure function
    """
    return {
        "to_email": to_email,
        "subject": subject,
        "body": body,
        "from_email": from_email,
        "from_name": from_name,
        "timestamp": datetime.utcnow().isoformat()
    }


def create_mime_message(email_data: Dict) -> MIMEMultipart:
    """
    Create MIME message from email data
    Pure function (technically creates object, but deterministic)
    """
    message = MIMEMultipart("alternative")
    message["Subject"] = email_data["subject"]
    message["From"] = f"{email_data['from_name']} <{email_data['from_email']}>"
    message["To"] = email_data["to_email"]
    
    # Add HTML body
    html_part = MIMEText(email_data["body"], "html")
    message.attach(html_part)
    
    return message


async def send_via_smtp(message: MIMEMultipart, to_email: str) -> Dict:
    """
    Send message via SMTP server
    Side effect function
    """
    try:
        # Create SMTP connection
        if settings.SMTP_USE_TLS:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT)
        
        # Login
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        
        # Send email
        server.send_message(message)
        server.quit()
        
        logger.info(f"Email sent successfully via SMTP to: {to_email}")
        
        return create_send_result(
            success=True,
            data={
                "method": "smtp",
                "recipient": to_email,
                "sent_at": datetime.utcnow().isoformat()
            }
        )
        
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error: {e}")
        return create_send_result(
            success=False,
            error=f"SMTP error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error sending via SMTP: {e}")
        return create_send_result(
            success=False,
            error=str(e)
        )


async def send_email_sendgrid(
    to_email: str,
    subject: str,
    body: str,
    from_email: Optional[str] = None,
    from_name: Optional[str] = None
) -> Dict:
    """
    Send email using SendGrid API
    Functional approach
    """
    try:
        if not settings.SENDGRID_API_KEY:
            return create_send_result(
                success=False,
                error="SendGrid API key not configured"
            )
        
        # Prepare SendGrid payload
        payload = create_sendgrid_payload(
            to_email=to_email,
            subject=subject,
            body=body,
            from_email=from_email or settings.SMTP_FROM_EMAIL,
            from_name=from_name or settings.SMTP_FROM_NAME
        )
        
        # Send via SendGrid API
        send_result = await send_via_sendgrid_api(payload)
        
        return send_result
        
    except Exception as e:
        logger.error(f"SendGrid send error: {e}")
        return create_send_result(
            success=False,
            error=str(e)
        )


def create_sendgrid_payload(
    to_email: str,
    subject: str,
    body: str,
    from_email: str,
    from_name: str
) -> Dict:
    """
    Create SendGrid API payload
    Pure function
    """
    return {
        "personalizations": [
            {
                "to": [{"email": to_email}],
                "subject": subject
            }
        ],
        "from": {
            "email": from_email,
            "name": from_name
        },
        "content": [
            {
                "type": "text/html",
                "value": body
            }
        ]
    }


async def send_via_sendgrid_api(payload: Dict) -> Dict:
    """
    Send email via SendGrid API
    Side effect function
    """
    try:
        url = "https://api.sendgrid.com/v3/mail/send"
        headers = {
            "Authorization": f"Bearer {settings.SENDGRID_API_KEY}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            
            if response.status_code in [200, 202]:
                logger.info(
                    f"Email sent successfully via SendGrid to: "
                    f"{payload['personalizations'][0]['to'][0]['email']}"
                )
                
                return create_send_result(
                    success=True,
                    data={
                        "method": "sendgrid",
                        "recipient": payload['personalizations'][0]['to'][0]['email'],
                        "sent_at": datetime.utcnow().isoformat(),
                        "message_id": response.headers.get("X-Message-Id")
                    }
                )
            else:
                return create_send_result(
                    success=False,
                    error=f"SendGrid returned {response.status_code}: {response.text}"
                )
                
    except httpx.TimeoutException:
        return create_send_result(
            success=False,
            error="SendGrid API timeout"
        )
    except Exception as e:
        return create_send_result(
            success=False,
            error=f"SendGrid API error: {str(e)}"
        )


def create_send_result(success: bool, data: any = None, error: str = None) -> Dict:
    """
    Create standardized send result
    Pure function
    """
    return {
        "success": success,
        "data": data,
        "error": error
    }


def validate_email(email: str) -> bool:
    """
    Simple email validation
    Pure function
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))