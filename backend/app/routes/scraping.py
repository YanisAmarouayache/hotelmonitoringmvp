from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import sys
import os

# Add the scraper directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'scraper'))

from booking_scraper import BookingScraper
from app.database import get_db
from app.models.hotel import (
    Hotel, HotelPrice, HotelCreate, HotelPriceCreate, 
    ScrapingRequest, ScrapingResponse
)

router = APIRouter()

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
        
        # Add price data if available
        price_data = None
        if scraped_data.get('price'):
            # Use extracted dates from URL if available
            check_in = request.check_in_date or scraped_data.get('check_in_date')
            check_out = request.check_out_date or scraped_data.get('check_out_date')
            
            price_data = HotelPrice(
                hotel_id=hotel.id,
                check_in_date=datetime.strptime(check_in, '%Y-%m-%d') if check_in else datetime.now(),
                check_out_date=datetime.strptime(check_out, '%Y-%m-%d') if check_out else datetime.now() + timedelta(days=1),
                price=scraped_data['price'],
                currency=scraped_data.get('currency', 'EUR'),
                room_type=scraped_data.get('room_type') or request.room_type,
                board_type=scraped_data.get('board_type') or request.board_type
            )
            db.add(price_data)
            db.commit()
            db.refresh(price_data)
        
        # Add multiple room options if available
        rooms_data = scraped_data.get('rooms_data', [])
        added_rooms = []
        if rooms_data:
            # Use extracted dates from URL if available
            check_in = request.check_in_date or scraped_data.get('check_in_date')
            check_out = request.check_out_date or scraped_data.get('check_out_date')
            
            for room_info in rooms_data:
                try:
                    # Validate room data before adding
                    room_type = room_info.get('room_type')
                    price = room_info.get('price')
                    
                    # Skip if room type is invalid or contains error messages
                    if room_type and any(error_text in room_type.lower() for error_text in [
                        'something went wrong',
                        'please try again',
                        'error',
                        'loading',
                        'unavailable'
                    ]):
                        print(f"Skipping invalid room type: {room_type}")
                        continue
                    
                    # Skip if no price and no valid room type
                    if not price and not room_type:
                        print(f"Skipping room with no price and no room type")
                        continue
                    
                    room_price = HotelPrice(
                        hotel_id=hotel.id,
                        check_in_date=datetime.strptime(check_in, '%Y-%m-%d') if check_in else datetime.now(),
                        check_out_date=datetime.strptime(check_out, '%Y-%m-%d') if check_out else datetime.now() + timedelta(days=1),
                        price=price,
                        currency=room_info.get('currency', 'EUR'),
                        room_type=room_type,
                        board_type=room_info.get('board_type')
                    )
                    db.add(room_price)
                    added_rooms.append(room_info)
                    print(f"Added room: {room_type} - {price} EUR")
                except Exception as e:
                    print(f"Error adding room price data: {e}")
                    continue
            
            db.commit()
            print(f"Added {len(added_rooms)} room options to database")
        
        # Add guest information to response if available
        response_data = {
            'success': True,
            'hotel_data': hotel,
            'price_data': price_data
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
    check_in_date: Optional[str] = None,
    check_out_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Update prices for an existing hotel."""
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    
    try:
        scraper = BookingScraper()
        
        # Add dates to URL if provided
        url = hotel.booking_url
        if check_in_date and check_out_date:
            url = scraper._add_dates_to_url(url, check_in_date, check_out_date)
        
        # Extract updated data
        scraped_data = scraper.extract_hotel_data(url, check_in_date, check_out_date)
        
        if 'error' in scraped_data:
            return {
                'success': False,
                'error': scraped_data['error']
            }
        
        # Add new price data
        price_data = None
        if scraped_data.get('price'):
            price_data = HotelPrice(
                hotel_id=hotel.id,
                check_in_date=datetime.strptime(check_in_date, '%Y-%m-%d') if check_in_date else datetime.now(),
                check_out_date=datetime.strptime(check_out_date, '%Y-%m-%d') if check_out_date else datetime.now() + timedelta(days=1),
                price=scraped_data['price'],
                currency=scraped_data.get('currency', 'EUR'),
                room_type=scraped_data.get('room_type'),
                board_type=scraped_data.get('board_type')
            )
            db.add(price_data)
            db.commit()
            db.refresh(price_data)
        
        # Add multiple room options if available
        rooms_data = scraped_data.get('rooms_data', [])
        added_rooms = []
        if rooms_data:
            for room_info in rooms_data:
                try:
                    # Validate room data before adding
                    room_type = room_info.get('room_type')
                    price = room_info.get('price')
                    
                    # Skip if room type is invalid or contains error messages
                    if room_type and any(error_text in room_type.lower() for error_text in [
                        'something went wrong',
                        'please try again',
                        'error',
                        'loading',
                        'unavailable'
                    ]):
                        print(f"Skipping invalid room type: {room_type}")
                        continue
                    
                    # Skip if no price and no valid room type
                    if not price and not room_type:
                        print(f"Skipping room with no price and no room type")
                        continue
                    
                    room_price = HotelPrice(
                        hotel_id=hotel.id,
                        check_in_date=datetime.strptime(check_in_date, '%Y-%m-%d') if check_in_date else datetime.now(),
                        check_out_date=datetime.strptime(check_out_date, '%Y-%m-%d') if check_out_date else datetime.now() + timedelta(days=1),
                        price=price,
                        currency=room_info.get('currency', 'EUR'),
                        room_type=room_type,
                        board_type=room_info.get('board_type')
                    )
                    db.add(room_price)
                    added_rooms.append(room_info)
                    print(f"Added room: {room_type} - {price} EUR")
                except Exception as e:
                    print(f"Error adding room price data: {e}")
                    continue
            
            db.commit()
            print(f"Added {len(added_rooms)} room options to database")
        
        return {
            'success': True,
            'message': f'Successfully updated prices for {hotel.name}',
            'price_data': price_data,
            'rooms_added': len(added_rooms)
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