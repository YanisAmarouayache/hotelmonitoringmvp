import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Typography,
  Paper,
  Alert,
  CircularProgress,
  Grid
} from '@mui/material';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { addHotel, ScrapingResponse } from '../api/hotels';

const AddHotel: React.FC = () => {
  const [formData, setFormData] = useState({
    booking_url: '',
    check_in_date: '',
    check_out_date: ''
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const mutation = useMutation({
    mutationFn: addHotel,
    onSuccess: (data: ScrapingResponse) => {
      console.log('Add hotel success:', data);
      let successMessage = `Hotel "${data.hotel_data?.name}" added successfully!`;
      
      // Add guest information if available
      if (data.guest_info) {
        const guests = [];
        if (data.guest_info.adults) {
          guests.push(`${data.guest_info.adults} adult${data.guest_info.adults > 1 ? 's' : ''}`);
        }
        if (data.guest_info.children) {
          guests.push(`${data.guest_info.children} child${data.guest_info.children > 1 ? 'ren' : ''}`);
        }
        if (guests.length > 0) {
          successMessage += ` (${guests.join(', ')})`;
        }
      }
      
      successMessage += ' Range updating has been initiated for the specified dates.';
      
      setSuccess(successMessage);
      setFormData({
        booking_url: '',
        check_in_date: '',
        check_out_date: '',
      });
      queryClient.invalidateQueries({ queryKey: ['hotels'] });
    },
    onError: (error: any) => {
      console.error('Add hotel error:', error);
      setError(error.response?.data?.error || 'Failed to add hotel');
    }
  });

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    setError('');
    setSuccess('');
  };

  const isUrlValid = (url: string): boolean => {
    return url.includes('booking.com') && url.includes('hotel');
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!formData.booking_url.trim()) {
      setError('Booking URL is required');
      return;
    }

    if (!isUrlValid(formData.booking_url)) {
      setError('Please enter a valid Booking.com hotel URL');
      return;
    }

    if (!formData.check_in_date || !formData.check_out_date) {
      setError('Check-in and check-out dates are required');
      return;
    }

    mutation.mutate({
      booking_url: formData.booking_url.trim(),
      check_in_date: formData.check_in_date,
      check_out_date: formData.check_out_date,
    });
  };

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto', p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Add Hotel
      </Typography>
      
      <Paper sx={{ mt: 3, p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Add New Hotel
        </Typography>
        
        <Alert severity="info" sx={{ mb: 3 }}>
          <Typography variant="body2">
            <strong>Note:</strong> When you add a hotel, the system will automatically update prices for each day in the date range you specify below. 
            This may take a few moments depending on the number of days.
          </Typography>
        </Alert>
        
        <Box component="form" onSubmit={handleSubmit} sx={{ mt: 2 }}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Booking.com Hotel URL"
                value={formData.booking_url}
                onChange={(e) => handleInputChange('booking_url', e.target.value)}
                placeholder="https://www.booking.com/hotel/..."
                error={Boolean(formData.booking_url && !isUrlValid(formData.booking_url))}
                helperText={
                  formData.booking_url && !isUrlValid(formData.booking_url)
                    ? 'Please enter a valid Booking.com hotel URL'
                    : 'Enter a Booking.com hotel URL to scrape and add hotel data'
                }
                required
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Range Start Date"
                type="date"
                value={formData.check_in_date}
                onChange={(e) => handleInputChange('check_in_date', e.target.value)}
                InputLabelProps={{
                  shrink: true,
                }}
                helperText="Start date for price updating"
                required
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Range End Date"
                type="date"
                value={formData.check_out_date}
                onChange={(e) => handleInputChange('check_out_date', e.target.value)}
                InputLabelProps={{
                  shrink: true,
                }}
                helperText="End date for price updating"
                required
              />
            </Grid>
            
            <Grid item xs={12}>
              <Button
                type="submit"
                variant="contained"
                size="large"
                fullWidth
                disabled={mutation.isPending}
                startIcon={mutation.isPending ? <CircularProgress size={20} /> : null}
              >
                {mutation.isPending ? 'Adding Hotel & Updating Prices...' : 'Add Hotel & Update Date Range'}
              </Button>
            </Grid>
          </Grid>
        </Box>
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mt: 2 }}>
          {success}
        </Alert>
      )}

      <Paper sx={{ mt: 3, p: 3 }}>
        <Typography variant="h6" gutterBottom>
          How to Add a Hotel
        </Typography>
        <Typography variant="body2" color="text.secondary">
          1. Go to Booking.com and find the hotel you want to monitor<br/>
          2. Copy the hotel's URL from your browser<br/>
          3. Paste it in the "Booking.com Hotel URL" field above<br/>
          4. Set check-in and check-out dates (required)<br/>
          5. Click "Add Hotel" to update and store the hotel data
        </Typography>
      </Paper>
    </Box>
  );
};

export default AddHotel; 