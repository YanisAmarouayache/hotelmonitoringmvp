from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.models.hotel import (
    Hotel, HotelPrice, HotelCreate, HotelUpdate, HotelResponse, 
    HotelPriceCreate, HotelPriceResponse, HotelWithPrices
)

router = APIRouter()

@router.get("/", response_model=List[HotelResponse])
async def get_hotels(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    city: Optional[str] = None,
    active_only: bool = Query(True),  # Changed back to True so deleted hotels don't show
    db: Session = Depends(get_db)
):
    """Get all hotels with optional filtering."""
    query = db.query(Hotel)
    
    if active_only:
        query = query.filter(Hotel.is_active == True)
    
    if city:
        query = query.filter(Hotel.city.ilike(f"%{city}%"))
    
    hotels = query.offset(skip).limit(limit).all()
    print(f"GET /api/hotels - Found {len(hotels)} hotels in database")
    print(f"active_only filter: {active_only}")
    for hotel in hotels:
        print(f"  - Hotel: {hotel.name} (ID: {hotel.id}, Active: {hotel.is_active})")
    return hotels

@router.get("/{hotel_id}", response_model=HotelResponse)
async def get_hotel(hotel_id: int, db: Session = Depends(get_db)):
    """Get a specific hotel by ID."""
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    return hotel

@router.post("/", response_model=HotelResponse)
async def create_hotel(hotel_data: HotelCreate, db: Session = Depends(get_db)):
    """Create a new hotel."""
    # Check if hotel with same URL already exists
    existing_hotel = db.query(Hotel).filter(Hotel.booking_url == hotel_data.booking_url).first()
    if existing_hotel:
        raise HTTPException(status_code=400, detail="Hotel with this URL already exists")
    
    # Ensure hotel is created as active
    hotel_dict = hotel_data.dict()
    hotel_dict['is_active'] = True
    
    db_hotel = Hotel(**hotel_dict)
    db.add(db_hotel)
    db.commit()
    db.refresh(db_hotel)
    return db_hotel

@router.put("/{hotel_id}", response_model=HotelResponse)
async def update_hotel(
    hotel_id: int, 
    hotel_data: HotelUpdate, 
    db: Session = Depends(get_db)
):
    """Update a hotel."""
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    
    # Update only provided fields
    update_data = hotel_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(hotel, field, value)
    
    db.commit()
    db.refresh(hotel)
    return hotel

@router.delete("/{hotel_id}")
async def delete_hotel(hotel_id: int, db: Session = Depends(get_db)):
    """Permanently delete a hotel and all its associated data."""
    print(f"DELETE request for hotel ID: {hotel_id}")
    
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        print(f"Hotel with ID {hotel_id} not found")
        raise HTTPException(status_code=404, detail="Hotel not found")
    
    print(f"Found hotel: {hotel.name} (ID: {hotel.id}) - will be permanently deleted")
    
    # Delete all associated price data first
    price_count = db.query(HotelPrice).filter(HotelPrice.hotel_id == hotel_id).count()
    db.query(HotelPrice).filter(HotelPrice.hotel_id == hotel_id).delete()
    print(f"Deleted {price_count} price records for hotel {hotel_id}")
    
    # Delete the hotel
    db.delete(hotel)
    db.commit()
    
    print(f"Hotel {hotel.name} (ID: {hotel_id}) permanently deleted from database")
    
    # Check total hotels after deletion
    total_hotels = db.query(Hotel).count()
    active_hotels = db.query(Hotel).filter(Hotel.is_active == True).count()
    print(f"After deletion - Total hotels: {total_hotels}, Active hotels: {active_hotels}")
    
    return {"message": "Hotel permanently deleted successfully"}

