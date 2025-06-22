#!/usr/bin/env python3
"""
Script de test pour déboguer l'API Playwright
"""

import asyncio
import sys
import os

# Ajouter le dossier scraper au path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scraper'))

from booking_playwright_final import BookingPlaywrightScraper

async def test_playwright_scraper():
    """Test direct du scraper Playwright."""
    print("=== Test direct du scraper Playwright ===")
    
    url = "https://www.booking.com/hotel/fr/bonne-nouvelle.html"
    print(f"URL: {url}")
    
    try:
        scraper = BookingPlaywrightScraper()
        print("✅ Scraper créé avec succès")
        
        result = await scraper.scrape_hotel_pricing(url)
        print(f"✅ Résultat: {result}")
        
        if result.get("success"):
            print(f"✅ Succès! Jours trouvés: {result.get('total_days', 0)}")
        else:
            print(f"❌ Erreur: {result.get('error', 'Erreur inconnue')}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_playwright_scraper()) 