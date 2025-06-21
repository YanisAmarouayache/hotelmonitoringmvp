#!/usr/bin/env python3
"""
Simple script to check the database contents
"""

import sqlite3
import json
from datetime import datetime

def check_database():
    """Check the contents of the hotel monitoring database."""
    try:
        # Connect to the database
        conn = sqlite3.connect('hotel_monitoring.db')
        cursor = conn.cursor()
        
        # Check what tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("Tables in database:")
        for table in tables:
            print(f"  - {table[0]}")
        
        print("\n" + "="*50)
        
        # Check hotels table
        cursor.execute("SELECT COUNT(*) FROM hotels")
        hotel_count = cursor.fetchone()[0]
        print(f"Total hotels in database: {hotel_count}")
        
        if hotel_count > 0:
            # Get all hotels
            cursor.execute("""
                SELECT id, name, booking_url, city, country, is_active, 
                       user_rating, star_rating, created_at
                FROM hotels
                ORDER BY created_at DESC
            """)
            hotels = cursor.fetchall()
            
            print("\nAll hotels:")
            for hotel in hotels:
                (id, name, url, city, country, is_active, 
                 user_rating, star_rating, created_at) = hotel
                print(f"  ID: {id}")
                print(f"  Name: {name}")
                print(f"  URL: {url}")
                print(f"  City: {city}")
                print(f"  Country: {country}")
                print(f"  Active: {is_active}")
                print(f"  User Rating: {user_rating}")
                print(f"  Star Rating: {star_rating}")
                print(f"  Created: {created_at}")
                print("  " + "-"*30)
        
        # Check active hotels only
        cursor.execute("SELECT COUNT(*) FROM hotels WHERE is_active = 1")
        active_count = cursor.fetchone()[0]
        print(f"\nActive hotels: {active_count}")
        
        if active_count > 0:
            cursor.execute("""
                SELECT id, name, booking_url, city, country, user_rating, star_rating
                FROM hotels
                WHERE is_active = 1
                ORDER BY created_at DESC
            """)
            active_hotels = cursor.fetchall()
            
            print("\nActive hotels only:")
            for hotel in active_hotels:
                (id, name, url, city, country, user_rating, star_rating) = hotel
                print(f"  {id}: {name} ({city}, {country}) - Rating: {user_rating}/10, Stars: {star_rating}")
        
        # Check hotel prices
        cursor.execute("SELECT COUNT(*) FROM hotel_prices")
        price_count = cursor.fetchone()[0]
        print(f"\nTotal price records: {price_count}")
        
        if price_count > 0:
            cursor.execute("""
                SELECT id, hotel_id, price, currency, check_in_date, check_out_date
                FROM hotel_prices
                ORDER BY scraped_at DESC
                LIMIT 5
            """)
            prices = cursor.fetchall()
            
            print("\nRecent price records:")
            for price in prices:
                (id, hotel_id, price_val, currency, check_in, check_out) = price
                print(f"  ID: {id}, Hotel ID: {hotel_id}, Price: {price_val} {currency}")
                print(f"    Check-in: {check_in}, Check-out: {check_out}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking database: {e}")

if __name__ == "__main__":
    check_database() 