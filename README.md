# Hotel Monitoring MVP

A comprehensive hotel monitoring and yield strategy simulation platform that tracks competitor hotels, analyzes pricing trends, and provides yield management recommendations.

## 🏨 Core Features

### Hotel Monitoring
- Add competitor hotels via Booking.com URLs
- Extract and store pricing, ratings, amenities, and location data
- Track historical price evolution over time
- Real-time dashboard with competitor analysis

### Yield Strategy Simulation
- Define your hotel's historical data (prices, reservations, booking curves)
- Simulate booking pace trends and compare with market
- Receive intelligent recommendations for pricing strategies

### Smart Criteria Weighting
- Customize feature importance by season
- Dynamic competitor ranking based on weighted criteria
- Seasonal amenity relevance (e.g., pool importance in summer vs winter)

### Event Sensitivity Analysis
- Manual event registration for cities/dates
- Correlation analysis between events and pricing surges
- Event-driven pricing recommendations

## 🏗️ Technical Architecture

### Frontend
- **Stack**: React + Vite + TypeScript + Material-UI
- **State Management**: React Query (TanStack)
- **Charts**: Recharts
- **Pages**: Hotel List, Add Hotel, Analytics, Settings

### Backend
- **Stack**: FastAPI (Python)
- **Database**: SQLite
- **Scraping**: BeautifulSoup4 + requests
- **API Endpoints**: Scraping, hotel management, analytics, recommendations

### Scraper
- **Libraries**: requests, BeautifulSoup4
- **Features**: User-Agent rotation, rate limiting, graceful error handling
- **Data**: Hotel details, pricing, ratings, amenities

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd hotelmonitoringmvp
   ```

2. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Access the Application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## 📊 Usage

1. **Add Competitor Hotels**: Use the "Add Hotel" page to input Booking.com URLs
2. **Monitor Dashboard**: View real-time competitor data and pricing trends
3. **Analytics**: Analyze historical price evolution and booking patterns
4. **Settings**: Configure criteria weights and add local events
5. **Recommendations**: Get yield management suggestions based on market analysis

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the backend directory:
```env
DATABASE_URL=sqlite:///./hotel_monitoring.db
SCRAPER_DELAY=2
MAX_RETRIES=3
```

### Customization
- Modify criteria weights in Settings page
- Add local events for your target markets
- Upload historical data for your hotel

## 📈 Features in Detail

### Hotel Monitoring
- Real-time price tracking for specified dates (J+3, J+7, etc.)
- Star rating and user review analysis
- Amenity comparison and scoring
- Location-based competitor analysis

### Yield Strategy
- Historical data upload (CSV/JSON)
- Booking curve analysis
- Market comparison algorithms
- Automated pricing recommendations

### Smart Analytics
- Seasonal weight adjustments
- Event correlation analysis
- Trend prediction models
- Competitive positioning insights

## 🤝 Contributing

This is an MVP for local development and non-commercial use. For commercial applications, ensure compliance with Booking.com's terms of service and implement appropriate rate limiting and data usage policies.

## 📝 License

This project is for educational and MVP purposes. Please respect Booking.com's terms of service when using the scraper functionality. 