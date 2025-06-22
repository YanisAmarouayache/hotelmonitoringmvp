import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Chip,
  Rating,
  Divider,
  Tabs,
  Tab,
  Button,
  Alert,
  CircularProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  TextField,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import {
  LocationOn as LocationIcon,
  Star as StarIcon,
  Wifi as WifiIcon,
  Restaurant as RestaurantIcon,
  LocalParking as ParkingIcon,
  FitnessCenter as GymIcon,
  Pool as PoolIcon,
  Spa as SpaIcon,
  BusinessCenter as BusinessIcon,
  ArrowBack as ArrowBackIcon,
  Refresh as RefreshIcon,
  TrendingUp as TrendingUpIcon,
  AttachMoney as MoneyIcon,
  CalendarToday as CalendarIcon,
  ExpandMore as ExpandMoreIcon,
  DateRange as DateRangeIcon
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams, useNavigate } from 'react-router-dom';
import { getHotel, getHotelPrices, scrapeDateRange } from '../api/hotels';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`hotel-tabpanel-${index}`}
      aria-labelledby={`hotel-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const HotelDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [tabValue, setTabValue] = useState(0);
  const [checkInDate, setCheckInDate] = useState('');
  const [checkOutDate, setCheckOutDate] = useState('');
  const [dateError, setDateError] = useState('');
  
  // Date range scraping state
  const [rangeStartDate, setRangeStartDate] = useState('');
  const [rangeEndDate, setRangeEndDate] = useState('');
  const [rangeDateError, setRangeDateError] = useState('');
  const [showRangeScraping, setShowRangeScraping] = useState(false);
  
  const queryClient = useQueryClient();

  const { data: hotel, isLoading: hotelLoading, error: hotelError } = useQuery({
    queryKey: ['hotel', id],
    queryFn: () => getHotel(Number(id)),
    enabled: !!id
  });

  const scrapeRangeMutation = useMutation({
    mutationFn: ({ hotelId, startDate, endDate }: { hotelId: number; startDate: string; endDate: string }) =>
      scrapeDateRange(hotelId, startDate, endDate),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['hotel', id] });
      setRangeDateError(''); // Clear any date errors on success
      console.log('Date range scraping completed:', data);
    },
    onError: (error) => {
      console.error('Failed to scrape date range:', error);
    }
  });

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  // Clear date error when dates change
  const handleDateChange = (field: 'checkIn' | 'checkOut', value: string) => {
    if (field === 'checkIn') {
      setCheckInDate(value);
    } else {
      setCheckOutDate(value);
    }
    setDateError(''); // Clear error when user changes dates
  };

  // Validate dates
  const validateDates = () => {
    if (!checkInDate || !checkOutDate) {
      setDateError('Please select both check-in and check-out dates');
      return false;
    }
    
    const checkIn = new Date(checkInDate);
    const checkOut = new Date(checkOutDate);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    if (checkIn < today) {
      setDateError('Check-in date cannot be in the past');
      return false;
    }
    
    if (checkOut <= checkIn) {
      setDateError('Check-out date must be after check-in date');
      return false;
    }
    
    setDateError('');
    return true;
  };

  const handleScrapeDateRange = () => {
    if (!validateDates()) {
      return;
    }
    
    if (hotel) {
      scrapeRangeMutation.mutate({
        hotelId: hotel.id,
        startDate: checkInDate,
        endDate: checkOutDate
      });
    }
  };

  // Clear range date error when dates change
  const handleRangeDateChange = (field: 'start' | 'end', value: string) => {
    if (field === 'start') {
      setRangeStartDate(value);
    } else {
      setRangeEndDate(value);
    }
    setRangeDateError(''); // Clear error when user changes dates
  };

  // Set default dates (tomorrow and day after tomorrow)
  React.useEffect(() => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const dayAfterTomorrow = new Date();
    dayAfterTomorrow.setDate(dayAfterTomorrow.getDate() + 2);
    
    setCheckInDate(tomorrow.toISOString().split('T')[0]);
    setCheckOutDate(dayAfterTomorrow.toISOString().split('T')[0]);
    
    // Set default range dates (next week)
    const nextWeek = new Date();
    nextWeek.setDate(nextWeek.getDate() + 7);
    const nextWeekPlus5 = new Date();
    nextWeekPlus5.setDate(nextWeekPlus5.getDate() + 12);
    
    setRangeStartDate(nextWeek.toISOString().split('T')[0]);
    setRangeEndDate(nextWeekPlus5.toISOString().split('T')[0]);
  }, []);

  const getAmenityIcon = (amenity: string) => {
    const amenityLower = amenity.toLowerCase();
    if (amenityLower.includes('wifi') || amenityLower.includes('internet')) return <WifiIcon />;
    if (amenityLower.includes('restaurant') || amenityLower.includes('breakfast')) return <RestaurantIcon />;
    if (amenityLower.includes('parking')) return <ParkingIcon />;
    if (amenityLower.includes('gym') || amenityLower.includes('fitness')) return <GymIcon />;
    if (amenityLower.includes('pool')) return <PoolIcon />;
    if (amenityLower.includes('spa')) return <SpaIcon />;
    if (amenityLower.includes('business')) return <BusinessIcon />;
    return <WifiIcon />; // Default icon
  };

  const formatPrice = (price: number | null, currency: string = 'EUR') => {
    if (price === null) return 'N/A';
    return `${Math.floor(price*100)/100} ${currency}`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  if (hotelLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (hotelError) {
    return (
      <Box p={3}>
        <Alert severity="error">
          Failed to load hotel details: {hotelError instanceof Error ? hotelError.message : 'Unknown error'}
        </Alert>
      </Box>
    );
  }

  if (!hotel) {
    return (
      <Box p={3}>
        <Alert severity="warning">Hotel not found</Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box display="flex" alignItems="center" gap={2} mb={3}>
        <IconButton onClick={() => navigate('/hotels')}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h4" component="h1">
          {hotel.name}
        </Typography>
      </Box>

      {/* Main Content */}
      <Grid container spacing={3}>
        {/* Left Column - Hotel Info */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h5" gutterBottom>
              Hotel Information
            </Typography>
            
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <Box display="flex" alignItems="center" gap={1} mb={2}>
                  <LocationIcon color="action" />
                  <Box>
                    <Typography variant="body1">{hotel.city}</Typography>
                    <Typography variant="body2" color="text.secondary">
                      {hotel.country}
                    </Typography>
                  </Box>
                </Box>
                
                <Typography variant="body2" color="text.secondary" mb={2}>
                  {hotel.address}
                </Typography>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <Box display="flex" alignItems="center" gap={1} mb={2}>
                  <StarIcon color="warning" />
                  <Typography variant="body1">
                    {hotel.star_rating ? `${hotel.star_rating} Stars` : 'N/A'}
                  </Typography>
                </Box>
                
                {hotel.user_rating && (
                  <Box display="flex" alignItems="center" gap={1} mb={2}>
                    <Rating value={hotel.user_rating / 2} precision={0.1} size="small" readOnly />
                    <Typography variant="body2">
                      {hotel.user_rating.toFixed(1)}/10
                    </Typography>
                  </Box>
                )}
              </Grid>
            </Grid>

            <Divider sx={{ my: 2 }} />

            {/* Amenities */}
            {hotel.amenities && hotel.amenities.length > 0 && (
              <Box>
                <Typography variant="h6" gutterBottom>
                  Amenities
                </Typography>
                <Grid container spacing={1}>
                  {hotel.amenities.map((amenity, index) => (
                    <Grid item key={index}>
                      <Chip
                        icon={getAmenityIcon(amenity)}
                        label={amenity}
                        variant="outlined"
                        size="small"
                      />
                    </Grid>
                  ))}
                </Grid>
              </Box>
            )}
          </Paper>

          {/* Tabs */}
          <Paper>
            <Tabs value={tabValue} onChange={handleTabChange} aria-label="hotel details tabs">
              <Tab label="Current Rooms & Prices" />
              <Tab label="Price History" />
              <Tab label="Prices by Date" />
              <Tab label="Analytics" />
              <Tab label="Competitors" />
              <Tab label="Settings" />
            </Tabs>
            
            <TabPanel value={tabValue} index={0}>
              <Typography variant="h6" gutterBottom>Current Rooms & Prices</Typography>
              
              {/* Scraping Section */}
              <Paper sx={{ p: 3, mb: 3 }}>
                <Typography variant="subtitle1" gutterBottom>Update Prices for Date Range</Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Enter dates to update prices for this hotel across the specified range
                </Typography>
                
                <Grid container spacing={2} alignItems="center">
                  <Grid item xs={12} sm={4}>
                    <TextField
                      label="Check-in Date"
                      type="date"
                      value={checkInDate}
                      onChange={(e) => handleDateChange('checkIn', e.target.value)}
                      fullWidth
                      size="small"
                      InputLabelProps={{ shrink: true }}
                      error={!!dateError}
                    />
                  </Grid>
                  <Grid item xs={12} sm={4}>
                    <TextField
                      label="Check-out Date"
                      type="date"
                      value={checkOutDate}
                      onChange={(e) => handleDateChange('checkOut', e.target.value)}
                      fullWidth
                      size="small"
                      InputLabelProps={{ shrink: true }}
                      error={!!dateError}
                    />
                  </Grid>
                  <Grid item xs={12} sm={4}>
                    <Button
                      variant="contained"
                      startIcon={<RefreshIcon />}
                      onClick={handleScrapeDateRange}
                      disabled={scrapeRangeMutation.isPending || !checkInDate || !checkOutDate}
                      fullWidth
                    >
                      {scrapeRangeMutation.isPending ? 'Updating...' : 'Update Prices'}
                    </Button>
                  </Grid>
                </Grid>
                
                {dateError && (
                  <Alert severity="error" sx={{ mt: 2 }}>
                    {dateError}
                  </Alert>
                )}
                
                {scrapeRangeMutation.isSuccess && scrapeRangeMutation.data && (
                  <Alert severity="success" sx={{ mt: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Date Range Updating Completed!
                    </Typography>
                    <Typography variant="body2">
                      Successfully updated {scrapeRangeMutation.data.results?.successful_scrapes || 0} days
                      ({scrapeRangeMutation.data.results?.failed_scrapes || 0} failed)
                    </Typography>
                    <Typography variant="body2">
                      Total prices added: {scrapeRangeMutation.data.results?.total_prices_added || 0}
                    </Typography>
                  </Alert>
                )}
                
                {scrapeRangeMutation.isError && (
                  <Alert severity="error" sx={{ mt: 2 }}>
                    Failed to update date range: {scrapeRangeMutation.error instanceof Error 
                      ? scrapeRangeMutation.error.message 
                      : 'Unknown error'
                    }
                  </Alert>
                )}
              </Paper>

              {/* Date Range Scraping Section */}
              <Paper sx={{ p: 3, mb: 3 }}>
                <Box display="flex" alignItems="center" gap={1} mb={2}>
                  <DateRangeIcon color="primary" />
                  <Typography variant="subtitle1">Scrape Daily Prices (Date Range)</Typography>
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Scrape prices for each day in a date range. This will create price records for consecutive 1-night stays.
                </Typography>
                
                <Grid container spacing={2} alignItems="center">
                  <Grid item xs={12} sm={3}>
                    <TextField
                      label="Start Date"
                      type="date"
                      value={rangeStartDate}
                      onChange={(e) => handleRangeDateChange('start', e.target.value)}
                      fullWidth
                      size="small"
                      InputLabelProps={{ shrink: true }}
                      error={!!rangeDateError}
                    />
                  </Grid>
                  <Grid item xs={12} sm={3}>
                    <TextField
                      label="End Date"
                      type="date"
                      value={rangeEndDate}
                      onChange={(e) => handleRangeDateChange('end', e.target.value)}
                      fullWidth
                      size="small"
                      InputLabelProps={{ shrink: true }}
                      error={!!rangeDateError}
                    />
                  </Grid>
                  <Grid item xs={12} sm={3}>
                    <Button
                      variant="contained"
                      color="secondary"
                      startIcon={<DateRangeIcon />}
                      onClick={handleScrapeDateRange}
                      disabled={scrapeRangeMutation.isPending || !rangeStartDate || !rangeEndDate}
                      fullWidth
                    >
                      {scrapeRangeMutation.isPending ? 'Scraping Range...' : 'Scrape Date Range'}
                    </Button>
                  </Grid>
                  <Grid item xs={12} sm={3}>
                    <Typography variant="caption" color="text.secondary">
                      Max 30 days
                    </Typography>
                  </Grid>
                </Grid>
                
                {rangeDateError && (
                  <Alert severity="error" sx={{ mt: 2 }}>
                    {rangeDateError}
                  </Alert>
                )}
                
                {scrapeRangeMutation.isSuccess && scrapeRangeMutation.data && (
                  <Alert severity="success" sx={{ mt: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Date Range Scraping Completed!
                    </Typography>
                    <Typography variant="body2">
                      Successfully scraped {scrapeRangeMutation.data.results?.successful_scrapes || 0} days
                      ({scrapeRangeMutation.data.results?.failed_scrapes || 0} failed)
                    </Typography>
                    <Typography variant="body2">
                      Total prices added: {scrapeRangeMutation.data.results?.total_prices_added || 0}
                    </Typography>
                  </Alert>
                )}
                
                {scrapeRangeMutation.isError && (
                  <Alert severity="error" sx={{ mt: 2 }}>
                    Failed to update date range: {scrapeRangeMutation.error instanceof Error 
                      ? scrapeRangeMutation.error.message 
                      : 'Unknown error'
                    }
                  </Alert>
                )}
              </Paper>

              {/* Current Prices Display */}
              <Typography variant="subtitle1" gutterBottom>Recent Prices</Typography>
              {hotel.prices && hotel.prices.length > 0 ? (
                <Box>
                  {/* Summary stats */}
                  <Paper sx={{ p: 2, mb: 3 }}>
                    <Grid container spacing={2}>
                      <Grid item xs={12} sm={3}>
                        <Box textAlign="center">
                          <Typography variant="h4" color="primary">
                            {hotel.prices.length}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Total Price Records
                          </Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={12} sm={3}>
                        <Box textAlign="center">
                          <Typography variant="h4" color="secondary">
                            {new Set(hotel.prices.map(p => p.check_in_date.split('T')[0])).size}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Unique Dates
                          </Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={12} sm={3}>
                        <Box textAlign="center">
                          <Typography variant="h4" color="info.main">
                            {new Set(hotel.prices.map(p => p.room_type)).size}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Room Types
                          </Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={12} sm={3}>
                        <Box textAlign="center">
                          <Typography variant="h4" color="success.main">
                            {formatPrice(
                              hotel.prices.reduce((sum, p) => sum + (p.price || 0), 0) / hotel.prices.length,
                              'EUR'
                            )}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Average Price
                          </Typography>
                        </Box>
                      </Grid>
                    </Grid>
                  </Paper>

                  {/* Recent prices by date */}
                  {(() => {
                    const pricesByDate: { [key: string]: typeof hotel.prices } = {};
                    
                    // Group prices by check-in date
                    hotel.prices.forEach(price => {
                      const checkInDate = price.check_in_date.split('T')[0];
                      if (!pricesByDate[checkInDate]) {
                        pricesByDate[checkInDate] = [];
                      }
                      pricesByDate[checkInDate].push(price);
                    });

                    // Get the 3 most recent dates
                    const sortedDates = Object.keys(pricesByDate)
                      .sort()
                      .reverse()
                      .slice(0, 3);
                    
                    return sortedDates.map((date) => {
                      const datePrices = pricesByDate[date];
                      const nextDay = new Date(date);
                      nextDay.setDate(nextDay.getDate() + 1);
                      const nextDayStr = nextDay.toISOString().split('T')[0];
                      
                      return (
                        <Paper key={date} sx={{ p: 2, mb: 2 }}>
                          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                            <Typography variant="h6">
                              {formatDate(date)} - {formatDate(nextDayStr)}
                            </Typography>
                            <Chip 
                              label={`${datePrices.length} prices`} 
                              color="primary" 
                              size="small" 
                            />
                          </Box>
                          
                          <Grid container spacing={2}>
                            {datePrices
                              .sort((a, b) => new Date(b.scraped_at).getTime() - new Date(a.scraped_at).getTime())
                              .slice(0, 6) // Show max 6 prices per date
                              .map((price) => (
                                <Grid item xs={12} sm={6} md={4} key={price.id}>
                                  <Card variant="outlined">
                                    <CardContent>
                                      <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
                                        <Typography variant="h6" color="primary">
                                          {formatPrice(price.price, price.currency)}
                                        </Typography>
                                        <Typography variant="caption" color="text.secondary">
                                          {formatDate(price.scraped_at)}
                                        </Typography>
                                      </Box>
                                      <Typography variant="body2" color="text.secondary" gutterBottom>
                                        {price.room_type}
                                      </Typography>
                                      {price.board_type && (
                                        <Typography variant="body2" color="text.secondary" gutterBottom>
                                          {price.board_type}
                                        </Typography>
                                      )}
                                      <Typography variant="caption" color="text.secondary">
                                        Source: {price.source}
                                      </Typography>
                                    </CardContent>
                                  </Card>
                                </Grid>
                              ))}
                          </Grid>
                          
                          {datePrices.length > 6 && (
                            <Box mt={2} textAlign="center">
                              <Typography variant="body2" color="text.secondary">
                                +{datePrices.length - 6} more prices for this date
                              </Typography>
                            </Box>
                          )}
                        </Paper>
                      );
                    });
                  })()}
                </Box>
              ) : (
                <Alert severity="info">
                  No prices have been scraped for this hotel yet. Use the form above to scrape current prices.
                </Alert>
              )}
            </TabPanel>
            
            <TabPanel value={tabValue} index={1}>
              <Typography variant="h6" gutterBottom>Price History by Room Type</Typography>
                {hotel.prices && hotel.prices.length > 0 ? (
                    <Box>
                        {/* Group prices by room type */}
                        {(() => {
                            const pricesByRoomType: { [key: string]: typeof hotel.prices } = {};
                            hotel.prices.forEach(price => {
                                const roomType = price.room_type || 'Unknown Room Type';
                                if (!pricesByRoomType[roomType]) {
                                    pricesByRoomType[roomType] = [];
                                }
                                pricesByRoomType[roomType].push(price);
                            });
                            
                            return Object.entries(pricesByRoomType).map(([roomType, prices]) => (
                                <Accordion key={roomType} defaultExpanded>
                                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                                        <Typography variant="subtitle1">{roomType}</Typography>
                                    </AccordionSummary>
                                    <AccordionDetails>
                                        <Grid container spacing={2}>
                                            {prices
                                                .sort((a, b) => new Date(b.scraped_at).getTime() - new Date(a.scraped_at).getTime())
                                                .map((price) => (
                                                    <Grid item xs={12} sm={6} md={4} key={price.id}>
                                                        <Card variant="outlined" sx={{ height: '100%' }}>
                                                            <CardContent sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                                                                <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
                                                                    <Typography variant="h6" color="primary">{formatPrice(price.price, price.currency)}</Typography>
                                                                    <Typography variant="caption" color="text.secondary">{formatDate(price.scraped_at)}</Typography>
                                                                </Box>
                                                                <Typography variant="body2" color="text.secondary" gutterBottom>
                                                                    For: {formatDate(price.check_in_date)} - {formatDate(price.check_out_date)}
                                                                </Typography>
                                                                {price.board_type && (
                                                                    <Typography variant="body2" color="text.secondary" gutterBottom>
                                                                        Board: {price.board_type}
                                                                    </Typography>
                                                                )}
                                                                <Box sx={{ flexGrow: 1 }} />
                                                                <Typography variant="caption" color="text.secondary">
                                                                    Source: {price.source}
                                                                </Typography>
                                                            </CardContent>
                                                        </Card>
                                                    </Grid>
                                                ))}
                                        </Grid>
                                    </AccordionDetails>
                                </Accordion>
                            ));
                        })()}
                    </Box>
                ) : (
                    <Alert severity="info">No prices have been scraped for this hotel yet.</Alert>
                )}
            </TabPanel>
            
            <TabPanel value={tabValue} index={2}>
              <Typography variant="h6" gutterBottom>
                Prices by Date
              </Typography>
              {hotel.prices && hotel.prices.length > 0 ? (
                <Box>
                  {/* Date range filter */}
                  <Paper sx={{ p: 2, mb: 3 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Filter by Date Range
                    </Typography>
                    <Grid container spacing={2} alignItems="center">
                      <Grid item xs={12} sm={4}>
                        <TextField
                          label="From Date"
                          type="date"
                          size="small"
                          InputLabelProps={{ shrink: true }}
                          fullWidth
                        />
                      </Grid>
                      <Grid item xs={12} sm={4}>
                        <TextField
                          label="To Date"
                          type="date"
                          size="small"
                          InputLabelProps={{ shrink: true }}
                          fullWidth
                        />
                      </Grid>
                      <Grid item xs={12} sm={4}>
                        <Button variant="outlined" size="small" fullWidth>
                          Apply Filter
                        </Button>
                      </Grid>
                    </Grid>
                  </Paper>

                  {/* Price Calendar View */}
                  <Paper sx={{ p: 2, mb: 3 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Price Calendar View
                    </Typography>
                    {(() => {
                      const pricesByDate: { [key: string]: typeof hotel.prices } = {};
                      
                      // Group prices by check-in date
                      hotel.prices.forEach(price => {
                        const checkInDate = price.check_in_date.split('T')[0];
                        if (!pricesByDate[checkInDate]) {
                          pricesByDate[checkInDate] = [];
                        }
                        pricesByDate[checkInDate].push(price);
                      });

                      // Get all dates and sort them
                      const allDates = Object.keys(pricesByDate).sort();
                      
                      if (allDates.length === 0) {
                        return <Typography variant="body2" color="text.secondary">No price data available</Typography>;
                      }

                      // Calculate price statistics for color coding
                      const allPrices = hotel.prices.map(p => p.price).filter(p => p !== null);
                      const minPrice = Math.min(...allPrices);
                      const maxPrice = Math.max(...allPrices);
                      const priceRange = maxPrice - minPrice;

                      return (
                        <Grid container spacing={1}>
                          {allDates.map((date) => {
                            const datePrices = pricesByDate[date];
                            const avgPrice = datePrices.reduce((sum, p) => sum + (p.price || 0), 0) / datePrices.length;
                            
                            // Calculate color intensity based on price (higher price = darker color)
                            const priceRatio = priceRange > 0 ? (avgPrice - minPrice) / priceRange : 0.5;
                            const colorIntensity = Math.max(0.1, Math.min(0.9, priceRatio));
                            
                            return (
                              <Grid item xs={6} sm={4} md={3} lg={2} key={date}>
                                <Card 
                                  variant="outlined" 
                                  sx={{ 
                                    p: 1, 
                                    textAlign: 'center',
                                    backgroundColor: `rgba(25, 118, 210, ${colorIntensity * 0.2})`,
                                    borderColor: `rgba(25, 118, 210, ${colorIntensity * 0.5})`
                                  }}
                                >
                                  <Typography variant="caption" color="text.secondary" display="block">
                                    {formatDate(date)}
                                  </Typography>
                                  <Typography variant="body2" fontWeight="bold" color="primary">
                                    {formatPrice(avgPrice, 'EUR')}
                                  </Typography>
                                  <Typography variant="caption" color="text.secondary">
                                    {datePrices.length} prices
                                  </Typography>
                                </Card>
                              </Grid>
                            );
                          })}
                        </Grid>
                      );
                    })()}
                  </Paper>

                  {/* Detailed Price Breakdown */}
                  <Paper sx={{ p: 2, mb: 3 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Detailed Price Breakdown by Date
                    </Typography>
                    {(() => {
                      const pricesByDate: { [key: string]: typeof hotel.prices } = {};
                      
                      // Group prices by check-in date
                      hotel.prices.forEach(price => {
                        const checkInDate = price.check_in_date.split('T')[0];
                        if (!pricesByDate[checkInDate]) {
                          pricesByDate[checkInDate] = [];
                        }
                        pricesByDate[checkInDate].push(price);
                      });

                      // Sort dates in ascending order
                      const sortedDates = Object.keys(pricesByDate).sort();
                      
                      return sortedDates.map((date) => {
                        const datePrices = pricesByDate[date];
                        const nextDay = new Date(date);
                        nextDay.setDate(nextDay.getDate() + 1);
                        const nextDayStr = nextDay.toISOString().split('T')[0];
                        
                        // Group by room type for this date
                        const pricesByRoomType: { [key: string]: typeof hotel.prices } = {};
                        datePrices.forEach(price => {
                          const roomType = price.room_type || 'Unknown Room Type';
                          if (!pricesByRoomType[roomType]) {
                            pricesByRoomType[roomType] = [];
                          }
                          pricesByRoomType[roomType].push(price);
                        });

                        return (
                          <Accordion key={date} defaultExpanded>
                            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                              <Box display="flex" justifyContent="space-between" alignItems="center" width="100%">
                                <Typography variant="subtitle1">
                                  {formatDate(date)} - {formatDate(nextDayStr)}
                                </Typography>
                                <Box display="flex" gap={1}>
                                  <Chip 
                                    label={`${datePrices.length} prices`} 
                                    size="small" 
                                    color="primary" 
                                    variant="outlined" 
                                  />
                                  <Chip 
                                    label={`${Object.keys(pricesByRoomType).length} room types`} 
                                    size="small" 
                                    color="secondary" 
                                    variant="outlined" 
                                  />
                                </Box>
                              </Box>
                            </AccordionSummary>
                            <AccordionDetails>
                              <Grid container spacing={2}>
                                {Object.entries(pricesByRoomType).map(([roomType, prices]) => {
                                  // Get the most recent price for this room type on this date
                                  const mostRecentPrice = prices.sort((a, b) => 
                                    new Date(b.scraped_at).getTime() - new Date(a.scraped_at).getTime()
                                  )[0];
                                  
                                  // Calculate price range for this room type
                                  const priceValues = prices.map(p => p.price).filter(p => p !== null);
                                  const minPrice = Math.min(...priceValues);
                                  const maxPrice = Math.max(...priceValues);
                                  const avgPrice = priceValues.reduce((sum, price) => sum + price, 0) / priceValues.length;
                                  
                                  return (
                                    <Grid item xs={12} sm={6} md={4} key={roomType}>
                                      <Card variant="outlined" sx={{ height: '100%' }}>
                                        <CardContent>
                                          <Typography variant="h6" color="primary" gutterBottom>
                                            {roomType}
                                          </Typography>
                                          
                                          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                                            <Typography variant="h5" color="primary" fontWeight="bold">
                                              {formatPrice(mostRecentPrice.price, mostRecentPrice.currency)}
                                            </Typography>
                                            <Typography variant="caption" color="text.secondary">
                                              Latest
                                            </Typography>
                                          </Box>
                                          
                                          {priceValues.length > 1 && (
                                            <Box mb={2}>
                                              <Typography variant="body2" color="text.secondary" gutterBottom>
                                                Price Range:
                                              </Typography>
                                              <Box display="flex" gap={1} flexWrap="wrap">
                                                <Chip 
                                                  label={`Min: ${formatPrice(minPrice, mostRecentPrice.currency)}`} 
                                                  size="small" 
                                                  color="success" 
                                                  variant="outlined" 
                                                />
                                                <Chip 
                                                  label={`Max: ${formatPrice(maxPrice, mostRecentPrice.currency)}`} 
                                                  size="small" 
                                                  color="error" 
                                                  variant="outlined" 
                                                />
                                                <Chip 
                                                  label={`Avg: ${formatPrice(avgPrice, mostRecentPrice.currency)}`} 
                                                  size="small" 
                                                  color="info" 
                                                  variant="outlined" 
                                                />
                                              </Box>
                                            </Box>
                                          )}
                                          
                                          <Typography variant="body2" color="text.secondary" gutterBottom>
                                            {mostRecentPrice.board_type && `Board: ${mostRecentPrice.board_type}`}
                                          </Typography>
                                          
                                          <Typography variant="caption" color="text.secondary">
                                            Last updated: {formatDate(mostRecentPrice.scraped_at)}
                                          </Typography>
                                          
                                          {prices.length > 1 && (
                                            <Box mt={1}>
                                              <Typography variant="caption" color="text.secondary">
                                                {prices.length} price records for this room type
                                              </Typography>
                                            </Box>
                                          )}
                                        </CardContent>
                                      </Card>
                                    </Grid>
                                  );
                                })}
                              </Grid>
                              
                              {/* Show all price history for this date */}
                              <Box mt={3}>
                                <Typography variant="subtitle2" gutterBottom>
                                  Price History for {formatDate(date)}
                                </Typography>
                                <Grid container spacing={1}>
                                  {datePrices
                                    .sort((a, b) => new Date(b.scraped_at).getTime() - new Date(a.scraped_at).getTime())
                                    .map((price) => (
                                      <Grid item xs={12} sm={6} md={4} key={price.id}>
                                        <Card variant="outlined" sx={{ p: 1 }}>
                                          <Box display="flex" justifyContent="space-between" alignItems="center">
                                            <Box>
                                              <Typography variant="body2" fontWeight="bold">
                                                {price.room_type}
                                              </Typography>
                                              <Typography variant="body2" color="primary">
                                                {formatPrice(price.price, price.currency)}
                                              </Typography>
                                            </Box>
                                            <Typography variant="caption" color="text.secondary">
                                              {formatDate(price.scraped_at)}
                                            </Typography>
                                          </Box>
                                        </Card>
                                      </Grid>
                                    ))}
                                </Grid>
                              </Box>
                            </AccordionDetails>
                          </Accordion>
                        );
                      });
                    })()}
                  </Paper>
                </Box>
              ) : (
                <Alert severity="info">
                  No prices have been scraped for this hotel yet. Use the scraping tools above to get price data.
                </Alert>
              )}
            </TabPanel>
            
            <TabPanel value={tabValue} index={3}>
              <Typography variant="h6" gutterBottom>
                Analytics
              </Typography>
              <Alert severity="info">
                Analytics features coming soon! This will include price trends, 
                booking patterns, and revenue optimization insights.
              </Alert>
            </TabPanel>
            
            <TabPanel value={tabValue} index={4}>
              <Typography variant="h6" gutterBottom>
                Competitor Analysis
              </Typography>
              <Alert severity="info">
                Competitor analysis features coming soon! This will include 
                competitor pricing, market positioning, and competitive advantages.
              </Alert>
            </TabPanel>
            
            <TabPanel value={tabValue} index={5}>
              <Typography variant="h6" gutterBottom>
                Hotel Settings
              </Typography>
              <Alert severity="info">
                Settings features coming soon! This will include monitoring 
                preferences, alert settings, and data management options.
              </Alert>
            </TabPanel>
          </Paper>
        </Grid>

        {/* Right Column - Quick Actions & Stats */}
        <Grid item xs={12} md={4}>
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              <Box display="flex" flexDirection="column" gap={2}>
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Update Prices for Date Range
                  </Typography>
                  {dateError && (
                    <Alert severity="error" sx={{ mb: 1 }}>
                      {dateError}
                    </Alert>
                  )}
                  <TextField
                    label="Check-in"
                    type="date"
                    value={checkInDate}
                    onChange={(e) => handleDateChange('checkIn', e.target.value)}
                    fullWidth
                    size="small"
                    InputLabelProps={{ shrink: true }}
                    sx={{ mb: 1 }}
                    error={!!dateError}
                  />
                  <TextField
                    label="Check-out"
                    type="date"
                    value={checkOutDate}
                    onChange={(e) => handleDateChange('checkOut', e.target.value)}
                    fullWidth
                    size="small"
                    InputLabelProps={{ shrink: true }}
                    sx={{ mb: 1 }}
                    error={!!dateError}
                  />
                  <Button
                    variant="contained"
                    startIcon={<RefreshIcon />}
                    onClick={handleScrapeDateRange}
                    disabled={scrapeRangeMutation.isPending}
                    fullWidth
                  >
                    {scrapeRangeMutation.isPending ? 'Updating...' : 'Update Prices'}
                  </Button>
                </Box>
                
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Update Daily Prices (Range)
                  </Typography>
                  {rangeDateError && (
                    <Alert severity="error" sx={{ mb: 1 }}>
                      {rangeDateError}
                    </Alert>
                  )}
                  <TextField
                    label="Start Date"
                    type="date"
                    value={rangeStartDate}
                    onChange={(e) => handleRangeDateChange('start', e.target.value)}
                    fullWidth
                    size="small"
                    InputLabelProps={{ shrink: true }}
                    sx={{ mb: 1 }}
                    error={!!rangeDateError}
                  />
                  <TextField
                    label="End Date"
                    type="date"
                    value={rangeEndDate}
                    onChange={(e) => handleRangeDateChange('end', e.target.value)}
                    fullWidth
                    size="small"
                    InputLabelProps={{ shrink: true }}
                    sx={{ mb: 1 }}
                    error={!!rangeDateError}
                  />
                  <Button
                    variant="contained"
                    color="secondary"
                    startIcon={<DateRangeIcon />}
                    onClick={handleScrapeDateRange}
                    disabled={scrapeRangeMutation.isPending}
                    fullWidth
                  >
                    {scrapeRangeMutation.isPending ? 'Updating...' : 'Update Prices'}
                  </Button>
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                    Max 30 days
                  </Typography>
                </Box>
                
                <Button
                  variant="outlined"
                  startIcon={<TrendingUpIcon />}
                  fullWidth
                >
                  View Analytics
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<CalendarIcon />}
                  fullWidth
                >
                  Set Alerts
                </Button>
              </Box>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Hotel Stats
              </Typography>
              <List dense>
                <ListItem><ListItemText primary="Added" secondary={'N/A'} /></ListItem>
                <ListItem><ListItemText primary="Last Updated" secondary={'N/A'} /></ListItem>
                <ListItem><ListItemText primary="Price Records" secondary={hotel.prices ? hotel.prices.length : 0} /></ListItem>
                <ListItem><ListItemText primary="Amenities" secondary={hotel.amenities ? hotel.amenities.length : 0} /></ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default HotelDetails; 