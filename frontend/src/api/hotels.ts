import axios from 'axios';

const API_BASE_URL = '/api';

export interface Hotel {
  id: number;
  name: string;
  booking_url: string;
  address: string;
  city: string;
  country: string;
  star_rating: number | null;
  user_rating: number | null;
  user_rating_count: number | null;
  amenities: string[];
  latitude: number | null;
  longitude: number | null;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

export interface HotelPrice {
  id: number;
  hotel_id: number;
  room_type: string;
  price: number;
  currency: string;
  check_in_date: string;
  check_out_date: string;
  scraped_at: string;
  board_type: string | null;
  source: string;
}

export interface HotelWithPrices extends Hotel {
  prices: HotelPrice[];
}

export interface ScrapingRequest {
  booking_url: string;
  check_in_date?: string;
  check_out_date?: string;
  room_type?: string;
  board_type?: string;
}

export interface ScrapingResponse {
  success: boolean;
  hotel_data?: Hotel;
  price_data?: HotelPrice;
  guest_info?: {
    adults?: number;
    children?: number;
  };
  error?: string;
}

// Get all hotels
export const getHotels = async (): Promise<Hotel[]> => {
  console.log('Fetching hotels from API...');
  const response = await axios.get(`${API_BASE_URL}/hotels`);
  console.log('API response:', response.data);
  return response.data;
};

// Get hotel by ID
export const getHotel = async (id: number): Promise<HotelWithPrices> => {
  const response = await axios.get(`${API_BASE_URL}/hotels/${id}/with-prices`);
  return response.data;
};

// Add hotel (scrape and add)
export const addHotel = async (request: ScrapingRequest): Promise<ScrapingResponse> => {
  const response = await axios.post(`${API_BASE_URL}/scraping/hotel`, request);
  return response.data;
};

// Delete hotel
export const deleteHotel = async (id: number): Promise<void> => {
  await axios.delete(`${API_BASE_URL}/hotels/${id}`);
};

// Get hotel prices
export const getHotelPrices = async (hotelId: number): Promise<HotelPrice[]> => {
  const response = await axios.get(`${API_BASE_URL}/hotels/${hotelId}/prices`);
  return response.data;
};

// Scrape date range for hotel
export const scrapeDateRange = async (
  hotelId: number,
  startDate: string,
  endDate: string
): Promise<{
  success: boolean;
  message?: string;
  date_range?: {
    start_date: string;
    end_date: string;
    total_days: number;
  };
  results?: {
    successful_scrapes: number;
    failed_scrapes: number;
    total_prices_added: number;
  };
  error?: string;
}> => {
  const response = await axios.post(`${API_BASE_URL}/scraping/scrape-date-range/${hotelId}`, {
    start_date: startDate,
    end_date: endDate
  });
  return response.data;
}; 