import requests
import json
import time
import random
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
from urllib.parse import urlparse, parse_qs
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BookingGraphQLScraper:
    def __init__(self):
        self.session = requests.Session()
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        ]
        self.graphql_url = "https://www.booking.com/dml/graphql"
        
    def _get_random_user_agent(self) -> str:
        """Get a random user agent to avoid detection."""
        return random.choice(self.user_agents)
    
    def _add_headers(self, referer: str = None) -> Dict[str, str]:
        """Add headers to the request."""
        headers = {
            'User-Agent': self._get_random_user_agent(),
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Origin': 'https://www.booking.com',
            'Referer': referer or 'https://www.booking.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }
        return headers
    
    def _random_delay(self, min_delay: float = 1.0, max_delay: float = 3.0):
        """Add random delay between requests."""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    def extract_hotel_id_from_url(self, url: str) -> Optional[int]:
        """Extract hotel ID from Booking.com URL."""
        try:
            # Try to extract from URL path
            path_match = re.search(r'/hotel/[a-z]{2}/([^/]+)\.html', url)
            if path_match:
                hotel_slug = path_match.group(1)
                # The hotel ID might be in the URL parameters
                parsed_url = urlparse(url)
                params = parse_qs(parsed_url.query)
                
                # Check for highlighted_hotels parameter
                if 'highlighted_hotels' in params:
                    return int(params['highlighted_hotels'][0])
                
                # If not found, we'll need to extract it from the page
                return None
            
            return None
        except Exception as e:
            logger.error(f"Error extracting hotel ID from URL: {e}")
            return None
    
    def get_hotel_id_from_page(self, url: str) -> Optional[int]:
        """Get hotel ID by scraping the hotel page."""
        try:
            headers = self._add_headers(url)
            response = self.session.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Look for hotel ID in the page content
            content = response.text
            
            # Try to find hotel ID in various patterns
            patterns = [
                r'"hotelId":\s*(\d+)',
                r'"property_id":\s*(\d+)',
                r'data-hotel-id="(\d+)"',
                r'hotel_id=(\d+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, content)
                if match:
                    return int(match.group(1))
            
            return None
        except Exception as e:
            logger.error(f"Error getting hotel ID from page: {e}")
            return None
    
    def extract_url_parameters(self, url: str) -> Dict[str, str]:
        """Extract all URL parameters needed for GraphQL request."""
        try:
            parsed_url = urlparse(url)
            params = parse_qs(parsed_url.query)
            
            # Convert list values to single values
            extracted_params = {}
            for key, value_list in params.items():
                if value_list:
                    extracted_params[key] = value_list[0]
            
            return extracted_params
        except Exception as e:
            logger.error(f"Error extracting URL parameters: {e}")
            return {}
    
    def get_availability_calendar(self, url: str, hotel_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get availability calendar data using GraphQL API.
        
        Args:
            url: Booking.com hotel URL
            hotel_id: Hotel ID (will be extracted from URL if not provided)
            
        Returns:
            Dictionary containing availability calendar data
        """
        try:
            # 1. GET sur la page de l'hôtel pour récupérer les cookies/session
            headers_get = self._add_headers(url)
            logger.info(f"GET initial pour récupérer les cookies: {url}")
            self.session.get(url, headers=headers_get, timeout=30)
            # Les cookies sont maintenant dans self.session

            # 2. Extraction des paramètres et construction du body comme avant
            if not hotel_id:
                hotel_id = self.extract_hotel_id_from_url(url)
                if not hotel_id:
                    hotel_id = self.get_hotel_id_from_page(url)
            if not hotel_id:
                return {
                    'error': 'Could not extract hotel ID from URL',
                    'booking_url': url,
                    'scraped_at': datetime.now().isoformat()
                }
            url_params = self.extract_url_parameters(url)
            variables = {
                'hotelId': hotel_id,
                'checkin': url_params.get('checkin', '2025-06-23'),
                'checkout': url_params.get('checkout', '2025-06-24'),
                'groupAdults': int(url_params.get('group_adults', '2')),
                'groupChildren': int(url_params.get('group_children', '0')),
                'noRooms': int(url_params.get('no_rooms', '1')),
                'from': url_params.get('from', url_params.get('checkin', '2025-06-01'))
            }
            extensions = {
                'persistedQuery': {
                    'version': 1,
                    'sha256Hash': '8f08e03c7bd16fcad3c920c9e5e3c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0'
                }
            }
            body = {
                'operationName': 'AvailabilityCalendar',
                'variables': variables,
                'extensions': extensions
            }
            context_keys = [
                'sid', 'aid', 'lang', 'sb', 'src_elem', 'src', 'ssne', 'ssne_untouched',
                'highlighted_hotels', 'ss', 'dest_id', 'dest_type', 'hp_avform', 'origin',
                'do_availability_check', 'label', 'age'
            ]
            context_params = {k: v for k, v in url_params.items() if k in context_keys}
            graphql_url = self.graphql_url
            if context_params:
                graphql_url += '?' + '&'.join([f'{k}={v}' for k, v in context_params.items()])
            headers = self._add_headers(url)
            logger.info(f"Making GraphQL POST request for hotel {hotel_id}")
            logger.info(f"URL: {graphql_url}")
            logger.info(f"Body: {json.dumps(body)}")
            response = self.session.post(
                graphql_url,
                headers=headers,
                json=body,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            if 'data' in data and 'availabilityCalendar' in data['data']:
                calendar_data = data['data']['availabilityCalendar']
                processed_days = []
                for day in calendar_data.get('days', []):
                    if day.get('available', False):
                        price_str = day.get('avgPriceFormatted', '€0')
                        price = self._extract_price_from_formatted_string(price_str)
                        processed_day = {
                            'checkin': day.get('checkin'),
                            'available': day.get('available', False),
                            'price': price,
                            'price_formatted': price_str,
                            'min_length_of_stay': day.get('minLengthOfStay', 1)
                        }
                        processed_days.append(processed_day)
                return {
                    'hotel_id': hotel_id,
                    'days': processed_days,
                    'total_available_days': len(processed_days),
                    'scraped_at': datetime.now().isoformat(),
                    'booking_url': url,
                    'raw_response': data
                }
            else:
                return {
                    'error': 'No availability calendar data found in response',
                    'response_data': data,
                    'booking_url': url,
                    'scraped_at': datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Error getting availability calendar: {e}")
            return {
                'error': str(e),
                'booking_url': url,
                'scraped_at': datetime.now().isoformat()
            }
    
    def _extract_price_from_formatted_string(self, price_str: str) -> Optional[float]:
        """Extract numeric price from formatted string like '€1.6K'."""
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
    
    def scrape_hotel_with_pricing(self, url: str) -> Dict[str, Any]:
        """
        Scrape hotel data and pricing using GraphQL API.
        
        Args:
            url: Booking.com hotel URL
            
        Returns:
            Dictionary containing hotel data and pricing information
        """
        try:
            # First, get basic hotel information from the page
            hotel_data = self._get_hotel_basic_info(url)
            
            # Then get pricing data using GraphQL
            pricing_data = self.get_availability_calendar(url)
            
            # Combine the data
            result = {
                'hotel_data': hotel_data,
                'pricing_data': pricing_data,
                'scraped_at': datetime.now().isoformat(),
                'booking_url': url
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error scraping hotel with pricing: {e}")
            return {
                'error': str(e),
                'booking_url': url,
                'scraped_at': datetime.now().isoformat()
            }
    
    def _get_hotel_basic_info(self, url: str) -> Dict[str, Any]:
        """Get basic hotel information from the hotel page."""
        try:
            headers = self._add_headers(url)
            response = self.session.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            content = response.text
            
            # Extract basic information using regex patterns
            hotel_info = {}
            
            # Hotel name
            name_patterns = [
                r'<h1[^>]*class="[^"]*hp__hotel-name[^"]*"[^>]*>([^<]+)</h1>',
                r'"name":\s*"([^"]+)"',
                r'<title>([^<]+)</title>'
            ]
            
            for pattern in name_patterns:
                match = re.search(pattern, content)
                if match:
                    hotel_info['name'] = match.group(1).strip()
                    break
            
            # Address
            address_patterns = [
                r'"address":\s*"([^"]+)"',
                r'data-address="([^"]+)"'
            ]
            
            for pattern in address_patterns:
                match = re.search(pattern, content)
                if match:
                    hotel_info['address'] = match.group(1).strip()
                    break
            
            # City
            city_patterns = [
                r'"city":\s*"([^"]+)"',
                r'data-city="([^"]+)"'
            ]
            
            for pattern in city_patterns:
                match = re.search(pattern, content)
                if match:
                    hotel_info['city'] = match.group(1).strip()
                    break
            
            # Country
            country_patterns = [
                r'"country":\s*"([^"]+)"',
                r'data-country="([^"]+)"'
            ]
            
            for pattern in country_patterns:
                match = re.search(pattern, content)
                if match:
                    hotel_info['country'] = match.group(1).strip()
                    break
            
            # Star rating
            star_patterns = [
                r'"starRating":\s*(\d+(?:\.\d+)?)',
                r'data-star-rating="(\d+(?:\.\d+)?)"'
            ]
            
            for pattern in star_patterns:
                match = re.search(pattern, content)
                if match:
                    hotel_info['star_rating'] = float(match.group(1))
                    break
            
            # User rating
            rating_patterns = [
                r'"reviewScore":\s*(\d+(?:\.\d+)?)',
                r'data-review-score="(\d+(?:\.\d+)?)"'
            ]
            
            for pattern in rating_patterns:
                match = re.search(pattern, content)
                if match:
                    hotel_info['user_rating'] = float(match.group(1))
                    break
            
            # Review count
            review_count_patterns = [
                r'"reviewCount":\s*(\d+)',
                r'data-review-count="(\d+)"'
            ]
            
            for pattern in review_count_patterns:
                match = re.search(pattern, content)
                if match:
                    hotel_info['user_rating_count'] = int(match.group(1))
                    break
            
            return hotel_info
            
        except Exception as e:
            logger.error(f"Error getting hotel basic info: {e}")
            return {} 