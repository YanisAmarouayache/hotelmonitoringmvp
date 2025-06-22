import asyncio
import sys

# Force WindowsSelectorEventLoopPolicy for Playwright compatibility
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from playwright.async_api import async_playwright
import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BookingPlaywrightScraper:
    def __init__(self):
        self.graphql_responses = []
        
    def _extract_price_from_formatted_string(self, price_str: str) -> Optional[float]:
        """Extract numeric price from formatted string like '€763' or '€1.1K'."""
        try:
            # Remove currency symbols and spaces
            clean_price = re.sub(r'[€$£¥\s]', '', price_str)
            
            # Handle K (thousands) and M (millions)
            if 'K' in clean_price:
                clean_price = clean_price.replace('K', '')
                return float(clean_price) * 1000
            elif 'M' in clean_price:
                clean_price = clean_price.replace('M', '')
                return float(clean_price) * 1000000
            else:
                return float(clean_price)
        except Exception as e:
            logger.warning(f"Could not extract price from '{price_str}': {e}")
            return None
    
    async def scrape_hotel_pricing(self, url: str) -> Dict[str, Any]:
        """
        Scrape hotel pricing data using Playwright to trigger GraphQL requests.
        
        Args:
            url: Booking.com hotel URL
            
        Returns:
            Dictionary containing hotel pricing data
        """
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)  # headless=True for production
                page = await browser.new_page()
                
                # Intercept GraphQL responses
                async def on_response(response):
                    if "/dml/graphql" in response.url:
                        try:
                            body = await response.text()
                            try:
                                data = json.loads(body)
                                self.graphql_responses.append(data)
                                # Debug: afficher l'URL de la requête
                                logger.info(f"GraphQL request captured: {response.url}")
                                if 'availabilityCalendar' in str(data):
                                    logger.info("✅ AvailabilityCalendar found in response!")
                            except Exception:
                                pass  # Skip non-JSON responses
                        except Exception as e:
                            logger.warning(f"Error reading GraphQL response: {e}")
                
                page.on("response", on_response)
                
                logger.info(f"Opening page: {url}")
                await page.goto(url)
                await page.wait_for_timeout(3000)
                
                # Click on the second searchbox-dates-container in hp_availability_style_changes
                logger.info("Clicking on second searchbox-dates-container in hp_availability_style_changes...")
                try:
                    # Sélecteur pour le deuxième searchbox-dates-container dans hp_availability_style_changes
                    await page.click('#hp_availability_style_changes [data-testid="searchbox-dates-container"]')
                    logger.info("Successfully clicked on second searchbox-dates-container")
                except Exception as e:
                    logger.error(f"Error clicking second searchbox-dates-container: {e}")
                    # Try alternative selectors
                    try:
                        # Essayer de cliquer sur tous les searchbox-dates-container et prendre le deuxième
                        containers = await page.query_selector_all('[data-testid="searchbox-dates-container"]')
                        if len(containers) >= 2:
                            await containers[1].click()
                            logger.info("Clicked on second searchbox-dates-container (alternative method)")
                        else:
                            logger.error(f"Only found {len(containers)} searchbox-dates-container elements")
                    except Exception as e2:
                        logger.error(f"Error with fallback click: {e2}")
                
                # Wait for GraphQL requests to complete
                logger.info("Waiting for GraphQL requests to complete...")
                await page.wait_for_timeout(8000)
                
                await browser.close()
            
            # Process the responses to extract pricing data
            pricing_data = self._extract_pricing_from_responses()
            
            return {
                'success': True,
                'hotel_url': url,
                'pricing_data': pricing_data,
                'total_days': len(pricing_data.get('days', [])),
                'scraped_at': datetime.now().isoformat(),
                'raw_responses_count': len(self.graphql_responses)
            }
            
        except Exception as e:
            logger.error(f"Error in scrape_hotel_pricing: {e}")
            return {
                'success': False,
                'error': str(e),
                'hotel_url': url,
                'scraped_at': datetime.now().isoformat()
            }
    
    def _extract_pricing_from_responses(self) -> Dict[str, Any]:
        """Extract pricing data from GraphQL responses."""
        pricing_data = {
            'hotel_id': None,
            'days': [],
            'total_available_days': 0
        }
        
        for response in self.graphql_responses:
            if 'data' in response and 'availabilityCalendar' in response['data']:
                calendar_data = response['data']['availabilityCalendar']
                
                # Extract hotel ID if available
                if 'hotelId' in calendar_data:
                    pricing_data['hotel_id'] = calendar_data['hotelId']
                
                # Process days data
                if 'days' in calendar_data:
                    for day in calendar_data['days']:
                        if day.get('available', False):
                            # Convert price from formatted string to float
                            price_str = day.get('avgPriceFormatted', '€0')
                            price = self._extract_price_from_formatted_string(price_str)
                            
                            processed_day = {
                                'checkin': day.get('checkin'),
                                'available': day.get('available', False),
                                'price': price,
                                'price_formatted': price_str,
                                'min_length_of_stay': day.get('minLengthOfStay', 1)
                            }
                            pricing_data['days'].append(processed_day)
                
                pricing_data['total_available_days'] = len(pricing_data['days'])
                break  # We found the availability calendar, no need to continue
        
        return pricing_data
    
    async def scrape_multiple_hotels(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        Scrape pricing data for multiple hotels.
        
        Args:
            urls: List of Booking.com hotel URLs
            
        Returns:
            List of pricing data for each hotel
        """
        results = []
        
        for i, url in enumerate(urls):
            logger.info(f"Scraping hotel {i+1}/{len(urls)}: {url}")
            
            # Reset responses for each hotel
            self.graphql_responses = []
            
            # Add delay between requests
            if i > 0:
                await asyncio.sleep(3)
            
            result = await self.scrape_hotel_pricing(url)
            results.append(result)
        
        return results

async def main():
    """Test the scraper with the Brach hotel."""
    scraper = BookingPlaywrightScraper()
    
    # Test with Brach hotel
    url = "https://www.booking.com/hotel/fr/brach-paris.html"
    
    print("=== Test du scraper Playwright Booking.com ===")
    print(f"URL: {url}")
    print()
    
    result = await scraper.scrape_hotel_pricing(url)
    
    if result['success']:
        print("✅ Scraping réussi!")
        print(f"Jours disponibles: {result['total_days']}")
        print(f"Réponses GraphQL capturées: {result['raw_responses_count']}")
        
        # Afficher quelques exemples de prix
        pricing_data = result['pricing_data']
        days = pricing_data.get('days', [])
        if days:
            print("\nExemples de prix:")
            for i, day in enumerate(days[:10]):  # Afficher les 10 premiers
                print(f"  {day['checkin']}: {day['price_formatted']} (€{day['price']})")
            if len(days) > 10:
                print(f"  ... et {len(days) - 10} autres jours")
        
        # Sauvegarder le résultat
        with open('playwright_final_results.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print("\nRésultats sauvegardés dans 'playwright_final_results.json'")
        
    else:
        print(f"❌ Erreur: {result['error']}")

if __name__ == "__main__":
    asyncio.run(main()) 