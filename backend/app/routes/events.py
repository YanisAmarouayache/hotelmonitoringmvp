from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.models.event import Event, EventCreate, EventUpdate, EventResponse

router = APIRouter()

@router.get("/", response_model=List[EventResponse])
async def get_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    city: Optional[str] = None,
    event_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all events with optional filtering."""
    query = db.query(Event)
    
    if city:
        query = query.filter(Event.city.ilike(f"%{city}%"))
    
    if event_type:
        query = query.filter(Event.event_type == event_type)
    
    if start_date:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        query = query.filter(Event.start_date >= start_dt)
    
    if end_date:
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        query = query.filter(Event.end_date <= end_dt)
    
    events = query.offset(skip).limit(limit).order_by(Event.start_date).all()
    return events

@router.get("/{event_id}", response_model=EventResponse)
async def get_event(event_id: int, db: Session = Depends(get_db)):
    """Get a specific event by ID."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@router.post("/", response_model=EventResponse)
async def create_event(event_data: EventCreate, db: Session = Depends(get_db)):
    """Create a new event."""
    db_event = Event(**event_data.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    event_data: EventUpdate,
    db: Session = Depends(get_db)
):
    """Update an event."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Update only provided fields
    update_data = event_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(event, field, value)
    
    db.commit()
    db.refresh(event)
    return event

@router.delete("/{event_id}")
async def delete_event(event_id: int, db: Session = Depends(get_db)):
    """Delete an event."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    db.delete(event)
    db.commit()
    return {"message": "Event deleted successfully"}

@router.get("/upcoming/events")
async def get_upcoming_events(
    city: Optional[str] = None,
    days_ahead: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get upcoming events that may affect hotel pricing."""
    end_date = datetime.now() + timedelta(days=days_ahead)
    
    query = db.query(Event).filter(
        Event.start_date >= datetime.now(),
        Event.start_date <= end_date
    )
    
    if city:
        query = query.filter(Event.city.ilike(f"%{city}%"))
    
    events = query.order_by(Event.start_date).all()
    
    # Calculate impact scores
    upcoming_events = []
    for event in events:
        days_until_event = (event.start_date - datetime.now()).days
        
        # Adjust impact based on proximity
        proximity_multiplier = 1.0
        if days_until_event <= 7:
            proximity_multiplier = 1.5
        elif days_until_event <= 14:
            proximity_multiplier = 1.2
        elif days_until_event <= 30:
            proximity_multiplier = 1.0
        else:
            proximity_multiplier = 0.8
        
        adjusted_impact = event.impact_score * proximity_multiplier
        
        upcoming_events.append({
            'id': event.id,
            'name': event.name,
            'city': event.city,
            'start_date': event.start_date.strftime('%Y-%m-%d'),
            'end_date': event.end_date.strftime('%Y-%m-%d'),
            'event_type': event.event_type,
            'expected_attendance': event.expected_attendance,
            'impact_score': event.impact_score,
            'adjusted_impact': round(adjusted_impact, 2),
            'days_until_event': days_until_event,
            'description': event.description
        })
    
    return {
        'analysis_period_days': days_ahead,
        'total_events': len(upcoming_events),
        'events': upcoming_events
    }

@router.get("/cities/list")
async def get_event_cities(db: Session = Depends(get_db)):
    """Get list of all cities with events."""
    cities = db.query(Event.city).filter(Event.city.isnot(None)).distinct().all()
    return [city[0] for city in cities if city[0]]

@router.get("/types/list")
async def get_event_types(db: Session = Depends(get_db)):
    """Get list of all event types."""
    event_types = db.query(Event.event_type).filter(Event.event_type.isnot(None)).distinct().all()
    return [event_type[0] for event_type in event_types if event_type[0]]

@router.get("/impact-analysis/{city}")
async def get_event_impact_analysis(
    city: str,
    days_back: int = Query(90, ge=30, le=365),
    db: Session = Depends(get_db)
):
    """Analyze the impact of events on hotel pricing in a city."""
    # Get events in the city
    cutoff_date = datetime.now() - timedelta(days=days_back)
    events = db.query(Event).filter(
        Event.city.ilike(f"%{city}%"),
        Event.start_date >= cutoff_date
    ).order_by(Event.start_date).all()
    
    if not events:
        return {
            'city': city,
            'message': f'No events found in {city} for the specified period'
        }
    
    # Analyze event impact patterns
    event_analysis = []
    for event in events:
        # Calculate event duration
        event_duration = (event.end_date - event.start_date).days
        
        # Categorize event by size
        if event.expected_attendance:
            if event.expected_attendance > 10000:
                size_category = "major"
            elif event.expected_attendance > 1000:
                size_category = "medium"
            else:
                size_category = "small"
        else:
            size_category = "unknown"
        
        event_analysis.append({
            'event_id': event.id,
            'event_name': event.name,
            'event_type': event.event_type,
            'start_date': event.start_date.strftime('%Y-%m-%d'),
            'end_date': event.end_date.strftime('%Y-%m-%d'),
            'duration_days': event_duration,
            'expected_attendance': event.expected_attendance,
            'size_category': size_category,
            'impact_score': event.impact_score,
            'description': event.description
        })
    
    # Calculate summary statistics
    total_events = len(events)
    avg_impact_score = sum(e.impact_score for e in events) / total_events if events else 0
    avg_duration = sum((e.end_date - e.start_date).days for e in events) / total_events if events else 0
    
    # Group by event type
    event_types = {}
    for event in events:
        if event.event_type not in event_types:
            event_types[event.event_type] = []
        event_types[event.event_type].append(event)
    
    type_analysis = {}
    for event_type, type_events in event_types.items():
        type_analysis[event_type] = {
            'count': len(type_events),
            'avg_impact_score': sum(e.impact_score for e in type_events) / len(type_events),
            'avg_duration': sum((e.end_date - e.start_date).days for e in type_events) / len(type_events)
        }
    
    return {
        'city': city,
        'analysis_period_days': days_back,
        'summary': {
            'total_events': total_events,
            'average_impact_score': round(avg_impact_score, 2),
            'average_duration_days': round(avg_duration, 1)
        },
        'event_types': type_analysis,
        'events': event_analysis
    }

@router.post("/bulk-import")
async def bulk_import_events(
    events_data: List[EventCreate],
    db: Session = Depends(get_db)
):
    """Import multiple events at once."""
    imported_events = []
    errors = []
    
    for i, event_data in enumerate(events_data):
        try:
            db_event = Event(**event_data.dict())
            db.add(db_event)
            imported_events.append({
                'index': i,
                'name': event_data.name,
                'status': 'success'
            })
        except Exception as e:
            errors.append({
                'index': i,
                'name': event_data.name if hasattr(event_data, 'name') else 'Unknown',
                'error': str(e)
            })
    
    if imported_events:
        db.commit()
    
    return {
        'total_events': len(events_data),
        'successfully_imported': len(imported_events),
        'errors': len(errors),
        'imported_events': imported_events,
        'error_details': errors
    } 