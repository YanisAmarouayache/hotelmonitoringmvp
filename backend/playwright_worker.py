#!/usr/bin/env python3
"""
Worker script pour exécuter Playwright dans un processus séparé
Évite les problèmes d'event loop avec FastAPI sous Windows
"""

import sys
import os
import json
import asyncio
import subprocess
from pathlib import Path

# Ajouter le dossier scraper au path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scraper'))

def run_playwright_scraper(url: str) -> dict:
    """
    Lance le scraper Playwright dans un processus séparé
    """
    try:
        # Créer un script temporaire pour exécuter le scraper
        script_content = f'''
import asyncio
import sys
import os
import json

# Ajouter le dossier scraper au path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scraper'))

from booking_playwright_final import BookingPlaywrightScraper

async def main():
    scraper = BookingPlaywrightScraper()
    result = await scraper.scrape_hotel_pricing("{url}")
    print(json.dumps(result))

if __name__ == "__main__":
    asyncio.run(main())
'''
        
        # Écrire le script temporaire
        temp_script = Path(__file__).parent / "temp_scraper.py"
        with open(temp_script, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        # Exécuter le script dans un processus séparé
        result = subprocess.run(
            [sys.executable, str(temp_script)],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__)
        )
        
        # Nettoyer le script temporaire
        temp_script.unlink(missing_ok=True)
        
        if result.returncode == 0:
            return json.loads(result.stdout.strip())
        else:
            return {
                'success': False,
                'error': f"Process failed: {result.stderr}",
                'hotel_url': url
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'hotel_url': url
        }

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({'success': False, 'error': 'URL argument required'}))
        sys.exit(1)
    
    url = sys.argv[1]
    result = run_playwright_scraper(url)
    print(json.dumps(result)) 