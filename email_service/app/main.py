from fastapi import FastAPI
from threading import Thread
from .consumer import start_consumer

app = FastAPI(title="Email Service", version="1.0.0")

@app.on_event("startup")
def startup_event():
    
    Thread(target=start_consumer, daemon=True).start()

@app.get("/api/v1/health")
def health_check():
    return {"status": "healthy", "service": "email_service", "version": "1.0.0"}
