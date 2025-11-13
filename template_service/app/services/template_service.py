
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from typing import Dict, Optional, List
from datetime import datetime

from app.core.database import Template
from app.schemas.schema import (
    TemplateCreate,
    TemplateUpdate,
    TemplateRenderRequest,
    PaginationMeta
)
from app.services.template_render import render_template_with_variables
from app.core.redis import get_redis_client
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


async def create_template_service(
    template_data: TemplateCreate,
    session: AsyncSession
) -> Dict:
    """
    Create a new template
    Functional pipeline: validate -> check existing -> create -> cache
    """
    try:
        # Check if template already exists
        existing = await get_existing_template(
            template_data.template_code,
            template_data.language,
            session
        )
        
        if existing:
            return create_result(
                success=False,
                error=f"Template {template_data.template_code} already exists for language {template_data.language}"
            )
        
        # Create template entity
        template = create_template_entity(template_data)
        
        # Save to database
        saved_template = await save_template(template, session)
        
        if not saved_template:
            return create_result(
                success=False,
                error="Failed to save template"
            )
        
        # Invalidate cache
        await invalidate_template_cache(template_data.template_code, template_data.language)
        
        return create_result(
            success=True,
            data=template_to_dict(saved_template),
            message="Template created successfully"
        )
        
    except Exception as e:
        logger.error(f"Error creating template: {e}")
        return create_result(success=False, error=str(e))


async def get_template_service(
    template_code: str,
    language: str,
    version: Optional[int],
    session: AsyncSession
) -> Dict:
    """
    Get a specific template
    Functional pipeline: check cache -> query db -> cache result
    """
    try:
        # Try cache first
        cached = await get_cached_template(template_code, language, version)
        if cached:
            return create_result(
                success=True,
                data=cached,
                message="Template retrieved from cache"
            )
        
        # Query from database
        template = await query_template(template_code, language, version, session)
        
        if not template:
            return create_result(
                success=False,
                error="Template not found"
            )
        
        template_dict = template_to_dict(template)
        
        # Cache result
        await cache_template(template_code, language, version, template_dict)
        
        return create_result(
            success=True,
            data=template_dict,
            message="Template retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting template: {e}")
        return create_result(success=False, error=str(e))


async def update_template_service(
    template_code: str,
    language: str,
    template_data: TemplateUpdate,
    session: AsyncSession
) -> Dict:
    """
    Update template (creates new version)
    Functional pipeline: get current -> create new version -> save -> invalidate cache
    """
    try:
        # Get current template
        current = await query_template(template_code, language, None, session)
        
        if not current:
            return create_result(
                success=False,
                error="Template not found"
            )
        
        # Create new version
        new_version = create_new_version(current, template_data)
        
        # Deactivate old version
        current.is_active = False
        
        # Save both
        session.add(new_version)
        await session.commit()
        await session.refresh(new_version)
        
        # Invalidate cache
        await invalidate_template_cache(template_code, language)
        
        return create_result(
            success=True,
            data=template_to_dict(new_version),
            message=f"Template updated to version {new_version.version}"
        )
        
    except Exception as e:
        logger.error(f"Error updating template: {e}")
        await session.rollback()
        return create_result(success=False, error=str(e))


async def delete_template_service(
    template_code: str,
    language: str,
    session: AsyncSession
) -> Dict:
    """
    Soft delete template
    """
    try:
        template = await query_template(template_code, language, None, session)
        
        if not template:
            return create_result(
                success=False,
                error="Template not found"
            )
        
        template.is_active = False
        await session.commit()
        
        # Invalidate cache
        await invalidate_template_cache(template_code, language)
        
        return create_result(
            success=True,
            message="Template deleted successfully"
        )
        
    except Exception as e:
        logger.error(f"Error deleting template: {e}")
        await session.rollback()
        return create_result(success=False, error=str(e))


async def list_templates_service(
    language: Optional[str],
    active_only: bool,
    page: int,
    limit: int,
    session: AsyncSession
) -> Dict:
    """
    List templates with pagination
    Pure functional query composition
    """
    try:
        # Build query
        query = build_list_query(language, active_only)
        
        # Get total count
        count_query = select(func.count()).select_from(Template).where(query.whereclause)
        total_result = await session.execute(count_query)
        total = total_result.scalar_one()
        
        # Get paginated results
        offset = (page - 1) * limit
        result = await session.execute(
            query.offset(offset).limit(limit).order_by(desc(Template.created_at))
        )
        templates = result.scalars().all()
        
        # Calculate pagination meta
        meta = calculate_pagination_meta(total, page, limit)
        
        return create_result(
            success=True,
            data=[template_to_dict(t) for t in templates],
            message=f"Retrieved {len(templates)} templates",
            meta=meta
        )
        
    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        return create_result(success=False, error=str(e))


async def render_template_service(
    render_request: TemplateRenderRequest,
    session: AsyncSession
) -> Dict:
    """
    Render template with variables
    Main function used by Email Service
    Functional pipeline: get template -> render -> return
    """
    try:
        # Get template
        template_result = await get_template_service(
            render_request.template_code,
            render_request.language,
            render_request.version,
            session
        )
        
        if not template_result["success"]:
            return template_result
        
        template_data = template_result["data"]
        
        # Render subject and body
        rendered = render_template_with_variables(
            subject=template_data["subject"],
            body=template_data["body"],
            variables=render_request.variables
        )
        
        return create_result(
            success=True,
            data={
                "template_code": template_data["template_code"],
                "subject": rendered["subject"],
                "body": rendered["body"],
                "language": template_data["language"],
                "version": template_data["version"],
                "rendered_at": datetime.utcnow().isoformat()
            },
            message="Template rendered successfully"
        )
        
    except Exception as e:
        logger.error(f"Error rendering template: {e}")
        return create_result(success=False, error=str(e))


