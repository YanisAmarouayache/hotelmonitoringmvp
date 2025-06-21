from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from app.database import get_db
from app.models.hotel import Hotel, HotelPrice
from app.models.historical_data import HistoricalData

router = APIRouter()

@router.get("/price-evolution/{hotel_id}")
async def get_price_evolution(
    hotel_id: int,
    days_back: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get price evolution for a specific hotel."""
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    
    # Get price data
    cutoff_date = datetime.now() - timedelta(days=days_back)
    prices = db.query(HotelPrice).filter(
        HotelPrice.hotel_id == hotel_id,
        HotelPrice.scraped_at >= cutoff_date
    ).order_by(HotelPrice.scraped_at).all()
    
    # Format data for charts
    price_data = []
    for price in prices:
        price_data.append({
            'date': price.scraped_at.strftime('%Y-%m-%d'),
            'price': price.price,
            'currency': price.currency,
            'check_in_date': price.check_in_date.strftime('%Y-%m-%d'),
            'check_out_date': price.check_out_date.strftime('%Y-%m-%d')
        })
    
    return {
        'hotel_id': hotel_id,
        'hotel_name': hotel.name,
        'price_evolution': price_data,
        'total_records': len(price_data)
    }

@router.get("/market-comparison")
async def get_market_comparison(
    city: str,
    check_in_date: Optional[str] = None,
    check_out_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Compare hotel prices in a specific city."""
    query = db.query(Hotel).filter(
        Hotel.city.ilike(f"%{city}%"),
        Hotel.is_active == True
    )
    
    hotels = query.all()
    
    if not hotels:
        raise HTTPException(status_code=404, detail=f"No hotels found in {city}")
    
    # Get latest prices for each hotel
    market_data = []
    for hotel in hotels:
        price_query = db.query(HotelPrice).filter(HotelPrice.hotel_id == hotel.id)
        
        if check_in_date:
            check_in_dt = datetime.strptime(check_in_date, '%Y-%m-%d')
            price_query = price_query.filter(HotelPrice.check_in_date >= check_in_dt)
        
        if check_out_date:
            check_out_dt = datetime.strptime(check_out_date, '%Y-%m-%d')
            price_query = price_query.filter(HotelPrice.check_out_date <= check_out_dt)
        
        latest_price = price_query.order_by(desc(HotelPrice.scraped_at)).first()
        
        if latest_price:
            market_data.append({
                'hotel_id': hotel.id,
                'hotel_name': hotel.name,
                'star_rating': hotel.star_rating,
                'user_rating': hotel.user_rating,
                'price': latest_price.price,
                'currency': latest_price.currency,
                'amenities': hotel.amenities,
                'address': hotel.address
            })
    
    # Calculate market statistics
    if market_data:
        prices = [item['price'] for item in market_data if item['price']]
        avg_price = np.mean(prices) if prices else 0
        min_price = np.min(prices) if prices else 0
        max_price = np.max(prices) if prices else 0
        
        return {
            'city': city,
            'hotels_count': len(market_data),
            'market_stats': {
                'average_price': round(avg_price, 2),
                'min_price': round(min_price, 2),
                'max_price': round(max_price, 2),
                'price_range': round(max_price - min_price, 2)
            },
            'hotels': market_data
        }
    
    return {
        'city': city,
        'hotels_count': 0,
        'market_stats': {},
        'hotels': []
    }

@router.get("/price-trends")
async def get_price_trends(
    hotel_ids: List[int] = Query([]),
    days_back: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get price trends for multiple hotels."""
    if not hotel_ids:
        raise HTTPException(status_code=400, detail="At least one hotel ID is required")
    
    cutoff_date = datetime.now() - timedelta(days=days_back)
    
    trends_data = []
    for hotel_id in hotel_ids:
        hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
        if not hotel:
            continue
        
        prices = db.query(HotelPrice).filter(
            HotelPrice.hotel_id == hotel_id,
            HotelPrice.scraped_at >= cutoff_date
        ).order_by(HotelPrice.scraped_at).all()
        
        if prices:
            price_values = [p.price for p in prices]
            trend_data = {
                'hotel_id': hotel_id,
                'hotel_name': hotel.name,
                'price_trend': {
                    'current_price': price_values[-1],
                    'price_change': round(price_values[-1] - price_values[0], 2),
                    'price_change_percent': round(((price_values[-1] - price_values[0]) / price_values[0]) * 100, 2) if price_values[0] > 0 else 0,
                    'volatility': round(np.std(price_values), 2),
                    'data_points': len(price_values)
                },
                'prices': [
                    {
                        'date': p.scraped_at.strftime('%Y-%m-%d'),
                        'price': p.price,
                        'currency': p.currency
                    } for p in prices
                ]
            }
            trends_data.append(trend_data)
    
    return {
        'analysis_period_days': days_back,
        'hotels_analyzed': len(trends_data),
        'trends': trends_data
    }

@router.get("/occupancy-analysis")
async def get_occupancy_analysis(
    hotel_name: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Analyze occupancy patterns for a hotel using historical data."""
    query = db.query(HistoricalData).filter(
        HistoricalData.hotel_name.ilike(f"%{hotel_name}%")
    )
    
    if start_date:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        query = query.filter(HistoricalData.check_in_date >= start_dt)
    
    if end_date:
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        query = query.filter(HistoricalData.check_in_date <= end_dt)
    
    historical_data = query.all()
    
    if not historical_data:
        raise HTTPException(status_code=404, detail=f"No historical data found for {hotel_name}")
    
    # Analyze occupancy patterns
    occupancy_data = []
    for record in historical_data:
        occupancy_data.append({
            'date': record.check_in_date.strftime('%Y-%m-%d'),
            'occupancy_rate': record.occupancy_rate,
            'price': record.price,
            'season': record.season,
            'booking_date': record.booking_date.strftime('%Y-%m-%d') if record.booking_date else None
        })
    
    # Calculate booking curve (days between booking and check-in)
    booking_curves = []
    for record in historical_data:
        if record.booking_date and record.check_in_date:
            days_before = (record.check_in_date - record.booking_date).days
            if days_before >= 0:
                booking_curves.append({
                    'days_before_checkin': days_before,
                    'occupancy_rate': record.occupancy_rate,
                    'price': record.price
                })
    
    # Group by days before check-in
    if booking_curves:
        df = pd.DataFrame(booking_curves)
        curve_analysis = df.groupby('days_before_checkin').agg({
            'occupancy_rate': ['mean', 'std'],
            'price': ['mean', 'std']
        }).reset_index()
        
        curve_data = []
        for _, row in curve_analysis.iterrows():
            curve_data.append({
                'days_before_checkin': int(row['days_before_checkin']),
                'avg_occupancy': round(row[('occupancy_rate', 'mean')], 2),
                'avg_price': round(row[('price', 'mean')], 2)
            })
    else:
        curve_data = []
    
    return {
        'hotel_name': hotel_name,
        'total_records': len(historical_data),
        'occupancy_data': occupancy_data,
        'booking_curve': curve_data
    }

@router.get("/seasonal-analysis")
async def get_seasonal_analysis(
    city: str,
    year: int = Query(2024),
    db: Session = Depends(get_db)
):
    """Analyze seasonal pricing patterns for a city."""
    # Get hotels in the city
    hotels = db.query(Hotel).filter(
        Hotel.city.ilike(f"%{city}%"),
        Hotel.is_active == True
    ).all()
    
    if not hotels:
        raise HTTPException(status_code=404, detail=f"No hotels found in {city}")
    
    hotel_ids = [hotel.id for hotel in hotels]
    
    # Get price data for the year
    start_date = datetime(year, 1, 1)
    end_date = datetime(year, 12, 31)
    
    prices = db.query(HotelPrice).filter(
        HotelPrice.hotel_id.in_(hotel_ids),
        HotelPrice.check_in_date >= start_date,
        HotelPrice.check_in_date <= end_date
    ).all()
    
    if not prices:
        return {
            'city': city,
            'year': year,
            'message': 'No price data available for the specified period'
        }
    
    # Group by month
    monthly_data = {}
    for price in prices:
        month = price.check_in_date.month
        if month not in monthly_data:
            monthly_data[month] = []
        monthly_data[month].append(price.price)
    
    # Calculate monthly statistics
    seasonal_analysis = []
    for month in range(1, 13):
        if month in monthly_data:
            prices_month = monthly_data[month]
            seasonal_analysis.append({
                'month': month,
                'month_name': datetime(year, month, 1).strftime('%B'),
                'average_price': round(np.mean(prices_month), 2),
                'min_price': round(np.min(prices_month), 2),
                'max_price': round(np.max(prices_month), 2),
                'price_count': len(prices_month)
            })
        else:
            seasonal_analysis.append({
                'month': month,
                'month_name': datetime(year, month, 1).strftime('%B'),
                'average_price': 0,
                'min_price': 0,
                'max_price': 0,
                'price_count': 0
            })
    
    return {
        'city': city,
        'year': year,
        'hotels_analyzed': len(hotels),
        'total_price_records': len(prices),
        'seasonal_analysis': seasonal_analysis
    } 