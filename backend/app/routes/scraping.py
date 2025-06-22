from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import sys
import os
import asyncio
import subprocess
import json
from pydantic import BaseModel

# Add the scraper directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'scraper'))

from booking_scraper import BookingScraper
from booking_playwright_final import BookingPlaywrightScraper
from app.database import get_db
from app.models.hotel import (
    Hotel, HotelPrice, HotelCreate, HotelPriceCreate, 
    ScrapingRequest, ScrapingResponse
)

router = APIRouter()

class UpdatePricesRequest(BaseModel):
    check_in_date: str
    check_out_date: str

class ScrapeDateRangeRequest(BaseModel):
    start_date: str
    end_date: str

class PlaywrightScrapeRequest(BaseModel):
    url: str

class PlaywrightScrapeResponse(BaseModel):
    success: bool
    data: dict = None
    error: str = None

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
        
        # If check-in and check-out dates are provided, automatically range scrape
        if request.check_in_date and request.check_out_date:
            print(f"Automatically range scraping for hotel {hotel.id} from {request.check_in_date} to {request.check_out_date}")
            
            # Call the range scraping function
            range_result = await scrape_date_range_internal(
                hotel_id=hotel.id,
                start_date=request.check_in_date,
                end_date=request.check_out_date,
                db=db
            )
            
            if range_result['success']:
                print(f"Range scraping completed: {range_result['results']}")
            else:
                print(f"Range scraping failed: {range_result['error']}")
        
        # Add guest information to response if available
        response_data = {
            'success': True,
            'hotel_data': hotel,
            'price_data': None  # Will be populated by range scraping
        }
        
        if scraped_data.get('guest_info'):
            response_data['guest_info'] = scraped_data['guest_info']
        
        return ScrapingResponse(**response_data)
        
    except Exception as e:
        return ScrapingResponse(
            success=False,
            error=str(e)
        )

