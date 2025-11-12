from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from uuid import uuid4 

import models
import schemas
from database import get_db
from utils import cache_template, get_cached_template, invalidate_cache


router = APIRouter(prefix="/templates", tags=["Templates"])


@router.post("/", response_model=schemas.TemplateResponse)
def create_template(template: schemas.TemplateCreate, db: Session = Depends(get_db)):
    db_template = models.Template(
        id=str(uuid4()),
        name=template.name,
        content=template.content,
        version=1
    )
    db.add(db_template)
    try:
        db.commit()
        db.refresh(db_template)
        cache_template(str(db_template.id), schemas.TemplateResponse.from_orm(db_template))
        return db_template
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"Template with name '{template.name}' already exists."
        )


@router.get("/{template_id}", response_model=schemas.TemplateResponse)
def get_template(template_id: str, db: Session = Depends(get_db)):
    cached = get_cached_template(template_id, schemas.TemplateResponse)
    if cached:
        return cached

    template = db.query(models.Template).filter(models.Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    template_response = schemas.TemplateResponse.from_orm(template)
    cache_template(str(template.id), template_response)

    return template_response


@router.get("/", response_model=list[schemas.TemplateResponse])
def get_templates(db: Session = Depends(get_db)):
    # Only fetch latest version of each template
    latest_templates = (
        db.query(models.Template).all()
    )
    return [schemas.TemplateResponse.from_orm(t) for t in latest_templates]





@router.put("/{template_id}", response_model=schemas.TemplateResponse)
def update_template(template_id: str, update: schemas.TemplateUpdate, db: Session = Depends(get_db)):
    # Fetch current template
    template = db.query(models.Template).filter(models.Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    new_version = template.version + 1

  
    new_template = models.Template(
        id=str(uuid4()),
        name=template.name,
        content=update.content,
        version=new_version,
        updated_at=datetime.utcnow()
    )

    db.add(new_template)
    db.commit()
    db.refresh(new_template)

    invalidate_cache(template_id)
    cache_template(str(new_template.id), schemas.TemplateResponse.from_orm(new_template).dict())

    return new_template


@router.post("/{template_id}/rollback", response_model=schemas.TemplateResponse)
def rollback_template(template_id: str, db: Session = Depends(get_db)):
 
    template = db.query(models.Template).filter(models.Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

  
    prev_template = (
        db.query(models.Template)
        .filter(
            models.Template.name == template.name,
            models.Template.version == template.version - 1
        )
        .first()
    )

    if not prev_template:
        raise HTTPException(status_code=404, detail="No previous version to rollback to")

  
    rollback_template = models.Template(
        id=str(uuid4()),
        name=template.name,
        content=prev_template.content,
        version=template.version + 1,
        updated_at=datetime.utcnow()
    )

    db.add(rollback_template)
    db.commit()
    db.refresh(rollback_template)

    # Update cache
    invalidate_cache(template_id)
    cache_template(str(rollback_template.id), schemas.TemplateResponse.from_orm(rollback_template).dict())

    return rollback_template