from fastapi import FastAPI
from notifications import router as notifications_router
from schemas import StandardResponse

app = FastAPI(title="API Gateway Service")

app.include_router(notifications_router, prefix="/notifications")

@app.get("/health", response_model=StandardResponse)
def health_check():
    return StandardResponse(success=True, message="API Gateway is healthy")
