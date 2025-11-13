# template_service/app/api/v1/routes/templates.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.database import get_db_session
from app.schemas.schema import (
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
    TemplateRenderRequest,
    TemplateRenderResponse,
    APIResponse
)
from app.services.template_service import (
    create_template_service,
    get_template_service,
    update_template_service,
    delete_template_service,
    list_templates_service,
    render_template_service,
    get_template_versions_service
)

router = APIRouter()


@router.post("/templates", response_model=APIResponse)
async def create_template(
    template_data: TemplateCreate,
    session: AsyncSession = Depends(get_db_session)
):
    """Create a new template"""
    result = await create_template_service(template_data, session)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result


@router.get("/templates/{template_code}", response_model=APIResponse)
async def get_template(
    template_code: str,
    language: Optional[str] = "en",
    version: Optional[int] = None,
    session: AsyncSession = Depends(get_db_session)
):
    """Get a specific template"""
    result = await get_template_service(template_code, language, version, session)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )
    
    return result


@router.put("/templates/{template_code}", response_model=APIResponse)
async def update_template(
    template_code: str,
    template_data: TemplateUpdate,
    language: Optional[str] = "en",
    session: AsyncSession = Depends(get_db_session)
):
    """Update a template (creates new version)"""
    result = await update_template_service(template_code, language, template_data, session)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result


@router.delete("/templates/{template_code}", response_model=APIResponse)
async def delete_template(
    template_code: str,
    language: Optional[str] = "en",
    session: AsyncSession = Depends(get_db_session)
):
    """Soft delete a template"""
    result = await delete_template_service(template_code, language, session)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )
    
    return result


@router.get("/templates", response_model=APIResponse)
async def list_templates(
    language: Optional[str] = None,
    active_only: bool = True,
    page: int = 1,
    limit: int = 20,
    session: AsyncSession = Depends(get_db_session)
):
    """List all templates"""
    result = await list_templates_service(language, active_only, page, limit, session)
    return result


@router.post("/templates/render", response_model=APIResponse)
async def render_template(
    render_request: TemplateRenderRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Render a template with variables
    This is the main endpoint used by Email Service
    """
    result = await render_template_service(render_request, session)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result


@router.get("/templates/{template_code}/versions", response_model=APIResponse)
async def get_template_versions(
    template_code: str,
    language: Optional[str] = "en",
    session: AsyncSession = Depends(get_db_session)
):
    """Get all versions of a template"""
    result = await get_template_versions_service(template_code, language, session)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )
    
    return result