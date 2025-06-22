import asyncio
from playwright.async_api import async_playwright
import json

async def main():
    url = "https://www.booking.com/hotel/fr/brach-paris.html"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Intercepter les requêtes GraphQL
        async def on_response(response):
            if "/dml/graphql" in response.url:
                try:
                    body = await response.text()
                    if 'availabilityCalendar' in body:
                        print("🎯 AVAILABILITY CALENDAR TROUVÉ!")
                        print(f"URL: {response.url}")
                        print(f"Données: {body[:300]}...")
                except:
                    pass
        
        page.on("response", on_response)
        
        print("🌐 Ouverture de la page...")
        await page.goto(url)
        
        print("\n🎯 Navigateur ouvert! Cliquez sur les éléments et regardez la console.")
        print("Appuyez sur Ctrl+C pour arrêter.")
        
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n⏹️ Arrêt...")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main()) 