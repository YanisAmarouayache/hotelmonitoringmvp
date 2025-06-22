import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Chip,
  Rating,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  CircularProgress,
  Tooltip,
  Grid,
  Card,
  CardContent,
  CardActions
} from '@mui/material';
import {
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  Visibility as ViewIcon,
  TrendingUp as TrendingUpIcon,
  LocationOn as LocationIcon,
  Star as StarIcon,
  DateRange as DateRangeIcon
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { getHotels, deleteHotel, scrapeDateRange, Hotel } from '../api/hotels';

const HotelList: React.FC = () => {
  const navigate = useNavigate();
  const [selectedHotel, setSelectedHotel] = useState<Hotel | null>(null);
  const [rangeDialogOpen, setRangeDialogOpen] = useState(false);
  const [rangeStartDate, setRangeStartDate] = useState('');
  const [rangeEndDate, setRangeEndDate] = useState('');
  const [rangeDateError, setRangeDateError] = useState('');
  const [viewMode, setViewMode] = useState<'table' | 'cards'>('cards');
  
  const queryClient = useQueryClient();

  const { data: hotels, isLoading, error } = useQuery({
    queryKey: ['hotels'],
    queryFn: getHotels
  });

  // Debug logging
  useEffect(() => {
    console.log('Hotels data updated:', hotels);
  }, [hotels]);

  useEffect(() => {
    if (error) {
      console.error('Hotels query error:', error);
    }
  }, [error]);

  const deleteMutation = useMutation({
    mutationFn: deleteHotel,
    onSuccess: () => {
      console.log('Hotel deleted successfully');
      queryClient.invalidateQueries({ queryKey: ['hotels'] });
    },
    onError: (error: any) => {
      console.error('Delete hotel error:', error);
      alert(`Failed to delete hotel: ${error.response?.data?.detail || error.message || 'Unknown error'}`);
    }
  });

  const scrapeRangeMutation = useMutation({
    mutationFn: ({ hotelId, startDate, endDate }: { hotelId: number; startDate: string; endDate: string }) =>
      scrapeDateRange(hotelId, startDate, endDate),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['hotels'] });
      setRangeDialogOpen(false);
      setSelectedHotel(null);
      setRangeDateError('');
      console.log('Date range scraping completed:', data);
    },
    onError: (error) => {
      console.error('Failed to scrape date range:', error);
    }
  });

  const handleDelete = (id: number) => {
    if (window.confirm('Are you sure you want to delete this hotel?')) {
      deleteMutation.mutate(id);
    }
  };

  const handleScrapeDateRange = (hotel: Hotel) => {
    setSelectedHotel(hotel);
    setRangeDialogOpen(true);
  };

  // Validate date range
  const validateDateRange = () => {
    if (!rangeStartDate || !rangeEndDate) {
      setRangeDateError('Please select both start and end dates');
      return false;
    }
    
    const startDate = new Date(rangeStartDate);
    const endDate = new Date(rangeEndDate);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    if (startDate < today) {
      setRangeDateError('Start date cannot be in the past');
      return false;
    }
    
    if (endDate <= startDate) {
      setRangeDateError('End date must be after start date');
      return false;
    }
    
    // Check if range is more than 30 days
    const daysDiff = (endDate.getTime() - startDate.getTime()) / (1000 * 3600 * 24);
    if (daysDiff > 30) {
      setRangeDateError('Date range cannot exceed 30 days');
      return false;
    }
    
    setRangeDateError('');
    return true;
  };

  const handleScrapeRangeSubmit = () => {
    if (!validateDateRange()) {
      return;
    }
    
    if (selectedHotel) {
      scrapeRangeMutation.mutate({
        hotelId: selectedHotel.id,
        startDate: rangeStartDate,
        endDate: rangeEndDate
      });
    }
  };

  // Set default dates
  React.useEffect(() => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const dayAfterTomorrow = new Date();
    dayAfterTomorrow.setDate(dayAfterTomorrow.getDate() + 2);
    
    setRangeStartDate(tomorrow.toISOString().split('T')[0]);
    setRangeEndDate(dayAfterTomorrow.toISOString().split('T')[0]);
  }, []);

  const formatPrice = (price: number | null, currency: string = 'EUR') => {
    if (price === null) return 'N/A';
    return `${price} ${currency}`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box p={3}>
        <Alert severity="error">
          Failed to load hotels: {error instanceof Error ? error.message : 'Unknown error'}
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">
          Hotels ({hotels?.length || 0})
        </Typography>
        
        <Box display="flex" gap={2}>
          <Button
            variant={viewMode === 'table' ? 'contained' : 'outlined'}
            onClick={() => setViewMode('table')}
            size="small"
          >
            Table View
          </Button>
          <Button
            variant={viewMode === 'cards' ? 'contained' : 'outlined'}
            onClick={() => setViewMode('cards')}
            size="small"
          >
            Card View
          </Button>
        </Box>
      </Box>

      {viewMode === 'table' ? (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Hotel Name</TableCell>
                <TableCell>Location</TableCell>
                <TableCell>Rating</TableCell>
                <TableCell>Star Rating</TableCell>
                <TableCell>Price</TableCell>
                <TableCell>Added</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {hotels?.map((hotel) => (
                <TableRow key={hotel.id}>
                  <TableCell>
                    <Typography variant="subtitle2" fontWeight="bold">
                      {hotel.name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {hotel.booking_url.slice(0, 50)}...
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Box display="flex" alignItems="center" gap={1}>
                      <LocationIcon fontSize="small" color="action" />
                      <Box>
                        <Typography variant="body2">{hotel.city}</Typography>
                        <Typography variant="caption" color="text.secondary">
                          {hotel.country}
                        </Typography>
                      </Box>
                    </Box>
                  </TableCell>
                  <TableCell>
                    {hotel.user_rating ? (
                      <Box display="flex" alignItems="center" gap={1}>
                        <Rating value={hotel.user_rating / 2} precision={0.1} size="small" readOnly />
                        <Typography variant="body2">
                          {hotel.user_rating.toFixed(1)}
                        </Typography>
                      </Box>
                    ) : (
                      'N/A'
                    )}
                  </TableCell>
                  <TableCell>
                    {hotel.star_rating ? (
                      <Box display="flex" alignItems="center" gap={1}>
                        <StarIcon fontSize="small" color="warning" />
                        <Typography variant="body2">{hotel.star_rating}</Typography>
                      </Box>
                    ) : (
                      'N/A'
                    )}
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {(() => {
                        // Show recent prices if available
                        if ((hotel as any).prices && (hotel as any).prices.length > 0) {
                          // Get the most recent price
                          const mostRecentPrice = (hotel as any).prices
                            .sort((a: any, b: any) => new Date(b.scraped_at).getTime() - new Date(a.scraped_at).getTime())[0];
                          
                          return (
                            <Box>
                              <Typography variant="body2" fontWeight="bold">
                                {formatPrice(mostRecentPrice.price, mostRecentPrice.currency)}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {formatDate(mostRecentPrice.check_in_date)}
                              </Typography>
                            </Box>
                          );
                        }
                        return formatPrice(null);
                      })()}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="caption">
                      {formatDate(hotel.created_at)}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Box display="flex" gap={1}>
                      <Tooltip title="Update Date Range">
                        <IconButton
                          size="small"
                          onClick={() => handleScrapeDateRange(hotel)}
                          disabled={scrapeRangeMutation.isPending}
                        >
                          <DateRangeIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="View Details">
                        <IconButton size="small" onClick={() => navigate(`/hotels/${hotel.id}`)}>
                          <ViewIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete Hotel">
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => handleDelete(hotel.id)}
                          disabled={deleteMutation.isPending}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      ) : (
        <Grid container spacing={3}>
          {hotels?.map((hotel) => (
            <Grid item xs={12} sm={6} md={4} key={hotel.id}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom noWrap>
                    {hotel.name}
                  </Typography>
                  
                  <Box display="flex" alignItems="center" gap={1} mb={1}>
                    <LocationIcon fontSize="small" color="action" />
                    <Typography variant="body2" color="text.secondary">
                      {hotel.city}, {hotel.country}
                    </Typography>
                  </Box>
                  
                  <Box display="flex" alignItems="center" gap={2} mb={2}>
                    {hotel.user_rating && (
                      <Box display="flex" alignItems="center" gap={0.5}>
                        <Rating value={hotel.user_rating / 2} precision={0.1} size="small" readOnly />
                        <Typography variant="caption">
                          {hotel.user_rating.toFixed(1)}
                        </Typography>
                      </Box>
                    )}
                    
                    {hotel.star_rating && (
                      <Box display="flex" alignItems="center" gap={0.5}>
                        <StarIcon fontSize="small" color="warning" />
                        <Typography variant="caption">
                          {hotel.star_rating}
                        </Typography>
                      </Box>
                    )}
                  </Box>
                  
                  {hotel.amenities && hotel.amenities.length > 0 && (
                    <Box mb={2}>
                      <Typography variant="caption" color="text.secondary" display="block" mb={1}>
                        Amenities:
                      </Typography>
                      <Box display="flex" flexWrap="wrap" gap={0.5}>
                        {hotel.amenities.slice(0, 3).map((amenity, index) => (
                          <Chip
                            key={index}
                            label={amenity}
                            size="small"
                            variant="outlined"
                          />
                        ))}
                        {hotel.amenities.length > 3 && (
                          <Chip
                            label={`+${hotel.amenities.length - 3} more`}
                            size="small"
                            variant="outlined"
                          />
                        )}
                      </Box>
                    </Box>
                  )}
                  
                  <Typography variant="caption" color="text.secondary">
                    Added: {formatDate(hotel.created_at)}
                  </Typography>
                  
                  {/* Price summary if available */}
                  {(hotel as any).prices && (hotel as any).prices.length > 0 && (
                    <Box mt={1}>
                      <Typography variant="caption" color="text.secondary" display="block" mb={0.5}>
                        Recent Prices:
                      </Typography>
                      <Box display="flex" flexWrap="wrap" gap={0.5}>
                        {(() => {
                          // Group by check-in date and get the most recent price for each date
                          const pricesByDate: { [key: string]: any } = {};
                          (hotel as any).prices.forEach((price: any) => {
                            const checkInDate = price.check_in_date.split('T')[0];
                            if (!pricesByDate[checkInDate] || 
                                new Date(price.scraped_at) > new Date(pricesByDate[checkInDate].scraped_at)) {
                              pricesByDate[checkInDate] = price;
                            }
                          });
                          
                          // Get the 3 most recent dates
                          const recentDates = Object.keys(pricesByDate)
                            .sort()
                            .reverse()
                            .slice(0, 3);
                          
                          return recentDates.map((date) => {
                            const price = pricesByDate[date];
                            return (
                              <Chip
                                key={date}
                                label={`${formatDate(date)}: ${formatPrice(price.price, price.currency)}`}
                                size="small"
                                variant="outlined"
                                color="primary"
                              />
                            );
                          });
                        })()}
                      </Box>
                    </Box>
                  )}
                </CardContent>
                
                <CardActions>
                  <Button
                    size="small"
                    startIcon={<DateRangeIcon />}
                    onClick={() => handleScrapeDateRange(hotel)}
                    disabled={scrapeRangeMutation.isPending}
                  >
                    {scrapeRangeMutation.isPending ? 'Updating...' : 'Update Date Range'}
                  </Button>
                  <Button
                    size="small"
                    startIcon={<ViewIcon />}
                    onClick={() => navigate(`/hotels/${hotel.id}`)}
                  >
                    View Details
                  </Button>
                  <Button
                    size="small"
                    color="error"
                    startIcon={<DeleteIcon />}
                    onClick={() => handleDelete(hotel.id)}
                    disabled={deleteMutation.isPending}
                  >
                    Delete
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Date Range Dialog */}
      <Dialog open={rangeDialogOpen} onClose={() => setRangeDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          Update Date Range for {selectedHotel?.name}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  type="date"
                  label="Start Date"
                  value={rangeStartDate}
                  onChange={(e) => setRangeStartDate(e.target.value)}
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  type="date"
                  label="End Date"
                  value={rangeEndDate}
                  onChange={(e) => setRangeEndDate(e.target.value)}
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
            </Grid>
            
            {rangeDateError && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {rangeDateError}
              </Alert>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRangeDialogOpen(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleScrapeRangeSubmit}
            variant="contained"
            disabled={scrapeRangeMutation.isPending}
            startIcon={scrapeRangeMutation.isPending ? <CircularProgress size={16} /> : <DateRangeIcon />}
          >
            {scrapeRangeMutation.isPending ? 'Updating...' : 'Update Date Range'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default HotelList; 