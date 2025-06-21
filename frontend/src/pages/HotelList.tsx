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
  Star as StarIcon
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { getHotels, deleteHotel, updateHotelPrices, Hotel } from '../api/hotels';

const HotelList: React.FC = () => {
  const navigate = useNavigate();
  const [selectedHotel, setSelectedHotel] = useState<Hotel | null>(null);
  const [updateDialogOpen, setUpdateDialogOpen] = useState(false);
  const [checkInDate, setCheckInDate] = useState('');
  const [checkOutDate, setCheckOutDate] = useState('');
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

  const updatePricesMutation = useMutation({
    mutationFn: ({ hotelId, checkIn, checkOut }: { hotelId: number; checkIn?: string; checkOut?: string }) =>
      updateHotelPrices(hotelId, checkIn, checkOut),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hotels'] });
      setUpdateDialogOpen(false);
      setSelectedHotel(null);
    }
  });

  const handleDelete = (id: number) => {
    if (window.confirm('Are you sure you want to delete this hotel?')) {
      deleteMutation.mutate(id);
    }
  };

  const handleUpdatePrices = (hotel: Hotel) => {
    setSelectedHotel(hotel);
    setUpdateDialogOpen(true);
  };

  const handleUpdatePricesSubmit = () => {
    if (selectedHotel) {
      updatePricesMutation.mutate({
        hotelId: selectedHotel.id,
        checkIn: checkInDate || undefined,
        checkOut: checkOutDate || undefined
      });
    }
  };

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
                      {formatPrice(null)} {/* TODO: Get current price */}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="caption">
                      {formatDate(hotel.created_at)}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Box display="flex" gap={1}>
                      <Tooltip title="Update Prices">
                        <IconButton
                          size="small"
                          onClick={() => handleUpdatePrices(hotel)}
                          disabled={updatePricesMutation.isPending}
                        >
                          <RefreshIcon />
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
                </CardContent>
                
                <CardActions>
                  <Button
                    size="small"
                    startIcon={<RefreshIcon />}
                    onClick={() => handleUpdatePrices(hotel)}
                    disabled={updatePricesMutation.isPending}
                  >
                    Update Prices
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

      {/* Update Prices Dialog */}
      <Dialog open={updateDialogOpen} onClose={() => setUpdateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          Update Prices for {selectedHotel?.name}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  type="date"
                  label="Check-in Date"
                  value={checkInDate}
                  onChange={(e) => setCheckInDate(e.target.value)}
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  type="date"
                  label="Check-out Date"
                  value={checkOutDate}
                  onChange={(e) => setCheckOutDate(e.target.value)}
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
            </Grid>
            
            {updatePricesMutation.isError && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {updatePricesMutation.error instanceof Error 
                  ? updatePricesMutation.error.message 
                  : 'Failed to update prices'
                }
              </Alert>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUpdateDialogOpen(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleUpdatePricesSubmit}
            variant="contained"
            disabled={updatePricesMutation.isPending}
            startIcon={updatePricesMutation.isPending ? <CircularProgress size={16} /> : <TrendingUpIcon />}
          >
            {updatePricesMutation.isPending ? 'Updating...' : 'Update Prices'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default HotelList; 