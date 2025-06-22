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
  ExpandMore as ExpandMoreIcon
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams, useNavigate } from 'react-router-dom';
import { getHotel, getHotelPrices, updateHotelPrices } from '../api/hotels';

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
  
  const queryClient = useQueryClient();

  const { data: hotel, isLoading: hotelLoading, error: hotelError } = useQuery({
    queryKey: ['hotel', id],
    queryFn: () => getHotel(Number(id)),
    enabled: !!id
  });

  const updatePricesMutation = useMutation({
    mutationFn: ({ hotelId, checkIn, checkOut }: { hotelId: number; checkIn?: string; checkOut?: string }) =>
      updateHotelPrices(hotelId, checkIn, checkOut),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hotel', id] });
      setDateError(''); // Clear any date errors on success
    },
    onError: (error) => {
      console.error('Failed to update prices:', error);
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

  const handleUpdatePrices = () => {
    if (!validateDates()) {
      return;
    }
    
    if (hotel) {
      updatePricesMutation.mutate({
        hotelId: hotel.id,
        checkIn: checkInDate || undefined,
        checkOut: checkOutDate || undefined
      });
    }
  };

  // Set default dates (tomorrow and day after tomorrow)
  React.useEffect(() => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const dayAfterTomorrow = new Date();
    dayAfterTomorrow.setDate(dayAfterTomorrow.getDate() + 2);
    
    setCheckInDate(tomorrow.toISOString().split('T')[0]);
    setCheckOutDate(dayAfterTomorrow.toISOString().split('T')[0]);
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
    return `${price} ${currency}`;
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
              <Tab label="Analytics" />
              <Tab label="Competitors" />
              <Tab label="Settings" />
            </Tabs>
            
            <TabPanel value={tabValue} index={0}>
              <Typography variant="h6" gutterBottom>Current Rooms & Prices</Typography>
              
              {/* Scraping Section */}
              <Paper sx={{ p: 3, mb: 3 }}>
                <Typography variant="subtitle1" gutterBottom>Scrape New Prices</Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Enter dates to scrape current prices for this hotel
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
                      onClick={handleUpdatePrices}
                      disabled={updatePricesMutation.isPending || !checkInDate || !checkOutDate}
                      fullWidth
                    >
                      {updatePricesMutation.isPending ? 'Scraping...' : 'Scrape Prices'}
                    </Button>
                  </Grid>
                </Grid>
                
                {dateError && (
                  <Alert severity="error" sx={{ mt: 2 }}>
                    {dateError}
                  </Alert>
                )}
                
                {updatePricesMutation.isSuccess && (
                  <Alert severity="success" sx={{ mt: 2 }}>
                    Successfully scraped {updatePricesMutation.data?.prices_added || 0} new price records!
                  </Alert>
                )}
              </Paper>

              {/* Current Prices Display */}
              <Typography variant="subtitle1" gutterBottom>Recent Prices</Typography>
              {hotel.prices && hotel.prices.length > 0 ? (
                <Grid container spacing={2}>
                  {hotel.prices
                    .sort((a, b) => new Date(b.scraped_at).getTime() - new Date(a.scraped_at).getTime())
                    .slice(0, 6) // Show only the 6 most recent prices
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
                            <Typography variant="body2" color="text.secondary" gutterBottom>
                              For: {formatDate(price.check_in_date)} - {formatDate(price.check_out_date)}
                            </Typography>
                            {price.board_type && (
                              <Typography variant="body2" color="text.secondary">
                                {price.board_type}
                              </Typography>
                            )}
                          </CardContent>
                        </Card>
                      </Grid>
                    ))}
                </Grid>
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
                Analytics
              </Typography>
              <Alert severity="info">
                Analytics features coming soon! This will include price trends, 
                booking patterns, and revenue optimization insights.
              </Alert>
            </TabPanel>
            
            <TabPanel value={tabValue} index={3}>
              <Typography variant="h6" gutterBottom>
                Competitor Analysis
              </Typography>
              <Alert severity="info">
                Competitor analysis features coming soon! This will include 
                competitor pricing, market positioning, and competitive advantages.
              </Alert>
            </TabPanel>
            
            <TabPanel value={tabValue} index={4}>
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
                    Update Prices for Specific Dates
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
                    onClick={handleUpdatePrices}
                    disabled={updatePricesMutation.isPending}
                    fullWidth
                  >
                    {updatePricesMutation.isPending ? 'Updating...' : 'Update Prices'}
                  </Button>
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