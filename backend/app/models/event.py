from sqlalchemy import Column, Integer, String, DateTime, Text, Float
from sqlalchemy.sql import func
from app.database import Base
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# SQLAlchemy Model
class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    city = Column(String, nullable=False)
    country = Column(String)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    event_type = Column(String)  # conference, festival, sports, etc.
    expected_attendance = Column(Integer)
    impact_score = Column(Float, default=1.0)  # 0.0 to 2.0 scale
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# Pydantic Models for API
class EventBase(BaseModel):
    name: str
    city: str
    country: Optional[str] = None
    start_date: datetime
    end_date: datetime
    event_type: Optional[str] = None
    expected_attendance: Optional[int] = None
    impact_score: float = 1.0
    description: Optional[str] = None

class EventCreate(EventBase):
    pass

class EventUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    event_type: Optional[str] = None
    expected_attendance: Optional[int] = None
    impact_score: Optional[float] = None
    description: Optional[str] = None

class EventResponse(EventBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True 