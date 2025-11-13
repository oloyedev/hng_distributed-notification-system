# app/middleware/auth.py
from fastapi import Header, HTTPException, status
from typing import Optional
import jwt
from datetime import datetime, timedelta

from app.core.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


async def get_current_user(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None)
):
    """
    Authenticate user using JWT token or API key
    
    Priority:
    1. JWT Token (Bearer token)
    2. API Key
    """
    # Try JWT first
    if authorization:
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format"
            )
        
        token = authorization.replace("Bearer ", "")
        
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            # Check expiration
            exp = payload.get("exp")
            if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token expired"
                )
            
            return {
                "user_id": payload.get("user_id"),
                "email": payload.get("email"),
                "auth_type": "jwt"
            }
            
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid JWT token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    # Try API Key
    if x_api_key:
        # In production, validate against database
        # For now, simple validation
        if len(x_api_key) < 20:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        return {
            "user_id": "api_key_user",
            "auth_type": "api_key",
            "api_key": x_api_key
        }
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No authentication provided"
    )


async def verify_service_token(
    x_service_token: Optional[str] = Header(None)
):
    """
    Verify service-to-service authentication
    
    Used by Email/Push services to update notification status
    """
    if not x_service_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Service token required"
        )
    
    # In production, validate against configured service tokens
    # For now, simple validation
    valid_services = ["email-service", "push-service"]
    
    # Token format: service-name:secret
    try:
        service_name, secret = x_service_token.split(":", 1)
        
        if service_name not in valid_services:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid service"
            )
        
        # In production, verify secret against database/env
        if len(secret) < 20:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid service secret"
            )
        
        return {
            "service": service_name,
            "auth_type": "service"
        }
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid service token format"
        )


def create_jwt_token(user_id: str, email: str, expires_delta: timedelta = None) -> str:
    """
    Create JWT token for testing
    """
    if expires_delta is None:
        expires_delta = timedelta(hours=24)
    
    expire = datetime.utcnow() + expires_delta
    
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token
