from sqlalchemy import Column, String, DateTime
from datetime import datetime
from .database import Base

class EmailStatus(Base):
    __tablename__ = "email_status"
    
    request_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, index=True)
    status = Column(String, default="pending")  
    error = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
