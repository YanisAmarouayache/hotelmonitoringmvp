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
}

export interface HotelPrice {
  id: number;
  hotel_id: number;
  check_in_date: string;
  check_out_date: string;
  price: number;
  currency: string;
  room_type: string | null;
  board_type: string | null;
  created_at: string;
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
export const getHotel = async (id: number): Promise<Hotel> => {
  const response = await axios.get(`${API_BASE_URL}/hotels/${id}`);
  return response.data;
};

// Add hotel (scrape and add)
export const addHotel = async (request: ScrapingRequest): Promise<ScrapingResponse> => {
  const response = await axios.post(`${API_BASE_URL}/scraping/hotel`, request);
  return response.data;
};

// Update hotel prices
export const updateHotelPrices = async (
  hotelId: number,
  checkInDate?: string,
  checkOutDate?: string
): Promise<{ success: boolean; price_data?: HotelPrice; message?: string }> => {
  const response = await axios.post(`${API_BASE_URL}/scraping/update-prices/${hotelId}`, {
    check_in_date: checkInDate,
    check_out_date: checkOutDate
  });
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