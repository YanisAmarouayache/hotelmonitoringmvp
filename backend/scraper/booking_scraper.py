import requests
from bs4 import BeautifulSoup
import re
import time
import random
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import logging
import os
from urllib.parse import urlparse, parse_qs

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BookingScraper:
    def __init__(self):
        self.session = requests.Session()
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; CrOS x86_64 8172.45.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.64 Safari/537.36'
        ]
        self.base_url = "https://www.booking.com"
        
    def _get_random_user_agent(self) -> str:
        """Get a random user agent to avoid detection."""
        return random.choice(self.user_agents)
    
    def _add_headers(self, url: str) -> Dict[str, str]:
        """Add headers to the request."""
        return {
            'User-Agent': self._get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': self.base_url
        }
    
    def _random_delay(self, min_delay: float = 1.0, max_delay: float = 3.0):
        """Add random delay between requests."""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    def _save_html_for_debugging(self, soup: BeautifulSoup, url: str):
        """Save HTML content for debugging purposes."""
        try:
            debug_dir = "debug_html"
            if not os.path.exists(debug_dir):
                os.makedirs(debug_dir)
            
            # Create a safe filename from the URL
            safe_filename = url.replace("https://", "").replace("http://", "").replace("/", "_").replace("?", "_").replace("&", "_")
            safe_filename = safe_filename[:100] + ".html"  # Limit length
            
            filepath = os.path.join(debug_dir, safe_filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(soup.prettify())
            
            print(f"Saved HTML for debugging to: {filepath}")
        except Exception as e:
            print(f"Failed to save HTML for debugging: {e}")

    def extract_hotel_data(self, url: str, check_in_date: Optional[str] = None, 
                          check_out_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract hotel data from Booking.com URL.
        
        Args:
            url: Booking.com hotel URL
            check_in_date: Check-in date (YYYY-MM-DD) - will be extracted from URL if not provided
            check_out_date: Check-out date (YYYY-MM-DD) - will be extracted from URL if not provided
            
        Returns:
            Dictionary containing hotel data
        """
        try:
            # Extract dates and guest info from URL if not provided
            url_check_in, url_check_out, guest_info = self._extract_dates_from_url(url)
            
            # Use provided dates or extracted dates
            final_check_in = check_in_date or url_check_in
            final_check_out = check_out_date or url_check_out
            
            # Add dates to URL if we have them
            if final_check_in and final_check_out:
                url = self._add_dates_to_url(url, final_check_in, final_check_out)
            
            logger.info(f"Scraping hotel data from: {url}")
            logger.info(f"Check-in: {final_check_in}, Check-out: {final_check_out}")
            if guest_info:
                logger.info(f"Guest info: {guest_info}")
            
            # Make request
            headers = self._add_headers(url)
            response = self.session.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Save HTML for debugging
            self._save_html_for_debugging(soup, url)
            
            # Extract data from hotel page
            print("=== Extracting from HOTEL page ===")
            result = self._extract_from_hotel_page(soup, url)
            
            # Add extracted dates and guest info to result
            if final_check_in:
                result['check_in_date'] = final_check_in
            if final_check_out:
                result['check_out_date'] = final_check_out
            if guest_info:
                result['guest_info'] = guest_info
            
            return result
            
        except Exception as e:
            logger.error(f"Error scraping hotel data: {str(e)}")
            return {
                'error': str(e),
                'booking_url': url,
                'scraped_at': datetime.now().isoformat()
            }
    
    def _extract_dates_from_url(self, url: str) -> tuple[Optional[str], Optional[str], Optional[dict]]:
        """Extract check-in, check-out dates and guest info from URL parameters."""
        try:
            parsed_url = urlparse(url)
            params = parse_qs(parsed_url.query)
            
            # Extract dates
            check_in = params.get('checkin', [None])[0]
            check_out = params.get('checkout', [None])[0]
            
            # Extract guest info
            guest_info = {}
            if 'group_adults' in params:
                guest_info['adults'] = int(params['group_adults'][0])
            if 'group_children' in params:
                guest_info['children'] = int(params['group_children'][0])
            if 'req_adults' in params:
                guest_info['adults'] = int(params['req_adults'][0])
            if 'req_children' in params:
                guest_info['children'] = int(params['req_children'][0])
            
            print(f"Extracted from URL - Check-in: {check_in}, Check-out: {check_out}, Guests: {guest_info}")
            
            return check_in, check_out, guest_info if guest_info else None
            
        except Exception as e:
            logger.warning(f"Error extracting dates from URL: {e}")
            return None, None, None
    
    def _extract_from_hotel_page(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract data from individual hotel page."""
        try:
            print(f"\n=== Extracting data from hotel page: {url} ===")
            
            # Extract hotel name
            name = self._extract_hotel_name(soup)
            print(f"Extracted name: {name}")
            
            # Extract JSON data first (more reliable)
            json_data = self._extract_json_data(soup)
            json_review_score = self._extract_review_score_from_json(soup)
            json_amenities = self._extract_amenities_from_json(soup)
            
            # Extract address and location (use JSON data as fallback)
            address = self._extract_address(soup) or json_data.get('address')
            print(f"Extracted address: {address}")
            
            city = self._extract_city(soup) or json_data.get('city')
            print(f"Extracted city: {city}")
            
            country = self._extract_country(soup) or json_data.get('country')
            print(f"Extracted country: {country}")
            
            # Extract ratings
            star_rating = self._extract_star_rating(soup)
            print(f"Extracted star rating: {star_rating}")
            
            user_rating = self._extract_user_rating(soup) or json_review_score
            print(f"Extracted user rating: {user_rating}")
            
            user_rating_count = self._extract_rating_count(soup)
            print(f"Extracted rating count: {user_rating_count}")
            
            # Extract amenities (use JSON data as fallback)
            amenities = self._extract_amenities(soup) or json_amenities
            print(f"Extracted amenities: {amenities}")
            
            # Extract coordinates
            latitude = self._extract_latitude(soup)
            print(f"Extracted latitude: {latitude}")
            
            longitude = self._extract_longitude(soup)
            print(f"Extracted longitude: {longitude}")
            
            # Extract price
            price = self._extract_price(soup)
            print(f"Extracted price: {price}")
            
            currency = self._extract_currency(soup)
            print(f"Extracted currency: {currency}")
            
            # Extract room and board info
            room_type = self._extract_room_type(soup)
            print(f"Extracted room type: {room_type}")
            
            board_type = self._extract_board_type(soup)
            print(f"Extracted board type: {board_type}")
            
            # Extract multiple room types and prices
            rooms_data = self._extract_room_types_and_prices(soup)
            print(f"Extracted rooms data: {rooms_data}")
            
            result = {
                'type': 'hotel_page',
                'name': name,
                'address': address,
                'city': city,
                'country': country,
                'star_rating': star_rating,
                'user_rating': user_rating,
                'user_rating_count': user_rating_count,
                'amenities': amenities,
                'latitude': latitude,
                'longitude': longitude,
                'price': price,
                'currency': currency,
                'room_type': room_type,
                'board_type': board_type,
                'rooms_data': rooms_data,
                'booking_url': url,
                'scraped_at': datetime.now().isoformat()
            }
            
            print(f"=== Final result: {result} ===")
            return result
            
        except Exception as e:
            logger.error(f"Error extracting from hotel page: {e}")
            return {
                'error': str(e),
                'type': 'hotel_page',
                'booking_url': url,
                'scraped_at': datetime.now().isoformat()
            }
    
    def _extract_price(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract current price."""
        try:
            # First try to extract from JSON data (more reliable)
            # json_price = self._extract_price_from_json(soup)
            # if json_price:
            #     print(f"Found price in JSON: {json_price}")
            #     return json_price
            
            # Try multiple selectors for price
            selectors = [
                '[data-testid="price-and-discounted-price"] .b5cd09854e',
                '[data-testid="price-and-discounted-price"]',
                '.hp__hotel-rate',
                '.hp__hotel-price',
                '[class*="price"]',
                '.price',
                '.rate',
                '.hotel-price',
                '.room-price',
                '[data-testid="price"]',
                '.b5cd09854e.d10a6220b4',  # Common Booking.com price class
                '.b5cd09854e.c90c0a70d3.db63693c62',  # Another price class
                '.b5cd09854e.f0d4d6a2f5.e46e88563a',  # Price class
                '.b5cd09854e.d10a6220b4.e46e88563a'   # Price class
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text(strip=True)
                    if text:
                        # Extract number from price text
                        price = self._extract_price_from_text(text)
                        if price:
                            print(f"Found price with selector '{selector}': {price}")
                            return price
            
            # Try to find price in any element containing currency symbols
            currency_patterns = [
                r'€\s*([\d,]+\.?\d*)',
                r'(\d+)\s*€',
                r'\$\s*([\d,]+\.?\d*)',
                r'(\d+)\s*\$',
                r'£\s*([\d,]+\.?\d*)',
                r'(\d+)\s*£'
            ]
            
            for pattern in currency_patterns:
                matches = soup.find_all(text=re.compile(pattern))
                for match in matches:
                    if match.parent:
                        text = match.parent.get_text(strip=True)
                        price = self._extract_price_from_text(text)
                        if price:
                            print(f"Found price with currency pattern: {price}")
                            return price
            
            print("No price found")
            return None
        except Exception as e:
            logger.warning(f"Error extracting price: {e}")
            return None
    
    def _extract_price_from_json(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract price from JSON data embedded in the HTML."""
        try:
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    script_text = script.string
                    
                    # Look for price in JSON data
                    price_patterns = [
                        r'"price":\s*([\d.]+)',
                        r'"amount":\s*([\d.]+)',
                        r'"value":\s*([\d.]+)',
                        r'"rate":\s*([\d.]+)',
                        r'"current_price":\s*([\d.]+)',
                        r'"display_price":\s*([\d.]+)',
                        r'"price_amount":\s*([\d.]+)',
                        r'"priceValue":\s*([\d.]+)',
                        r'"price_value":\s*([\d.]+)',
                        r'"priceAmount":\s*([\d.]+)'
                    ]
                    
                    for pattern in price_patterns:
                        match = re.search(pattern, script_text)
                        if match:
                            price = float(match.group(1))
                            if price > 0 and price < 10000:  # Reasonable price range
                                return price
            
            return None
        except Exception as e:
            logger.warning(f"Error extracting price from JSON: {e}")
            return None
    
    def _extract_room_types_and_prices(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract multiple room types with their prices."""
        try:
            rooms_data = []
            
            # Try to extract from room selection table FIRST (most reliable)
            table_rooms = self._extract_rooms_from_selection_table(soup)
            if table_rooms:
                print(f"Found {len(table_rooms)} rooms in selection table")
                return table_rooms
            
            # Try to extract from JSON data as fallback
            json_rooms = self._extract_room_types_from_json(soup)
            if json_rooms:
                print(f"Found {len(json_rooms)} rooms in JSON data")
                return json_rooms
            
            # Try HTML selectors for room cards - use more specific selectors
            room_selectors = [
                '[data-testid="property-card"]',
                '.room-card',
                '.room-item',
                '.room-option',
                '.hp__room',
                '.room-block',
                # More specific Booking.com selectors
                '[data-testid="room-card"]',
                '.room-card-container',
                '.room-type-card',
                # Avoid generic room selectors that might catch error messages
                # '[class*="room"]'  # Removed this as it's too broad
            ]
            
            for selector in room_selectors:
                room_elements = soup.select(selector)
                if room_elements:
                    print(f"Found {len(room_elements)} room elements with selector '{selector}'")
                    
                    for room_element in room_elements:
                        try:
                            # Extract room type
                            room_type = self._extract_room_type_from_element(room_element)
                            
                            # Extract price
                            price = self._extract_price_from_element(room_element)
                            
                            # Extract board type
                            board_type = self._extract_board_type_from_element(room_element)
                            
                            # Only add if we have valid room type or price
                            if room_type or price:
                                room_data = {
                                    'room_type': room_type,
                                    'price': price,
                                    'board_type': board_type,
                                    'currency': 'EUR'  # Default
                                }
                                rooms_data.append(room_data)
                                print(f"Extracted room: {room_type} - {price} EUR")
                        
                        except Exception as e:
                            logger.warning(f"Error extracting room data: {e}")
                            continue
            
            return rooms_data
            
        except Exception as e:
            logger.warning(f"Error extracting room types and prices: {e}")
            return []
    
    def _extract_rooms_from_selection_table(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract room types and prices from the room selection table."""
        try:
            rooms_data = []
            
            # Find all elements with data-hotel-rounded-price attribute
            price_elements = soup.find_all(attrs={'data-hotel-rounded-price': True})
            
            if price_elements:
                print(f"Found {len(price_elements)} elements with data-hotel-rounded-price attribute")
                
                for price_element in price_elements:
                    try:
                        # Extract price from the data attribute
                        price_attr = price_element.get('data-hotel-rounded-price')
                        price = float(price_attr) if price_attr else None
                        
                        # Find the next hprt-roomtype-icon-link span
                        room_type = None
                        next_element = price_element.find_next_sibling()
                        
                        # Look for the span in siblings or nearby elements
                        while next_element and not room_type:
                            # Check if this element has the room type span
                            room_span = next_element.find('span', class_='hprt-roomtype-icon-link')
                            if room_span:
                                room_type = room_span.get_text(strip=True)
                                print(f"Found room type: {room_type}")
                                break
                            
                            # Check if this element itself is the room type span
                            if next_element.name == 'span' and 'hprt-roomtype-icon-link' in next_element.get('class', []):
                                room_type = next_element.get_text(strip=True)
                                print(f"Found room type: {room_type}")
                                break
                            
                            # Move to next sibling
                            next_element = next_element.find_next_sibling()
                        
                        # If we still don't have room type, look in the same container
                        if not room_type:
                            container = price_element.find_parent(['tr', 'td', 'div'])
                            if container:
                                room_span = container.find('span', class_='hprt-roomtype-icon-link')
                                if room_span:
                                    room_type = room_span.get_text(strip=True)
                                    print(f"Found room type in container: {room_type}")
                        
                        # Only add if we have both price and room type
                        if price and room_type:
                            room_data = {
                                'room_type': room_type,
                                'price': price,
                                'board_type': None,
                                'currency': 'EUR'  # Default
                            }
                            rooms_data.append(room_data)
                            print(f"Extracted room: {room_type} - {price} EUR")
                    
                    except Exception as e:
                        print(f"Error extracting room from price element: {e}")
                        continue
            
            print(f"Total rooms extracted: {len(rooms_data)}")
            return rooms_data
            
        except Exception as e:
            logger.error(f"Error extracting rooms from selection table: {e}")
            return []
    
    def _extract_room_type_from_element(self, element) -> Optional[str]:
        """Extract room type from a specific element."""
        try:
            # Try multiple selectors for room type
            selectors = [
                '[data-testid="room-type"]',
                '.room-type',
                '.room-name',
                '.room-title',
                'h3',
                'h4',
                '.title',
                '[class*="room"]'
            ]
            
            for selector in selectors:
                room_element = element.select_one(selector)
                if room_element:
                    room_type = room_element.get_text(strip=True)
                    if room_type and len(room_type) < 100:
                        # Filter out error messages and invalid room types
                        if any(error_text in room_type.lower() for error_text in [
                            'something went wrong',
                            'please try again',
                            'error',
                            'loading',
                            'unavailable'
                        ]):
                            continue
                        
                        # Check if it looks like a valid room type
                        valid_room_keywords = [
                            'room', 'suite', 'apartment', 'studio', 'villa', 'chalet',
                            'single', 'double', 'twin', 'triple', 'quad', 'family',
                            'deluxe', 'standard', 'superior', 'executive', 'presidential'
                        ]
                        
                        if any(keyword in room_type.lower() for keyword in valid_room_keywords):
                            return room_type
            
            return None
        except Exception as e:
            logger.warning(f"Error extracting room type from element: {e}")
            return None
    
    def _extract_price_from_element(self, element) -> Optional[float]:
        """Extract price from a specific element."""
        try:
            # Try multiple selectors for price
            selectors = [
                '[data-testid="price"]',
                '.price',
                '.rate',
                '.amount',
                '[class*="price"]',
                '.b5cd09854e'  # Common Booking.com price class
            ]
            
            for selector in selectors:
                price_element = element.select_one(selector)
                if price_element:
                    text = price_element.get_text(strip=True)
                    if text:
                        price = self._extract_price_from_text(text)
                        if price:
                            return price
            
            return None
        except Exception as e:
            logger.warning(f"Error extracting price from element: {e}")
            return None
    
    def _extract_board_type_from_element(self, element) -> Optional[str]:
        """Extract board type from a specific element."""
        try:
            # Try multiple selectors for board type
            selectors = [
                '[data-testid="board-type"]',
                '.board-type',
                '.meal-plan',
                '.breakfast',
                '[class*="board"]',
                '[class*="meal"]'
            ]
            
            for selector in selectors:
                board_element = element.select_one(selector)
                if board_element:
                    board_type = board_element.get_text(strip=True)
                    if board_type and len(board_type) < 50:
                        return board_type
            
            return None
        except Exception as e:
            logger.warning(f"Error extracting board type from element: {e}")
            return None

    def _extract_price_from_text(self, price_text: str) -> Optional[float]:
        """Extract numeric price from text."""
        if not price_text:
            return None
        
        # Remove currency symbols and extract numbers
        price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
        if price_match:
            return float(price_match.group())
        return None
    
    def _extract_rating_from_text(self, rating_text: str) -> Optional[float]:
        """Extract numeric rating from text."""
        if not rating_text:
            return None
        
        # Extract numbers from rating text
        rating_match = re.search(r'(\d+\.?\d*)', rating_text)
        if rating_match:
            rating = float(rating_match.group(1))
            # Normalize to 0-10 scale if needed
            if rating > 10:
                rating = rating / 10
            return rating
        return None
    
    def _add_dates_to_url(self, url: str, check_in: str, check_out: str) -> str:
        """Add check-in and check-out dates to the URL."""
        # Parse dates
        check_in_date = datetime.strptime(check_in, '%Y-%m-%d')
        check_out_date = datetime.strptime(check_out, '%Y-%m-%d')
        
        # Format dates for Booking.com
        check_in_str = check_in_date.strftime('%Y-%m-%d')
        check_out_str = check_out_date.strftime('%Y-%m-%d')
        
        # Add to URL
        if '?' in url:
            url += f"&checkin={check_in_str}&checkout={check_out_str}"
        else:
            url += f"?checkin={check_in_str}&checkout={check_out_str}"
        
        return url
    
    def _extract_hotel_name(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract hotel name from the page."""
        try:
            # First try to extract from JSON data (cleaner name)
            json_name = self._extract_hotel_name_from_json(soup)
            if json_name:
                print(f"Found hotel name in JSON: {json_name}")
                return json_name
            
            # Try multiple selectors for hotel name
            selectors = [
                'h1[data-testid="property-header"]',
                'h1.pp-header__title',
                'h1[class*="title"]',
                'h1',
                '[data-testid="property-header"] h1',
                '.hp__hotel-title',
                '.hp__hotel-name'
            ]
            
            for selector in selectors:
                element = soup.select_one(selector)
                if element:
                    name = element.get_text(strip=True)
                    if name and len(name) > 3:
                        # Clean up the name - remove extra text like "(updated prices 2025)"
                        clean_name = self._clean_hotel_name(name)
                        print(f"Found hotel name with selector '{selector}': {clean_name}")
                        return clean_name
            
            # Try to find any h1 or h2 with hotel-like text
            for tag in ['h1', 'h2']:
                elements = soup.find_all(tag)
                for element in elements:
                    text = element.get_text(strip=True)
                    if text and ('hotel' in text.lower() or 'hostel' in text.lower() or 'inn' in text.lower()):
                        clean_name = self._clean_hotel_name(text)
                        print(f"Found hotel name in {tag}: {clean_name}")
                        return clean_name
            
            print("No hotel name found")
            return None
        except Exception as e:
            logger.warning(f"Error extracting hotel name: {e}")
            return None
    
    def _extract_hotel_name_from_json(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract hotel name from JSON data embedded in the HTML."""
        try:
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    script_text = script.string
                    
                    # Look for hotel name in JSON data
                    patterns = [
                        r'"b_hotel_name":\s*[\'"]([^\'"]+)[\'"]',
                        r'"hotel_name":\s*[\'"]([^\'"]+)[\'"]',
                        r'"propertyName":\s*[\'"]([^\'"]+)[\'"]',
                        r'"name":\s*[\'"]([^\'"]+)[\'"][^}]*"@type":\s*"Hotel"',
                        r'b_hotel_name_en_with_translation:\s*[\'"]([^\'"]+)[\'"]'
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, script_text)
                        if match:
                            name = match.group(1).strip()
                            if name and len(name) > 3:
                                # Clean up the name
                                clean_name = self._clean_hotel_name(name)
                                return clean_name
            
            return None
        except Exception as e:
            logger.warning(f"Error extracting hotel name from JSON: {e}")
            return None
    
    def _clean_hotel_name(self, name: str) -> str:
        """Clean up hotel name by removing extra text."""
        # Remove common suffixes and extra information
        patterns_to_remove = [
            r'\s*\([^)]*updated prices[^)]*\)',
            r'\s*\([^)]*2025[^)]*\)',
            r'\s*\([^)]*2024[^)]*\)',
            r'\s*\([^)]*Hotel[^)]*\)',
            r'\s*\([^)]*France[^)]*\)',
            r'\s*,\s*Paris[^,]*$',
            r'\s*,\s*France[^,]*$',
            r'\s*-\s*[^-]*$',
            r'\s*★+\s*',
            r'\s*\([^)]*\)\s*$'
        ]
        
        clean_name = name
        for pattern in patterns_to_remove:
            clean_name = re.sub(pattern, '', clean_name, flags=re.IGNORECASE)
        
        # Clean up extra whitespace
        clean_name = re.sub(r'\s+', ' ', clean_name).strip()
        
        return clean_name
    
    def _extract_address(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract hotel address."""
        try:
            selectors = [
                '[data-testid="property-location"]',
                '.hp-address',
                '[class*="address"]',
                '.hp__hotel-address',
                '.hp__hotel-location',
                '[data-testid="address"]',
                '.address',
                '.location',
                '.property-address',
                '.hotel-address'
            ]
            
            for selector in selectors:
                element = soup.select_one(selector)
                if element:
                    address = element.get_text(strip=True)
                    if address and len(address) > 5:
                        print(f"Found address with selector '{selector}': {address}")
                        return address
            
            # Try to find address in meta tags
            meta_address = soup.find('meta', {'property': 'og:street-address'})
            if meta_address and meta_address.get('content'):
                print(f"Found address in meta tag: {meta_address['content']}")
                return meta_address['content']
            
            print("No address found")
            return None
        except Exception as e:
            logger.warning(f"Error extracting address: {e}")
            return None
    
    def _extract_city(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract city from address or breadcrumb."""
        try:
            # Try to extract from breadcrumb
            breadcrumb_selectors = [
                '.breadcrumb',
                '[data-testid="breadcrumb"]',
                '.hp__breadcrumb',
                'nav[aria-label*="breadcrumb"]',
                '.breadcrumbs'
            ]
            
            for selector in breadcrumb_selectors:
                breadcrumb = soup.select_one(selector)
                if breadcrumb:
                    links = breadcrumb.find_all('a')
                    if len(links) >= 2:
                        city = links[1].get_text(strip=True)
                        print(f"Found city in breadcrumb: {city}")
                        return city
            
            # Try to find city in meta tags
            meta_city = soup.find('meta', {'property': 'og:locality'})
            if meta_city and meta_city.get('content'):
                print(f"Found city in meta tag: {meta_city['content']}")
                return meta_city['content']
            
            print("No city found")
            return None
        except Exception as e:
            logger.warning(f"Error extracting city: {e}")
            return None
    
    def _extract_country(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract country from breadcrumb or address."""
        try:
            # Try breadcrumb
            breadcrumb_selectors = [
                '.breadcrumb',
                '[data-testid="breadcrumb"]',
                '.hp__breadcrumb',
                'nav[aria-label*="breadcrumb"]',
                '.breadcrumbs'
            ]
            
            for selector in breadcrumb_selectors:
                breadcrumb = soup.select_one(selector)
                if breadcrumb:
                    links = breadcrumb.find_all('a')
                    if len(links) >= 3:
                        country = links[-1].get_text(strip=True)
                        print(f"Found country in breadcrumb: {country}")
                        return country
            
            # Try to find country in meta tags
            meta_country = soup.find('meta', {'property': 'og:country-name'})
            if meta_country and meta_country.get('content'):
                print(f"Found country in meta tag: {meta_country['content']}")
                return meta_country['content']
            
            print("No country found")
            return None
        except Exception as e:
            logger.warning(f"Error extracting country: {e}")
            return None
    
    def _extract_star_rating(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract star rating."""
        try:
            selectors = [
                '[data-testid="property-star-rating"]',
                '.hp__hotel-rating',
                '[class*="star"]',
                '.star-rating',
                '.hotel-stars',
                '[aria-label*="star"]'
            ]
            
            for selector in selectors:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text(strip=True)
                    # Extract number from text like "4-star hotel"
                    match = re.search(r'(\d+)', text)
                    if match:
                        stars = float(match.group(1))
                        print(f"Found star rating with selector '{selector}': {stars}")
                        return stars
            
            # Try to find stars in aria-label
            star_elements = soup.find_all(attrs={'aria-label': re.compile(r'\d+\s*star')})
            for element in star_elements:
                aria_label = element.get('aria-label', '')
                match = re.search(r'(\d+)', aria_label)
                if match:
                    stars = float(match.group(1))
                    print(f"Found star rating in aria-label: {stars}")
                    return stars
            
            print("No star rating found")
            return None
        except Exception as e:
            logger.warning(f"Error extracting star rating: {e}")
            return None
    
    def _extract_user_rating(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract user rating score."""
        try:
            selectors = [
                '[data-testid="review-score"] .b5cd09854e',
                '.hp__hotel-rating-score',
                '[class*="rating"]',
                '.review-score',
                '.user-rating',
                '[data-testid="review-score"]',
                '.hp__hotel-rating'
            ]
            
            for selector in selectors:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text(strip=True)
                    # Extract number from text
                    match = re.search(r'(\d+\.?\d*)', text)
                    if match:
                        rating = float(match.group(1))
                        # Normalize to 0-10 scale if needed
                        if rating > 10:
                            rating = rating / 10
                        print(f"Found user rating with selector '{selector}': {rating}")
                        return rating
            
            # Try to find rating in data attributes
            rating_elements = soup.find_all(attrs={'data-testid': 'review-score'})
            for element in rating_elements:
                # Look for rating in child elements
                rating_text = element.get_text(strip=True)
                match = re.search(r'(\d+\.?\d*)', rating_text)
                if match:
                    rating = float(match.group(1))
                    if rating > 10:
                        rating = rating / 10
                    print(f"Found user rating in review-score: {rating}")
                    return rating
            
            print("No user rating found")
            return None
        except Exception as e:
            logger.warning(f"Error extracting user rating: {e}")
            return None
    
    def _extract_rating_count(self, soup: BeautifulSoup) -> Optional[int]:
        """Extract number of reviews."""
        try:
            selectors = [
                '[data-testid="review-score"] .b5cd09854e + span',
                '.hp__hotel-rating-score + span',
                '[class*="review-count"]',
                '.review-count',
                '.reviews-count'
            ]
            
            for selector in selectors:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text(strip=True)
                    # Extract number from text like "1,234 reviews"
                    match = re.search(r'([\d,]+)', text)
                    if match:
                        count_str = match.group(1).replace(',', '')
                        count = int(count_str)
                        print(f"Found rating count with selector '{selector}': {count}")
                        return count
            
            # Try to find reviews count in the same area as rating
            rating_elements = soup.find_all(attrs={'data-testid': 'review-score'})
            for element in rating_elements:
                # Look for review count in nearby text
                parent = element.parent
                if parent:
                    text = parent.get_text(strip=True)
                    match = re.search(r'([\d,]+)\s*reviews?', text, re.IGNORECASE)
                    if match:
                        count_str = match.group(1).replace(',', '')
                        count = int(count_str)
                        print(f"Found rating count near review-score: {count}")
                        return count
            
            print("No rating count found")
            return None
        except Exception as e:
            logger.warning(f"Error extracting rating count: {e}")
            return None
    
    def _extract_amenities(self, soup: BeautifulSoup) -> List[str]:
        """Extract hotel amenities."""
        amenities = []
        try:
            # First try HTML selectors
            selectors = [
                '[data-testid="property-facilities"] .b5cd09854e',
                '.hp-amenity-list li',
                '[class*="amenity"]',
                '.amenities li',
                '.facilities li',
                '[data-testid="facilities"] li',
                '.hp__hotel-amenities li',
                '[data-testid="facility-icon"]',
                '[data-testid="amenity-icon"]'
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                for element in elements:
                    # Try to get text from the element or its parent
                    amenity_text = element.get_text(strip=True)
                    if not amenity_text:
                        # Try to get text from parent or sibling
                        parent = element.parent
                        if parent:
                            amenity_text = parent.get_text(strip=True)
                    
                    if amenity_text and len(amenity_text) > 2 and len(amenity_text) < 100:
                        amenities.append(amenity_text)
                
                if amenities:
                    print(f"Found {len(amenities)} amenities with selector '{selector}'")
                    break
            
            # Remove duplicates and clean
            amenities = list(set(amenities))
            print(f"Total unique amenities found: {len(amenities)}")
            return amenities[:20]  # Limit to 20 amenities
            
        except Exception as e:
            logger.warning(f"Error extracting amenities: {e}")
            return []
    
    def _extract_latitude(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract latitude from page."""
        try:
            # Look for latitude in script tags
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    # Look for latitude in JSON data
                    match = re.search(r'"latitude":\s*([\d.-]+)', script.string)
                    if match:
                        return float(match.group(1))
            
            return None
        except Exception as e:
            logger.warning(f"Error extracting latitude: {e}")
            return None
    
    def _extract_longitude(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract longitude from page."""
        try:
            # Look for longitude in script tags
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    # Look for longitude in JSON data
                    match = re.search(r'"longitude":\s*([\d.-]+)', script.string)
                    if match:
                        return float(match.group(1))
            
            return None
        except Exception as e:
            logger.warning(f"Error extracting longitude: {e}")
            return None
    
    def _extract_currency(self, soup: BeautifulSoup) -> str:
        """Extract currency symbol."""
        try:
            selectors = [
                '[data-testid="price-and-discounted-price"]',
                '.hp__hotel-rate',
                '[class*="price"]'
            ]
            
            for selector in selectors:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text(strip=True)
                    # Look for currency symbols
                    if '€' in text:
                        return 'EUR'
                    elif '$' in text:
                        return 'USD'
                    elif '£' in text:
                        return 'GBP'
            
            return 'EUR'  # Default
        except Exception as e:
            logger.warning(f"Error extracting currency: {e}")
            return 'EUR'
    
    def _extract_room_type(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract room type."""
        try:
            selectors = [
                '[data-testid="room-type"]',
                '.hp__room-type',
                '[class*="room"]',
                '.room-type',
                '.room-name'
            ]
            
            for selector in selectors:
                element = soup.select_one(selector)
                if element:
                    room_type = element.get_text(strip=True)
                    if room_type and len(room_type) < 100:  # Avoid huge strings
                        print(f"Found room type with selector '{selector}': {room_type}")
                        return room_type
            
            # Try to extract from the page title or breadcrumb
            title = soup.find('title')
            if title:
                title_text = title.get_text(strip=True)
                # Look for room type in title
                if 'single' in title_text.lower():
                    return 'Single Room'
                elif 'double' in title_text.lower():
                    return 'Double Room'
                elif 'twin' in title_text.lower():
                    return 'Twin Room'
                elif 'suite' in title_text.lower():
                    return 'Suite'
            
            print("No room type found")
            return None
        except Exception as e:
            logger.warning(f"Error extracting room type: {e}")
            return None
    
    def _extract_board_type(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract board type (breakfast, half-board, etc.)."""
        try:
            # First try HTML selectors
            selectors = [
                '[data-testid="board-type"]',
                '.hp__board-type',
                '[class*="board"]',
                '.board-type',
                '.meal-plan',
                '.breakfast-info',
                '.meal-info'
            ]
            
            for selector in selectors:
                element = soup.select_one(selector)
                if element:
                    board_type = element.get_text(strip=True)
                    if board_type and len(board_type) < 50:  # Avoid huge strings
                        print(f"Found board type with selector '{selector}': {board_type}")
                        return board_type
            
            # Try to find breakfast information in text
            breakfast_keywords = ['breakfast', 'meal', 'board', 'dining']
            for keyword in breakfast_keywords:
                elements = soup.find_all(text=re.compile(keyword, re.IGNORECASE))
                for element in elements:
                    if element.parent:
                        text = element.parent.get_text(strip=True)
                        if len(text) < 100 and keyword in text.lower():
                            print(f"Found board type with keyword '{keyword}': {text}")
                            return text
            
            print("No board type found")
            return None
        except Exception as e:
            logger.warning(f"Error extracting board type: {e}")
            return None

    def _extract_json_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract hotel data from JSON embedded in the HTML."""
        try:
            # Look for JSON data in script tags
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    # Look for JSON data with hotel information
                    script_text = script.string
                    
                    # Try to find formattedAddress
                    address_match = re.search(r'"formattedAddress":"([^"]+)"', script_text)
                    if address_match:
                        address = address_match.group(1)
                        print(f"Found address in JSON: {address}")
                        
                        # Extract city and country from address
                        parts = address.split(',')
                        if len(parts) >= 3:
                            # Format: "17 rue Beauregard, 2nd arr., 75002 Paris, France"
                            city_part = parts[-2].strip()  # "75002 Paris"
                            country = parts[-1].strip()  # "France"
                            
                            # Clean up city (remove postal code)
                            city_match = re.search(r'(\d+\s+)?(.+)', city_part)
                            if city_match:
                                city = city_match.group(2).strip()  # "Paris"
                            else:
                                city = city_part
                        elif len(parts) >= 2:
                            city_part = parts[-2].strip()
                            country = parts[-1].strip()
                            
                            # Clean up city (remove postal code)
                            city_match = re.search(r'(\d+\s+)?(.+)', city_part)
                            if city_match:
                                city = city_match.group(2).strip()
                            else:
                                city = city_part
                        else:
                            city = None
                            country = None
                        
                        return {
                            'address': address,
                            'city': city,
                            'country': country
                        }
            
            return {}
        except Exception as e:
            logger.warning(f"Error extracting JSON data: {e}")
            return {}
    
    def _extract_review_score_from_json(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract review score from JSON data."""
        try:
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    script_text = script.string
                    
                    # Look for review score in various formats
                    patterns = [
                        r'"b_review_score_detailed":\s*[\'"]([0-9.]+)[\'"]',
                        r'"review_score":\s*[\'"]([0-9.]+)[\'"]',
                        r'data-review-score="([0-9.]+)"',
                        r'review_score["\']?\s*:\s*["\']?([0-9.]+)',
                        r'b_review_score_detailed["\']?\s*:\s*["\']?([0-9.]+)'
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, script_text)
                        if match:
                            score = float(match.group(1))
                            print(f"Found review score in JSON: {score}")
                            return score
            
            return None
        except Exception as e:
            logger.warning(f"Error extracting review score from JSON: {e}")
            return None
    
    def _extract_amenities_from_json(self, soup: BeautifulSoup) -> List[str]:
        """Extract amenities from JSON data."""
        try:
            amenities = []
            scripts = soup.find_all('script')
            
            for script in scripts:
                if script.string:
                    script_text = script.string
                    
                    # Look for amenities in JSON - BaseFacility titles
                    amenity_patterns = [
                        r'"title":"([^"]+)"[^}]*"__typename":"BaseFacility"',
                        r'"title":"([^"]+)"[^}]*"__typename":"GenericFacilityHighlight"',
                        r'"title":"([^"]+)"[^}]*"__typename":"WifiFacilityHighlight"',
                        r'"title":"([^"]+)"[^}]*"level":"(?:room|property)"',
                        r'"title":"([^"]+)"[^}]*"slug":"[^"]*"'
                    ]
                    
                    for pattern in amenity_patterns:
                        matches = re.findall(pattern, script_text)
                        for match in matches:
                            if match and len(match) > 2 and match not in amenities:
                                amenities.append(match)
            
            # Remove duplicates and clean
            amenities = list(set(amenities))
            print(f"Found {len(amenities)} amenities in JSON")
            return amenities[:20]  # Limit to 20
            
        except Exception as e:
            logger.warning(f"Error extracting amenities from JSON: {e}")
            return []
    
    def _extract_board_type_from_json(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract board type from JSON data."""
        try:
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    script_text = script.string
                    
                    # Look for board type in JSON
                    board_patterns = [
                        r'"breakfast":"([^"]+)"',
                        r'"mealplan_vector/name":\s*\{[^}]*"([^"]+)":\s*"([^"]+)"',
                        r'"board_type":\s*"([^"]+)"',
                        r'"meal_plan":\s*"([^"]+)"'
                    ]
                    
                    for pattern in board_patterns:
                        matches = re.findall(pattern, script_text)
                        for match in matches:
                            if isinstance(match, tuple):
                                # Handle tuple matches
                                for item in match:
                                    if item and len(item) > 3:
                                        print(f"Found board type in JSON: {item}")
                                        return item
                            else:
                                # Handle string matches
                                if match and len(match) > 3:
                                    print(f"Found board type in JSON: {match}")
                                    return match
            
            return None
        except Exception as e:
            logger.warning(f"Error extracting board type from JSON: {e}")
            return None
    
    def _extract_room_types_from_json(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract room types and prices from JSON data."""
        try:
            rooms_data = []
            scripts = soup.find_all('script')
            
            for script in scripts:
                if script.string:
                    script_text = script.string
                    
                    # Look for room data in JSON - more comprehensive patterns
                    room_patterns = [
                        r'"roomType":\s*"([^"]+)"[^}]*"price":\s*([\d.]+)',
                        r'"type":\s*"([^"]+)"[^}]*"amount":\s*([\d.]+)',
                        r'"name":\s*"([^"]+)"[^}]*"price":\s*([\d.]+)',
                        r'"room_type":\s*"([^"]+)"[^}]*"price":\s*([\d.]+)',
                        r'"roomName":\s*"([^"]+)"[^}]*"price":\s*([\d.]+)',
                        r'"room_name":\s*"([^"]+)"[^}]*"price":\s*([\d.]+)',
                        r'"title":\s*"([^"]+)"[^}]*"price":\s*([\d.]+)',
                        # Look for room arrays
                        r'"rooms":\s*\[([^\]]+)\]',
                        r'"roomTypes":\s*\[([^\]]+)\]',
                        r'"accommodations":\s*\[([^\]]+)\]'
                    ]
                    
                    for pattern in room_patterns:
                        if 'rooms' in pattern or 'roomTypes' in pattern or 'accommodations' in pattern:
                            # Handle room arrays
                            match = re.search(pattern, script_text)
                            if match:
                                room_array_text = match.group(1)
                                # Extract individual room objects from array
                                room_objects = re.findall(r'\{[^}]+\}', room_array_text)
                                for room_obj in room_objects:
                                    # Extract room name and price from each object
                                    name_match = re.search(r'"name":\s*"([^"]+)"', room_obj)
                                    price_match = re.search(r'"price":\s*([\d.]+)', room_obj)
                                    if name_match and price_match:
                                        room_type = name_match.group(1)
                                        try:
                                            price = float(price_match.group(1))
                                            if price > 0 and price < 10000:
                                                rooms_data.append({
                                                    'room_type': room_type,
                                                    'price': price,
                                                    'board_type': None,
                                                    'currency': 'EUR'
                                                })
                                        except ValueError:
                                            continue
                        else:
                            # Handle simple room patterns
                            matches = re.findall(pattern, script_text)
                            for match in matches:
                                room_type = match[0]
                                try:
                                    price = float(match[1])
                                    if price > 0 and price < 10000:
                                        rooms_data.append({
                                            'room_type': room_type,
                                            'price': price,
                                            'board_type': None,
                                            'currency': 'EUR'
                                        })
                                except ValueError:
                                    continue
            
            return rooms_data
            
        except Exception as e:
            logger.warning(f"Error extracting room types from JSON: {e}")
            return []

# Example usage
if __name__ == "__main__":
    scraper = BookingScraper()
    
    # Example search results URL
    search_url = "https://www.booking.com/searchresults.html?ss=London&checkin=2024-06-15&checkout=2024-06-17"
    
    # Extract data from search results
    data = scraper.extract_hotel_data(search_url)
    
    print(json.dumps(data, indent=2, default=str)) 