@router.get("/{hotel_id}/prices", response_model=List[HotelPriceResponse])
async def get_hotel_prices(
    hotel_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get price history for a specific hotel."""
    query = db.query(HotelPrice).filter(HotelPrice.hotel_id == hotel_id)
    
    if start_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        query = query.filter(HotelPrice.check_in_date >= start_dt)
    
    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        query = query.filter(HotelPrice.check_in_date <= end_dt)
    
    prices = query.order_by(HotelPrice.check_in_date.desc()).all()
    return prices

@router.post("/{hotel_id}/prices", response_model=HotelPriceResponse)
async def add_hotel_price(
    hotel_id: int,
    price_data: HotelPriceCreate,
    db: Session = Depends(get_db)
):
    """Add a new price record for a hotel."""
    # Verify hotel exists
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    
    db_price = HotelPrice(**price_data.dict())
    db.add(db_price)
    db.commit()
    db.refresh(db_price)
    return db_price

@router.get("/{hotel_id}/with-prices", response_model=HotelWithPrices)
async def get_hotel_with_prices(
    hotel_id: int,
    days_back: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get hotel with recent price data grouped by room type."""
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    
    # Get recent prices
    cutoff_date = datetime.now() - timedelta(days=days_back)
    prices = db.query(HotelPrice).filter(
        HotelPrice.hotel_id == hotel_id,
        HotelPrice.scraped_at >= cutoff_date
    ).order_by(HotelPrice.check_in_date.desc(), HotelPrice.scraped_at.desc()).all()
    
    return HotelWithPrices(
        **hotel.__dict__,
        prices=prices
    )

@router.get("/cities/list")
async def get_cities(db: Session = Depends(get_db)):
    """Get list of all cities with hotels."""
    cities = db.query(Hotel.city).filter(
        Hotel.city.isnot(None),
        Hotel.is_active == True
    ).distinct().all()
    
    return [city[0] for city in cities if city[0]]

@router.get("/stats/overview")
async def get_hotels_overview(db: Session = Depends(get_db)):
    """Get overview statistics for hotels."""
    total_hotels = db.query(Hotel).count()
    active_hotels = db.query(Hotel).count()  # All hotels are active now
    
    # Get average ratings
    avg_rating = db.query(Hotel.user_rating).filter(
        Hotel.user_rating.isnot(None)
    ).all()
    avg_rating = sum(r[0] for r in avg_rating) / len(avg_rating) if avg_rating else 0
    
    # Get cities count
    cities_count = db.query(Hotel.city).filter(
        Hotel.city.isnot(None)
    ).distinct().count()
    
    return {
        "total_hotels": total_hotels,
        "active_hotels": active_hotels,
        "average_rating": round(avg_rating, 2),
        "cities_count": cities_count
    }

@router.post("/test-create")
def test_create_hotel(db: Session = Depends(get_db)):
    """Test endpoint to create a hotel manually."""
    try:
        # Create a test hotel
        test_hotel = Hotel(
            name="Test Hotel",
            booking_url="https://www.booking.com/test",
            address="123 Test Street",
            city="Test City",
            country="Test Country",
            star_rating=4,
            user_rating=8.5,
            user_rating_count=100,
            amenities=["WiFi", "Pool"],
            latitude=40.7128,
            longitude=-74.0060
        )
        
        print(f"Creating test hotel: {test_hotel.name}")
        db.add(test_hotel)
        db.commit()
        db.refresh(test_hotel)
        print(f"Test hotel created with ID: {test_hotel.id}")
        
        # Verify it was saved
        saved_hotel = db.query(Hotel).filter(Hotel.id == test_hotel.id).first()
        print(f"Verification - saved test hotel: {saved_hotel.name if saved_hotel else 'NOT FOUND'}")
        
        # Check total hotels
        total_hotels = db.query(Hotel).count()
        print(f"Total hotels in database: {total_hotels}")
        
        return {
            "success": True,
            "hotel_id": test_hotel.id,
            "total_hotels": total_hotels,
            "message": "Test hotel created successfully"
        }
    except Exception as e:
        print(f"Error creating test hotel: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/debug")
def debug_database(db: Session = Depends(get_db)):
    """Debug endpoint to show all hotels in database."""
    try:
        # Get all hotels (including inactive ones)
        all_hotels = db.query(Hotel).all()
        
        # Get active hotels only
        active_hotels = db.query(Hotel).filter(Hotel.is_active == True).all()
        
        # Get total count
        total_count = db.query(Hotel).count()
        active_count = db.query(Hotel).filter(Hotel.is_active == True).count()
        
        debug_info = {
            "total_hotels": total_count,
            "active_hotels": active_count,
            "all_hotels": [
                {
                    "id": hotel.id,
                    "name": hotel.name,
                    "booking_url": hotel.booking_url,
                    "city": hotel.city,
                    "country": hotel.country,
                    "is_active": hotel.is_active,
                    "created_at": hotel.created_at.isoformat() if hotel.created_at else None,
                    "user_rating": hotel.user_rating,
                    "star_rating": hotel.star_rating
                }
                for hotel in all_hotels
            ],
            "active_hotels_only": [
                {
                    "id": hotel.id,
                    "name": hotel.name,
                    "booking_url": hotel.booking_url,
                    "city": hotel.city,
                    "country": hotel.country,
                    "is_active": hotel.is_active,
                    "created_at": hotel.created_at.isoformat() if hotel.created_at else None,
                    "user_rating": hotel.user_rating,
                    "star_rating": hotel.star_rating
                }
                for hotel in active_hotels
            ]
        }
        
        return debug_info
        
    except Exception as e:
        return {"error": str(e), "traceback": str(e.__traceback__)}

@router.get("/test-db")
def test_database(db: Session = Depends(get_db)):
    """Test database connection and show basic info."""
    try:
        # Test basic query
        hotel_count = db.query(Hotel).count()
        
        # Test if we can access the database
        result = db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        tables = [row[0] for row in result]
        
        return {
            "status": "Database connection successful",
            "tables": tables,
            "hotel_count": hotel_count,
            "database_file": "hotel_monitoring.db"
        }
        
    except Exception as e:
        return {"error": str(e)}

@router.get("/check-state")
def check_hotel_state(db: Session = Depends(get_db)):
    """Check the current state of hotels in the database."""
    try:
        # Get all hotels
        all_hotels = db.query(Hotel).all()
        
        # Get active hotels
        active_hotels = db.query(Hotel).filter(Hotel.is_active == True).all()
        
        # Get inactive hotels
        inactive_hotels = db.query(Hotel).filter(Hotel.is_active == False).all()
        
        # Check the most recent hotel
        recent_hotel = db.query(Hotel).order_by(Hotel.created_at.desc()).first()
        
        state_info = {
            "total_hotels": len(all_hotels),
            "active_hotels": len(active_hotels),
            "inactive_hotels": len(inactive_hotels),
            "all_hotels": [
                {
                    "id": hotel.id,
                    "name": hotel.name,
                    "is_active": hotel.is_active,
                    "created_at": hotel.created_at.isoformat() if hotel.created_at else None,
                    "booking_url": hotel.booking_url
                }
                for hotel in all_hotels
            ],
            "recent_hotel": {
                "id": recent_hotel.id,
                "name": recent_hotel.name,
                "is_active": recent_hotel.is_active,
                "created_at": recent_hotel.created_at.isoformat() if recent_hotel.created_at else None
            } if recent_hotel else None
        }
        
        return state_info
        
    except Exception as e:
        return {"error": str(e)}

@router.post("/activate-all")
def activate_all_hotels(db: Session = Depends(get_db)):
    """Activate all hotels in the database."""
    try:
        # Get all hotels
        all_hotels = db.query(Hotel).all()
        
        if not all_hotels:
            return {"message": "No hotels found in database"}
        
        # Set all to active
        for hotel in all_hotels:
            hotel.is_active = True
        
        db.commit()
        
        return {
            "message": f"Activated {len(all_hotels)} hotels",
            "hotels": [
                {
                    "id": hotel.id,
                    "name": hotel.name,
                    "is_active": hotel.is_active
                }
                for hotel in all_hotels
            ]
        }
        
    except Exception as e:
        return {"error": str(e)} 