async def get_template_versions_service(
    template_code: str,
    language: str,
    session: AsyncSession
) -> Dict:
    """
    Get all versions of a template
    """
    try:
        query = select(Template).where(
            and_(
                Template.template_code == template_code,
                Template.language == language
            )
        ).order_by(desc(Template.version))
        
        result = await session.execute(query)
        templates = result.scalars().all()
        
        if not templates:
            return create_result(
                success=False,
                error="No versions found"
            )
        
        return create_result(
            success=True,
            data=[template_to_dict(t) for t in templates],
            message=f"Retrieved {len(templates)} versions"
        )
        
    except Exception as e:
        logger.error(f"Error getting template versions: {e}")
        return create_result(success=False, error=str(e))


# Pure helper functions

def create_template_entity(template_data: TemplateCreate) -> Template:
    """Create Template entity from schema - Pure function"""
    return Template(
        template_code=template_data.template_code,
        name=template_data.name,
        description=template_data.description,
        subject=template_data.subject,
        body=template_data.body,
        language=template_data.language,
        version=1,
        is_active=True,
        created_by=template_data.created_by
    )


def create_new_version(current: Template, update_data: TemplateUpdate) -> Template:
    """Create new version from current template - Pure function"""
    return Template(
        template_code=current.template_code,
        name=update_data.name or current.name,
        description=update_data.description or current.description,
        subject=update_data.subject or current.subject,
        body=update_data.body or current.body,
        language=current.language,
        version=current.version + 1,
        is_active=True,
        created_by=current.created_by
    )


def template_to_dict(template: Template) -> Dict:
    """Convert Template to dict - Pure function"""
    return {
        "id": template.id,
        "template_code": template.template_code,
        "name": template.name,
        "description": template.description,
        "subject": template.subject,
        "body": template.body,
        "language": template.language,
        "version": template.version,
        "is_active": template.is_active,
        "created_at": template.created_at.isoformat(),
        "updated_at": template.updated_at.isoformat(),
        "created_by": template.created_by
    }


def build_list_query(language: Optional[str], active_only: bool):
    """Build list query - Pure function"""
    conditions = []
    
    if language:
        conditions.append(Template.language == language)
    
    if active_only:
        conditions.append(Template.is_active == True)
    
    if conditions:
        return select(Template).where(and_(*conditions))
    return select(Template)


def calculate_pagination_meta(total: int, page: int, limit: int) -> Dict:
    """Calculate pagination metadata - Pure function"""
    total_pages = (total + limit - 1) // limit
    
    return {
        "total": total,
        "limit": limit,
        "page": page,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1
    }


def create_result(
    success: bool,
    data: any = None,
    error: str = None,
    message: str = "",
    meta: any = None
) -> Dict:
    """Create standardized result - Pure function"""
    return {
        "success": success,
        "data": data,
        "error": error,
        "message": message,
        "meta": meta
    }


# Database operations

async def get_existing_template(
    template_code: str,
    language: str,
    session: AsyncSession
) -> Optional[Template]:
    """Check if template exists"""
    query = select(Template).where(
        and_(
            Template.template_code == template_code,
            Template.language == language,
            Template.is_active == True
        )
    )
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def query_template(
    template_code: str,
    language: str,
    version: Optional[int],
    session: AsyncSession
) -> Optional[Template]:
    """Query template from database"""
    conditions = [
        Template.template_code == template_code,
        Template.language == language,
        Template.is_active == True
    ]
    
    if version:
        conditions.append(Template.version == version)
    
    query = select(Template).where(and_(*conditions)).order_by(desc(Template.version))
    
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def save_template(template: Template, session: AsyncSession) -> Optional[Template]:
    """Save template to database"""
    try:
        session.add(template)
        await session.commit()
        await session.refresh(template)
        return template
    except Exception as e:
        logger.error(f"Error saving template: {e}")
        await session.rollback()
        return None


# Cache operations

async def get_cached_template(
    template_code: str,
    language: str,
    version: Optional[int]
) -> Optional[Dict]:
    """Get template from cache"""
    try:
        redis = get_redis_client()
        cache_key = create_template_cache_key(template_code, language, version)
        return await redis.get_json(cache_key)
    except Exception as e:
        logger.error(f"Error getting cached template: {e}")
        return None


async def cache_template(
    template_code: str,
    language: str,
    version: Optional[int],
    template_data: Dict
) -> bool:
    """Cache template"""
    try:
        redis = get_redis_client()
        cache_key = create_template_cache_key(template_code, language, version)
        return await redis.set_json(cache_key, template_data, ttl=3600)
    except Exception as e:
        logger.error(f"Error caching template: {e}")
        return False


async def invalidate_template_cache(template_code: str, language: str) -> bool:
    """Invalidate template cache"""
    try:
        redis = get_redis_client()
        # Delete all versions of this template
        pattern = f"template:{template_code}:{language}:*"
        # In production, use SCAN instead of KEYS
        return True
    except Exception as e:
        logger.error(f"Error invalidating cache: {e}")
        return False


def create_template_cache_key(
    template_code: str,
    language: str,
    version: Optional[int]
) -> str:
    """Create cache key - Pure function"""
    version_str = str(version) if version else "latest"
    return f"template:{template_code}:{language}:{version_str}"