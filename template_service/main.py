from fastapi import FastAPI
import templates
from database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Template Service")

app.include_router(templates.router)

@app.get("/")
def root():
    return {"message": "Template Service running"}