async def scrape_date_range_internal(
    hotel_id: int,
    start_date: str,
    end_date: str,
    db: Session
):
    """Internal function for range scraping (used by hotel creation)."""
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        return {'success': False, 'error': 'Hotel not found'}
    
    try:
        # Parse dates
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Validate date range
        if start_dt >= end_dt:
            return {'success': False, 'error': 'Start date must be before end date'}
        
        # Calculate date range (max 30 days)
        date_range = (end_dt - start_dt).days
        if date_range > 30:
            return {'success': False, 'error': 'Date range cannot exceed 30 days'}
        
        scraper = BookingScraper()
        total_prices_added = 0
        total_prices_updated = 0
        successful_scrapes = 0
        failed_scrapes = 0
        
        # Iterate through each day in the range
        current_date = start_dt
        while current_date < end_dt:
            check_in = current_date.strftime('%Y-%m-%d')
            check_out = (current_date + timedelta(days=1)).strftime('%Y-%m-%d')
            
            print(f"Auto-scraping prices for {hotel.name}: {check_in} to {check_out}")
            
            try:
                url = scraper._add_dates_to_url(hotel.booking_url, check_in, check_out)
                scraped_data = scraper.extract_hotel_data(url, check_in, check_out)
                
                if 'error' in scraped_data:
                    print(f"Error auto-scraping {check_in}: {scraped_data['error']}")
                    failed_scrapes += 1
                    current_date += timedelta(days=1)
                    continue
                
                check_in_dt = datetime.strptime(check_in, '%Y-%m-%d')
                check_out_dt = datetime.strptime(check_out, '%Y-%m-%d')
                
                rooms_data = scraped_data.get('rooms_data', [])
                prices_added_for_date = 0
                prices_updated_for_date = 0
                
                if rooms_data:
                    for room_info in rooms_data:
                        try:
                            room_type = room_info.get('room_type')
                            price = room_info.get('price')
                            
                            if not room_type or not price:
                                continue
                            
                            # Check if price already exists
                            existing_price = db.query(HotelPrice).filter(
                                HotelPrice.hotel_id == hotel.id,
                                HotelPrice.check_in_date == check_in_dt,
                                HotelPrice.check_out_date == check_out_dt,
                                HotelPrice.room_type == room_type
                            ).first()
                            
                            if existing_price:
                                # Update existing price
                                existing_price.price = price
                                existing_price.currency = room_info.get('currency', 'EUR')
                                existing_price.board_type = room_info.get('board_type')
                                existing_price.scraped_at = datetime.now()
                                existing_price.source = 'booking.com'
                                prices_updated_for_date += 1
                            else:
                                # Create new price record
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
                                prices_added_for_date += 1
                        
                        except Exception as e:
                            print(f"Error processing room price for {check_in}: {e}")
                            continue
                    
                    if prices_added_for_date > 0 or prices_updated_for_date > 0:
                        successful_scrapes += 1
                        total_prices_added += prices_added_for_date
                        total_prices_updated += prices_updated_for_date
                else:
                    failed_scrapes += 1
                
                # Small delay
                import time
                time.sleep(1)
                
            except Exception as e:
                print(f"Error auto-scraping {check_in}: {e}")
                failed_scrapes += 1
            
            current_date += timedelta(days=1)
        
        db.commit()
        
        return {
            'success': True,
            'results': {
                'successful_scrapes': successful_scrapes,
                'failed_scrapes': failed_scrapes,
                'total_prices_added': total_prices_added,
                'total_prices_updated': total_prices_updated
            }
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

@router.post("/scrape-date-range/{hotel_id}")
async def scrape_date_range(
    hotel_id: int,
    request: ScrapeDateRangeRequest,
    db: Session = Depends(get_db)
):
    """Scrape daily prices for a hotel across a date range."""
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    
    try:
        # Parse dates
        start_date = datetime.strptime(request.start_date, '%Y-%m-%d')
        end_date = datetime.strptime(request.end_date, '%Y-%m-%d')
        
        # Validate date range
        if start_date >= end_date:
            return {
                'success': False,
                'error': 'Start date must be before end date'
            }
        
        # Calculate date range (max 30 days to avoid overwhelming the system)
        date_range = (end_date - start_date).days
        if date_range > 30:
            return {
                'success': False,
                'error': 'Date range cannot exceed 30 days'
            }
        
        scraper = BookingScraper()
        total_prices_added = 0
        total_prices_updated = 0
        successful_scrapes = 0
        failed_scrapes = 0
        
        # Iterate through each day in the range
        current_date = start_date
        while current_date < end_date:
            # For each day, scrape a 1-night stay starting from that day
            check_in = current_date.strftime('%Y-%m-%d')
            check_out = (current_date + timedelta(days=1)).strftime('%Y-%m-%d')
            
            print(f"Scraping prices for {hotel.name}: {check_in} to {check_out}")
            
            try:
                # Add dates to URL
                url = scraper._add_dates_to_url(hotel.booking_url, check_in, check_out)
                
                # Extract updated data
                scraped_data = scraper.extract_hotel_data(url, check_in, check_out)
                
                if 'error' in scraped_data:
                    print(f"Error scraping {check_in}: {scraped_data['error']}")
                    failed_scrapes += 1
                    current_date += timedelta(days=1)
                    continue
                
                check_in_dt = datetime.strptime(check_in, '%Y-%m-%d')
                check_out_dt = datetime.strptime(check_out, '%Y-%m-%d')
                
                # Add new price data for each room type
                rooms_data = scraped_data.get('rooms_data', [])
                prices_added_for_date = 0
                prices_updated_for_date = 0
                
                if rooms_data:
                    for room_info in rooms_data:
                        try:
                            room_type = room_info.get('room_type')
                            price = room_info.get('price')
                            
                            # Skip if no room type or price
                            if not room_type or not price:
                                print(f"Skipping room with missing data for {check_in}: {room_info}")
                                continue
                            
                            # Check if price already exists for this hotel, date, and room type
                            existing_price = db.query(HotelPrice).filter(
                                HotelPrice.hotel_id == hotel.id,
                                HotelPrice.check_in_date == check_in_dt,
                                HotelPrice.check_out_date == check_out_dt,
                                HotelPrice.room_type == room_type
                            ).first()
                            
                            if existing_price:
                                # Update existing price
                                existing_price.price = price
                                existing_price.currency = room_info.get('currency', 'EUR')
                                existing_price.board_type = room_info.get('board_type')
                                existing_price.scraped_at = datetime.now()
                                existing_price.source = 'booking.com'
                                prices_updated_for_date += 1
                                print(f"Updated price for {check_in}: {room_type} - {price} EUR")
                            else:
                                # Create new price record
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
                                prices_added_for_date += 1
                                print(f"Added price for {check_in}: {room_type} - {price} EUR")
                        
                        except Exception as e:
                            print(f"Error adding room price data for {check_in}: {e}")
                            continue
                    
                    if prices_added_for_date > 0 or prices_updated_for_date > 0:
                        successful_scrapes += 1
                        total_prices_added += prices_added_for_date
                        total_prices_updated += prices_updated_for_date
                        print(f"Successfully processed {prices_added_for_date} new and {prices_updated_for_date} updated prices for {check_in}")
                    else:
                        failed_scrapes += 1
                        print(f"No prices found for {check_in}")
                else:
                    failed_scrapes += 1
                    print(f"No room data found for {check_in}")
                
                # Small delay to be respectful to the server
                import time
                time.sleep(1)
                
            except Exception as e:
                print(f"Error scraping {check_in}: {e}")
                failed_scrapes += 1
            
            current_date += timedelta(days=1)
        
        # Commit all changes
        db.commit()
        
        return {
            'success': True,
            'message': f'Successfully scraped prices for {hotel.name}',
            'date_range': {
                'start_date': request.start_date,
                'end_date': request.end_date,
                'total_days': date_range
            },
            'results': {
                'successful_scrapes': successful_scrapes,
                'failed_scrapes': failed_scrapes,
                'total_prices_added': total_prices_added,
                'total_prices_updated': total_prices_updated
            }
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

@router.post("/playwright-scrape", response_model=PlaywrightScrapeResponse)
async def playwright_scrape(request: PlaywrightScrapeRequest):
    """Scrape Booking.com hotel pricing using Playwright via worker process."""
    try:
        print(f"Starting Playwright scrape for URL: {request.url}")
        
        # Utiliser le worker script pour éviter les problèmes d'event loop
        worker_script = os.path.join(os.path.dirname(__file__), '..', '..', 'playwright_worker.py')
        
        result = subprocess.run(
            [sys.executable, worker_script, request.url],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__)
        )
        
        if result.returncode == 0:
            scraper_result = json.loads(result.stdout.strip())
            print(f"Scraping completed, success: {scraper_result.get('success')}")
            
            if scraper_result.get("success"):
                # Simplifier les données pour éviter les problèmes de sérialisation
                simplified_data = {
                    "hotel_url": scraper_result.get("hotel_url"),
                    "total_days": scraper_result.get("total_days", 0),
                    "scraped_at": scraper_result.get("scraped_at"),
                    "raw_responses_count": scraper_result.get("raw_responses_count", 0)
                }
                
                # Ajouter quelques exemples de prix si disponibles
                pricing_data = scraper_result.get("pricing_data", {})
                if pricing_data and "days" in pricing_data:
                    days = pricing_data["days"]
                    if days:
                        simplified_data["sample_prices"] = [
                            {
                                "checkin": day.get("checkin"),
                                "price": day.get("price"),
                                "price_formatted": day.get("price_formatted")
                            }
                            for day in days[:5]  # Juste les 5 premiers
                        ]
                
                return PlaywrightScrapeResponse(success=True, data=simplified_data)
            else:
                error_msg = scraper_result.get("error", "Unknown error")
                print(f"Scraping failed: {error_msg}")
                return PlaywrightScrapeResponse(success=False, error=error_msg)
        else:
            error_msg = f"Worker process failed: {result.stderr}"
            print(f"Worker error: {error_msg}")
            return PlaywrightScrapeResponse(success=False, error=error_msg)
            
    except Exception as e:
        print(f"Exception in playwright_scrape: {e}")
        import traceback
        traceback.print_exc()
        return PlaywrightScrapeResponse(success=False, error=str(e))

@router.get("/status")
async def get_scraping_status():
    """Get scraping service status."""
    return {
        'status': 'operational',
        'service': 'hotel-scraper',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    } 