from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import sys
import os
from pydantic import BaseModel

# Add the scraper directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'scraper'))

from booking_scraper import BookingScraper
from app.database import get_db
from app.models.hotel import (
    Hotel, HotelPrice, HotelCreate, HotelPriceCreate, 
    ScrapingRequest, ScrapingResponse
)

router = APIRouter()

class UpdatePricesRequest(BaseModel):
    check_in_date: str
    check_out_date: str

@router.post("/hotel", response_model=ScrapingResponse)
async def scrape_hotel(
    request: ScrapingRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Scrape hotel data from Booking.com URL."""
    try:
        scraper = BookingScraper()
        
        # Extract hotel data
        scraped_data = scraper.extract_hotel_data(
            url=request.booking_url,
            check_in_date=request.check_in_date,
            check_out_date=request.check_out_date
        )
        
        if 'error' in scraped_data:
            return ScrapingResponse(
                success=False,
                error=scraped_data['error']
            )
        
        # Debug: Log what type was detected
        print(f"DEBUG: Scraped data type: {scraped_data.get('type')}")
        print(f"DEBUG: Scraped data keys: {list(scraped_data.keys())}")
        
        # Individual hotel page
        # Check if hotel already exists
        existing_hotel = db.query(Hotel).filter(
            Hotel.booking_url == request.booking_url
        ).first()
        
        if existing_hotel:
            # Update existing hotel
            hotel = existing_hotel
            update_data = {
                'name': scraped_data.get('name'),
                'address': scraped_data.get('address'),
                'city': scraped_data.get('city'),
                'country': scraped_data.get('country'),
                'star_rating': scraped_data.get('star_rating'),
                'user_rating': scraped_data.get('user_rating'),
                'user_rating_count': scraped_data.get('user_rating_count'),
                'amenities': scraped_data.get('amenities'),
                'latitude': scraped_data.get('latitude'),
                'longitude': scraped_data.get('longitude')
            }
            
            for field, value in update_data.items():
                if value is not None:
                    setattr(hotel, field, value)
        else:
            # Create new hotel
            hotel_data = HotelCreate(
                name=scraped_data.get('name', 'Unknown Hotel'),
                booking_url=request.booking_url,
                address=scraped_data.get('address'),
                city=scraped_data.get('city'),
                country=scraped_data.get('country'),
                star_rating=scraped_data.get('star_rating'),
                user_rating=scraped_data.get('user_rating'),
                user_rating_count=scraped_data.get('user_rating_count'),
                amenities=scraped_data.get('amenities'),
                latitude=scraped_data.get('latitude'),
                longitude=scraped_data.get('longitude'),
                is_active=True  # Explicitly set as active
            )
            
            print(f"Creating new hotel: {hotel_data.name}")
            hotel = Hotel(**hotel_data.dict())
            db.add(hotel)
            print(f"Hotel created with ID: {hotel.id}")
            print(f"Hotel is_active status: {hotel.is_active}")
            
            # Verify hotel was saved
            saved_hotel = db.query(Hotel).filter(Hotel.id == hotel.id).first()
            print(f"Verification - saved hotel: {saved_hotel.name if saved_hotel else 'NOT FOUND'}")
            if saved_hotel:
                print(f"Verification - saved hotel is_active: {saved_hotel.is_active}")
            
            # Check total hotels in database
            total_hotels = db.query(Hotel).count()
            active_hotels = db.query(Hotel).filter(Hotel.is_active == True).count()
            print(f"Total hotels in database: {total_hotels}")
            print(f"Active hotels in database: {active_hotels}")
        
        db.commit()
        db.refresh(hotel)
        
        # Get dates for price records
        check_in = request.check_in_date or scraped_data.get('check_in_date')
        check_out = request.check_out_date or scraped_data.get('check_out_date')
        
        if not check_in or not check_out:
            return ScrapingResponse(
                success=False,
                error="Check-in and check-out dates are required for price scraping"
            )
        
        check_in_dt = datetime.strptime(check_in, '%Y-%m-%d')
        check_out_dt = datetime.strptime(check_out, '%Y-%m-%d')
        
        # Add price data for each room type found
        added_prices = []
        rooms_data = scraped_data.get('rooms_data', [])
        
        if rooms_data:
            for room_info in rooms_data:
                try:
                    room_type = room_info.get('room_type')
                    price = room_info.get('price')
                    
                    # Skip if no room type or price
                    if not room_type or not price:
                        print(f"Skipping room with missing data: {room_info}")
                        continue
                    
                    # Create price record
                    price_data = HotelPrice(
                        hotel_id=hotel.id,
                        room_type=room_type,
                        price=price,
                        currency=room_info.get('currency', 'EUR'),
                        check_in_date=check_in_dt,
                        check_out_date=check_out_dt,
                        board_type=room_info.get('board_type'),
                        source='booking.com'
                    )
                    db.add(price_data)
                    added_prices.append(price_data)
                    print(f"Added price: {room_type} - {price} EUR for {check_in}")
                
                except Exception as e:
                    print(f"Error adding room price data: {e}")
                    continue
            
            db.commit()
            print(f"Added {len(added_prices)} price records to database")
        
        # Add guest information to response if available
        response_data = {
            'success': True,
            'hotel_data': hotel,
            'price_data': added_prices[0] if added_prices else None
        }
        
        if scraped_data.get('guest_info'):
            response_data['guest_info'] = scraped_data['guest_info']
        
        return ScrapingResponse(**response_data)
        
    except Exception as e:
        return ScrapingResponse(
            success=False,
            error=str(e)
        )

@router.post("/update-prices/{hotel_id}")
async def update_hotel_prices(
    hotel_id: int,
    request: UpdatePricesRequest,
    db: Session = Depends(get_db)
):
    """Update prices for an existing hotel."""
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    
    try:
        scraper = BookingScraper()
        
        # Add dates to URL
        url = scraper._add_dates_to_url(hotel.booking_url, request.check_in_date, request.check_out_date)
        
        # Extract updated data
        scraped_data = scraper.extract_hotel_data(url, request.check_in_date, request.check_out_date)
        
        if 'error' in scraped_data:
            return {
                'success': False,
                'error': scraped_data['error']
            }
        
        check_in_dt = datetime.strptime(request.check_in_date, '%Y-%m-%d')
        check_out_dt = datetime.strptime(request.check_out_date, '%Y-%m-%d')
        
        # Add new price data for each room type
        added_prices = []
        rooms_data = scraped_data.get('rooms_data', [])
        
        if rooms_data:
            for room_info in rooms_data:
                try:
                    room_type = room_info.get('room_type')
                    price = room_info.get('price')
                    
                    # Skip if no room type or price
                    if not room_type or not price:
                        print(f"Skipping room with missing data: {room_info}")
                        continue
                    
                    # Create price record
                    price_data = HotelPrice(
                        hotel_id=hotel.id,
                        room_type=room_type,
                        price=price,
                        currency=room_info.get('currency', 'EUR'),
                        check_in_date=check_in_dt,
                        check_out_date=check_out_dt,
                        board_type=room_info.get('board_type'),
                        source='booking.com'
                    )
                    db.add(price_data)
                    added_prices.append(price_data)
                    print(f"Added price: {room_type} - {price} EUR for {request.check_in_date}")
                
                except Exception as e:
                    print(f"Error adding room price data: {e}")
                    continue
            
            db.commit()
            print(f"Added {len(added_prices)} price records to database")
        
        return {
            'success': True,
            'message': f'Successfully updated prices for {hotel.name}',
            'prices_added': len(added_prices)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

@router.get("/status")
async def get_scraping_status():
    """Get scraping service status."""
    return {
        'status': 'operational',
        'service': 'hotel-scraper',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    } 