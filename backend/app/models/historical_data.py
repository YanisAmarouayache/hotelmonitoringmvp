from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.sql import func
from app.database import Base
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

# SQLAlchemy Model
class HistoricalData(Base):
    __tablename__ = "historical_data"

    id = Column(Integer, primary_key=True, index=True)
    hotel_name = Column(String, nullable=False)
    check_in_date = Column(DateTime, nullable=False)
    check_out_date = Column(DateTime, nullable=False)
    price = Column(Float, nullable=False)
    currency = Column(String, default="EUR")
    room_type = Column(String)
    board_type = Column(String)
    occupancy_rate = Column(Float)  # Percentage of rooms occupied
    booking_date = Column(DateTime)  # When the booking was made
    revenue = Column(Float)
    cost_per_night = Column(Float)
    profit_margin = Column(Float)
    season = Column(String)  # high, low, shoulder
    event_impact = Column(Float, default=0.0)  # Impact of events on pricing
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class YieldStrategy(Base):
    __tablename__ = "yield_strategies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    criteria_weights = Column(JSON)  # Store season-based weights
    min_price = Column(Float)
    max_price = Column(Float)
    target_occupancy = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Integer, default=1)

# Pydantic Models for API
class HistoricalDataBase(BaseModel):
    hotel_name: str
    check_in_date: datetime
    check_out_date: datetime
    price: float
    currency: str = "EUR"
    room_type: Optional[str] = None
    board_type: Optional[str] = None
    occupancy_rate: Optional[float] = None
    booking_date: Optional[datetime] = None
    revenue: Optional[float] = None
    cost_per_night: Optional[float] = None
    profit_margin: Optional[float] = None
    season: Optional[str] = None
    event_impact: float = 0.0

class HistoricalDataCreate(HistoricalDataBase):
    pass

class HistoricalDataResponse(HistoricalDataBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class YieldStrategyBase(BaseModel):
    name: str
    description: Optional[str] = None
    criteria_weights: Dict[str, Any]
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    target_occupancy: Optional[float] = None

class YieldStrategyCreate(YieldStrategyBase):
    pass

class YieldStrategyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    criteria_weights: Optional[Dict[str, Any]] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    target_occupancy: Optional[float] = None
    is_active: Optional[bool] = None

class YieldStrategyResponse(YieldStrategyBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool

    class Config:
        from_attributes = True

class BookingCurveData(BaseModel):
    days_before_checkin: int
    booking_count: int
    average_price: float
    occupancy_rate: float

class MarketAnalysis(BaseModel):
    competitor_count: int
    average_market_price: float
    price_percentile: float  # Where your hotel stands in the market
    recommended_price: float
    confidence_score: float

class YieldRecommendation(BaseModel):
    recommendation_type: str  # "raise_price", "lower_price", "maintain", "discount"
    reasoning: str
    suggested_price: Optional[float] = None
    confidence_score: float
    factors: List[str]
    market_analysis: Optional[MarketAnalysis] = None 