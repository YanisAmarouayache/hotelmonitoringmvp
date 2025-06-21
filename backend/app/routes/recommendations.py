from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

from app.database import get_db
from app.models.hotel import Hotel, HotelPrice
from app.models.historical_data import HistoricalData, YieldStrategy
from app.models.event import Event
from app.models.historical_data import YieldRecommendation, MarketAnalysis

router = APIRouter()

@router.get("/yield-recommendation/{hotel_id}")
async def get_yield_recommendation(
    hotel_id: int,
    check_in_date: Optional[str] = None,
    check_out_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get yield management recommendations for a hotel."""
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    
    # Get competitor hotels in the same city
    competitors = db.query(Hotel).filter(
        Hotel.city == hotel.city,
        Hotel.id != hotel_id,
        Hotel.is_active == True
    ).all()
    
    if not competitors:
        return YieldRecommendation(
            recommendation_type="maintain",
            reasoning="No competitors found in the same city for comparison",
            confidence_score=0.5,
            factors=["No competitor data available"]
        )
    
    # Get latest prices for competitors
    competitor_prices = []
    for competitor in competitors:
        price_query = db.query(HotelPrice).filter(HotelPrice.hotel_id == competitor.id)
        
        if check_in_date:
            check_in_dt = datetime.strptime(check_in_date, '%Y-%m-%d')
            price_query = price_query.filter(HotelPrice.check_in_date >= check_in_dt)
        
        if check_out_date:
            check_out_dt = datetime.strptime(check_out_date, '%Y-%m-%d')
            price_query = price_query.filter(HotelPrice.check_out_date <= check_out_dt)
        
        latest_price = price_query.order_by(desc(HotelPrice.scraped_at)).first()
        if latest_price:
            competitor_prices.append({
                'hotel_id': competitor.id,
                'hotel_name': competitor.name,
                'star_rating': competitor.star_rating,
                'user_rating': competitor.user_rating,
                'price': latest_price.price,
                'currency': latest_price.currency
            })
    
    if not competitor_prices:
        return YieldRecommendation(
            recommendation_type="maintain",
            reasoning="No recent competitor price data available",
            confidence_score=0.5,
            factors=["No competitor price data"]
        )
    
    # Get your hotel's latest price
    your_price_query = db.query(HotelPrice).filter(HotelPrice.hotel_id == hotel_id)
    if check_in_date:
        check_in_dt = datetime.strptime(check_in_date, '%Y-%m-%d')
        your_price_query = your_price_query.filter(HotelPrice.check_in_date >= check_in_dt)
    
    your_latest_price = your_price_query.order_by(desc(HotelPrice.scraped_at)).first()
    
    if not your_latest_price:
        return YieldRecommendation(
            recommendation_type="maintain",
            reasoning="No recent price data for your hotel",
            confidence_score=0.3,
            factors=["No hotel price data available"]
        )
    
    # Calculate market analysis
    competitor_prices_list = [cp['price'] for cp in competitor_prices]
    avg_market_price = np.mean(competitor_prices_list)
    your_price = your_latest_price.price
    
    # Calculate percentile
    price_percentile = np.percentile(competitor_prices_list, 50)
    your_percentile = np.percentile([your_price] + competitor_prices_list, 50)
    
    # Check for events
    events = db.query(Event).filter(
        Event.city == hotel.city,
        Event.start_date <= datetime.now() + timedelta(days=30),
        Event.end_date >= datetime.now()
    ).all()
    
    event_impact = 0
    event_factors = []
    for event in events:
        days_until_event = (event.start_date - datetime.now()).days
        if days_until_event <= 7:
            event_impact += event.impact_score * 0.3
            event_factors.append(f"Major event: {event.name}")
        elif days_until_event <= 30:
            event_impact += event.impact_score * 0.1
            event_factors.append(f"Upcoming event: {event.name}")
    
    # Generate recommendation
    recommendation_type = "maintain"
    reasoning = ""
    suggested_price = None
    confidence_score = 0.7
    factors = []
    
    # Price positioning analysis
    if your_price < avg_market_price * 0.8:
        recommendation_type = "raise_price"
        reasoning = "Your hotel is significantly underpriced compared to competitors"
        suggested_price = avg_market_price * 0.9
        factors.append("Underpriced vs market average")
        confidence_score = 0.8
    elif your_price > avg_market_price * 1.2:
        recommendation_type = "lower_price"
        reasoning = "Your hotel is overpriced compared to competitors"
        suggested_price = avg_market_price * 1.1
        factors.append("Overpriced vs market average")
        confidence_score = 0.8
    
    # Event-based adjustments
    if event_impact > 0:
        if recommendation_type == "maintain":
            recommendation_type = "raise_price"
            reasoning = "Local events suggest opportunity for price increase"
            suggested_price = your_price * (1 + event_impact)
            factors.extend(event_factors)
            confidence_score = 0.7
        elif recommendation_type == "raise_price":
            suggested_price = suggested_price * (1 + event_impact)
            factors.extend(event_factors)
    
    # Seasonal adjustments
    current_month = datetime.now().month
    if current_month in [6, 7, 8]:  # Summer
        if recommendation_type == "maintain":
            recommendation_type = "raise_price"
            reasoning = "Summer season typically allows for higher pricing"
            suggested_price = your_price * 1.1
            factors.append("Summer season")
            confidence_score = 0.6
    elif current_month in [12, 1, 2]:  # Winter
        if recommendation_type == "maintain":
            recommendation_type = "lower_price"
            reasoning = "Winter season may require competitive pricing"
            suggested_price = your_price * 0.9
            factors.append("Winter season")
            confidence_score = 0.6
    
    market_analysis = MarketAnalysis(
        competitor_count=len(competitor_prices),
        average_market_price=round(avg_market_price, 2),
        price_percentile=round(your_percentile, 2),
        recommended_price=round(suggested_price, 2) if suggested_price else your_price,
        confidence_score=confidence_score
    )
    
    return YieldRecommendation(
        recommendation_type=recommendation_type,
        reasoning=reasoning,
        suggested_price=round(suggested_price, 2) if suggested_price else None,
        confidence_score=confidence_score,
        factors=factors,
        market_analysis=market_analysis
    )

@router.get("/booking-pace-analysis")
async def get_booking_pace_analysis(
    hotel_name: str,
    days_back: int = Query(90, ge=30, le=365),
    db: Session = Depends(get_db)
):
    """Analyze booking pace patterns for yield management."""
    # Get historical data
    cutoff_date = datetime.now() - timedelta(days=days_back)
    historical_data = db.query(HistoricalData).filter(
        HistoricalData.hotel_name.ilike(f"%{hotel_name}%"),
        HistoricalData.booking_date >= cutoff_date
    ).all()
    
    if not historical_data:
        raise HTTPException(status_code=404, detail=f"No historical data found for {hotel_name}")
    
    # Calculate booking curve
    booking_curves = []
    for record in historical_data:
        if record.booking_date and record.check_in_date:
            days_before = (record.check_in_date - record.booking_date).days
            if days_before >= 0:
                booking_curves.append({
                    'days_before_checkin': days_before,
                    'occupancy_rate': record.occupancy_rate,
                    'price': record.price,
                    'check_in_date': record.check_in_date
                })
    
    if not booking_curves:
        return {
            'hotel_name': hotel_name,
            'message': 'No booking curve data available'
        }
    
    # Group by days before check-in
    df = pd.DataFrame(booking_curves)
    curve_analysis = df.groupby('days_before_checkin').agg({
        'occupancy_rate': ['mean', 'std', 'count'],
        'price': ['mean', 'std']
    }).reset_index()
    
    # Calculate booking pace trends
    pace_analysis = []
    for _, row in curve_analysis.iterrows():
        days_before = int(row['days_before_checkin'])
        avg_occupancy = row[('occupancy_rate', 'mean')]
        booking_count = row[('occupancy_rate', 'count')]
        avg_price = row[('price', 'mean')]
        
        pace_analysis.append({
            'days_before_checkin': days_before,
            'avg_occupancy_rate': round(avg_occupancy, 2),
            'booking_count': int(booking_count),
            'avg_price': round(avg_price, 2)
        })
    
    # Sort by days before check-in
    pace_analysis.sort(key=lambda x: x['days_before_checkin'])
    
    # Calculate pace recommendations
    recent_bookings = [b for b in booking_curves if b['days_before_checkin'] <= 30]
    if recent_bookings:
        recent_avg_occupancy = np.mean([b['occupancy_rate'] for b in recent_bookings])
        recent_avg_price = np.mean([b['price'] for b in recent_bookings])
        
        # Compare with historical average
        historical_avg_occupancy = np.mean([b['occupancy_rate'] for b in booking_curves])
        historical_avg_price = np.mean([b['price'] for b in booking_curves])
        
        occupancy_trend = recent_avg_occupancy - historical_avg_occupancy
        price_trend = recent_avg_price - historical_avg_price
        
        if occupancy_trend < -0.1:  # 10% decrease
            pace_recommendation = "discount"
            pace_reasoning = "Recent booking pace is slower than historical average"
        elif occupancy_trend > 0.1:  # 10% increase
            pace_recommendation = "raise_price"
            pace_reasoning = "Recent booking pace is faster than historical average"
        else:
            pace_recommendation = "maintain"
            pace_reasoning = "Booking pace is within normal range"
    else:
        pace_recommendation = "maintain"
        pace_reasoning = "Insufficient recent booking data"
        occupancy_trend = 0
        price_trend = 0
    
    return {
        'hotel_name': hotel_name,
        'analysis_period_days': days_back,
        'total_bookings_analyzed': len(booking_curves),
        'booking_pace_analysis': pace_analysis,
        'pace_recommendation': {
            'recommendation': pace_recommendation,
            'reasoning': pace_reasoning,
            'occupancy_trend': round(occupancy_trend, 3),
            'price_trend': round(price_trend, 2)
        }
    }

@router.get("/seasonal-recommendations")
async def get_seasonal_recommendations(
    city: str,
    season: Optional[str] = Query(None, regex="^(spring|summer|autumn|winter)$"),
    db: Session = Depends(get_db)
):
    """Get seasonal pricing recommendations based on historical patterns."""
    # Get hotels in the city
    hotels = db.query(Hotel).filter(
        Hotel.city.ilike(f"%{city}%"),
        Hotel.is_active == True
    ).all()
    
    if not hotels:
        raise HTTPException(status_code=404, detail=f"No hotels found in {city}")
    
    hotel_ids = [hotel.id for hotel in hotels]
    
    # Define season months
    season_months = {
        'spring': [3, 4, 5],
        'summer': [6, 7, 8],
        'autumn': [9, 10, 11],
        'winter': [12, 1, 2]
    }
    
    # Get historical price data for the season
    if season:
        months = season_months[season]
        prices = db.query(HotelPrice).filter(
            HotelPrice.hotel_id.in_(hotel_ids),
            func.extract('month', HotelPrice.check_in_date).in_(months)
        ).all()
    else:
        # Get all seasonal data
        prices = db.query(HotelPrice).filter(
            HotelPrice.hotel_id.in_(hotel_ids)
        ).all()
    
    if not prices:
        return {
            'city': city,
            'season': season,
            'message': 'No price data available for analysis'
        }
    
    # Group by season and calculate statistics
    seasonal_stats = {}
    for price in prices:
        month = price.check_in_date.month
        current_season = None
        for s, months in season_months.items():
            if month in months:
                current_season = s
                break
        
        if current_season not in seasonal_stats:
            seasonal_stats[current_season] = []
        seasonal_stats[current_season].append(price.price)
    
    # Calculate seasonal recommendations
    recommendations = []
    for s, prices_list in seasonal_stats.items():
        if len(prices_list) < 10:  # Need minimum data points
            continue
        
        avg_price = np.mean(prices_list)
        std_price = np.std(prices_list)
        
        # Compare with other seasons
        other_seasons_avg = []
        for other_s, other_prices in seasonal_stats.items():
            if other_s != s and len(other_prices) >= 10:
                other_seasons_avg.append(np.mean(other_prices))
        
        if other_seasons_avg:
            overall_avg = np.mean(other_seasons_avg)
            price_multiplier = avg_price / overall_avg if overall_avg > 0 else 1.0
            
            if price_multiplier > 1.2:
                recommendation = "high_season"
                reasoning = f"{s.capitalize()} is a high-demand season"
            elif price_multiplier < 0.8:
                recommendation = "low_season"
                reasoning = f"{s.capitalize()} is a low-demand season"
            else:
                recommendation = "shoulder_season"
                reasoning = f"{s.capitalize()} is a moderate-demand season"
        else:
            recommendation = "moderate"
            reasoning = f"Insufficient data for {s} season comparison"
            price_multiplier = 1.0
        
        recommendations.append({
            'season': s,
            'average_price': round(avg_price, 2),
            'price_volatility': round(std_price, 2),
            'price_multiplier': round(price_multiplier, 2),
            'recommendation': recommendation,
            'reasoning': reasoning,
            'data_points': len(prices_list)
        })
    
    return {
        'city': city,
        'requested_season': season,
        'seasonal_recommendations': recommendations,
        'total_price_records': len(prices)
    }

@router.get("/amenity-impact-analysis")
async def get_amenity_impact_analysis(
    city: str,
    db: Session = Depends(get_db)
):
    """Analyze the impact of amenities on pricing."""
    hotels = db.query(Hotel).filter(
        Hotel.city.ilike(f"%{city}%"),
        Hotel.is_active == True,
        Hotel.amenities.isnot(None)
    ).all()
    
    if not hotels:
        raise HTTPException(status_code=404, detail=f"No hotels with amenity data found in {city}")
    
    # Get latest prices for each hotel
    hotel_data = []
    for hotel in hotels:
        latest_price = db.query(HotelPrice).filter(
            HotelPrice.hotel_id == hotel.id
        ).order_by(desc(HotelPrice.scraped_at)).first()
        
        if latest_price and hotel.amenities:
            hotel_data.append({
                'hotel_id': hotel.id,
                'hotel_name': hotel.name,
                'price': latest_price.price,
                'star_rating': hotel.star_rating,
                'amenities': hotel.amenities
            })
    
    if not hotel_data:
        return {
            'city': city,
            'message': 'No price data available for amenity analysis'
        }
    
    # Analyze amenity impact
    amenity_analysis = {}
    all_amenities = set()
    
    # Collect all unique amenities
    for hotel in hotel_data:
        all_amenities.update(hotel['amenities'])
    
    # Analyze each amenity
    for amenity in all_amenities:
        hotels_with_amenity = [h for h in hotel_data if amenity in h['amenities']]
        hotels_without_amenity = [h for h in hotel_data if amenity not in h['amenities']]
        
        if hotels_with_amenity and hotels_without_amenity:
            avg_price_with = np.mean([h['price'] for h in hotels_with_amenity])
            avg_price_without = np.mean([h['price'] for h in hotels_without_amenity])
            
            price_impact = avg_price_with - avg_price_without
            price_impact_percent = (price_impact / avg_price_without) * 100 if avg_price_without > 0 else 0
            
            amenity_analysis[amenity] = {
                'hotels_with_amenity': len(hotels_with_amenity),
                'hotels_without_amenity': len(hotels_without_amenity),
                'avg_price_with': round(avg_price_with, 2),
                'avg_price_without': round(avg_price_without, 2),
                'price_impact': round(price_impact, 2),
                'price_impact_percent': round(price_impact_percent, 1),
                'significance': 'high' if abs(price_impact_percent) > 10 else 'medium' if abs(price_impact_percent) > 5 else 'low'
            }
    
    # Sort by price impact
    sorted_amenities = sorted(
        amenity_analysis.items(),
        key=lambda x: abs(x[1]['price_impact_percent']),
        reverse=True
    )
    
    return {
        'city': city,
        'total_hotels_analyzed': len(hotel_data),
        'total_amenities_analyzed': len(amenity_analysis),
        'amenity_impact_analysis': dict(sorted_amenities)
    } 