from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, Boolean
from sqlalchemy.sql import func
from app.database import Base
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

# SQLAlchemy Model
class Hotel(Base):
    __tablename__ = "hotels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    booking_url = Column(String, unique=True, nullable=False)
    address = Column(String)
    city = Column(String)
    country = Column(String)
    star_rating = Column(Float)
    user_rating = Column(Float)
    user_rating_count = Column(Integer)
    amenities = Column(JSON)  # Store as JSON array
    latitude = Column(Float)
    longitude = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)

class HotelPrice(Base):
    __tablename__ = "hotel_prices"

    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(Integer, nullable=False)
    check_in_date = Column(DateTime, nullable=False)
    check_out_date = Column(DateTime, nullable=False)
    price = Column(Float, nullable=False)
    currency = Column(String, default="EUR")
    room_type = Column(String)
    board_type = Column(String)
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    source = Column(String, default="booking.com")

# Pydantic Models for API
class HotelBase(BaseModel):
    name: str
    booking_url: str
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    star_rating: Optional[float] = None
    user_rating: Optional[float] = None
    user_rating_count: Optional[int] = None
    amenities: Optional[List[str]] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class HotelCreate(HotelBase):
    is_active: bool = True

class HotelUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    star_rating: Optional[float] = None
    user_rating: Optional[float] = None
    user_rating_count: Optional[int] = None
    amenities: Optional[List[str]] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class HotelResponse(HotelBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool

    class Config:
        from_attributes = True

class HotelPriceBase(BaseModel):
    hotel_id: int
    check_in_date: datetime
    check_out_date: datetime
    price: float
    currency: str = "EUR"
    room_type: Optional[str] = None
    board_type: Optional[str] = None

class HotelPriceCreate(HotelPriceBase):
    pass

class HotelPriceResponse(HotelPriceBase):
    id: int
    scraped_at: datetime
    source: str

    class Config:
        from_attributes = True

class HotelWithPrices(HotelResponse):
    prices: List[HotelPriceResponse] = []

class ScrapingRequest(BaseModel):
    booking_url: str
    check_in_date: Optional[str] = None
    check_out_date: Optional[str] = None
    room_type: Optional[str] = None
    board_type: Optional[str] = None

class ScrapingResponse(BaseModel):
    success: bool
    hotel_data: Optional[HotelResponse] = None
    price_data: Optional[HotelPriceResponse] = None
    error: Optional[str] = None 