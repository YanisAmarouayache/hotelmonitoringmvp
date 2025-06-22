import React, { useState, useMemo, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Alert,
  CircularProgress,
  Button,
  TextField,
  Divider,
  Avatar,
  IconButton,
  Tooltip,
  Badge,
  Stack
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  TrendingFlat,
  CompareArrows,
  DateRange,
  Euro,
  Star,
  LocationOn,
  Hotel as HotelIcon,
  Add as AddIcon,
  Remove as RemoveIcon,
  Analytics as AnalyticsIcon,
  Timeline as TimelineIcon,
  TableChart as TableChartIcon
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { getHotels, getHotelPrices } from '../api/hotels';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';

const HotelComparison: React.FC = () => {
  const [selectedPrimaryHotel, setSelectedPrimaryHotel] = useState<number | ''>('');
  const [selectedComparisonHotels, setSelectedComparisonHotels] = useState<number[]>([]);
  const [dateRange, setDateRange] = useState({
    start: '',
    end: ''
  });
  const [viewMode, setViewMode] = useState<'overview' | 'charts' | 'detailed'>('overview');
  const [searchParams] = useSearchParams();

  // Handle URL parameters and set defaults
  useEffect(() => {
    const primaryParam = searchParams.get('primary');
    if (primaryParam) {
      const primaryId = parseInt(primaryParam);
      if (!isNaN(primaryId)) {
        setSelectedPrimaryHotel(primaryId);
      }
    }

    // Set default date range to next week
    if (!dateRange.start && !dateRange.end) {
      const tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);
      
      const nextWeek = new Date();
      nextWeek.setDate(nextWeek.getDate() + 7);
      
      setDateRange({
        start: tomorrow.toISOString().split('T')[0],
        end: nextWeek.toISOString().split('T')[0]
      });
    }
  }, [searchParams, dateRange.start, dateRange.end]);

  // Fetch hotels
  const { data: hotels, isLoading: hotelsLoading } = useQuery({
    queryKey: ['hotels'],
    queryFn: getHotels
  });

  // Fetch prices for all selected hotels
  const allHotelIds = useMemo(() => {
    const ids = [];
    if (selectedPrimaryHotel) ids.push(selectedPrimaryHotel);
    ids.push(...selectedComparisonHotels);
    return ids;
  }, [selectedPrimaryHotel, selectedComparisonHotels]);

  const { data: allPrices, isLoading: pricesLoading } = useQuery({
    queryKey: ['hotel-prices-multiple', allHotelIds],
    queryFn: async () => {
      const results = await Promise.all(
        allHotelIds.map(id => getHotelPrices(id))
      );
      return allHotelIds.map((id, index) => ({
        hotelId: id,
        prices: results[index] || []
      }));
    },
    enabled: allHotelIds.length > 0
  });

  const isLoading = hotelsLoading || pricesLoading;

  // Extract and filter prices
  const primaryPrices = useMemo(() => {
    if (!allPrices || !selectedPrimaryHotel) return [];
    const hotelData = allPrices.find(data => data.hotelId === selectedPrimaryHotel);
    return hotelData?.prices || [];
  }, [allPrices, selectedPrimaryHotel]);

  const comparisonPrices = useMemo(() => {
    if (!allPrices) return [];
    return selectedComparisonHotels.map(hotelId => {
      const hotelData = allPrices.find(data => data.hotelId === hotelId);
      return hotelData?.prices || [];
    });
  }, [allPrices, selectedComparisonHotels]);

  const filteredPrimaryPrices = useMemo(() => {
    if (!primaryPrices || !dateRange.start || !dateRange.end) return [];
    const startDate = new Date(dateRange.start);
    const endDate = new Date(dateRange.end);
    return primaryPrices.filter((price: any) => {
      const checkInDate = new Date(price.check_in_date);
      return checkInDate >= startDate && checkInDate <= endDate;
    });
  }, [primaryPrices, dateRange]);

  const filteredComparisonPrices = useMemo(() => {
    if (!dateRange.start || !dateRange.end) return [];
    const startDate = new Date(dateRange.start);
    const endDate = new Date(dateRange.end);
    return comparisonPrices.map(prices => 
      prices.filter((price: any) => {
        const checkInDate = new Date(price.check_in_date);
        return checkInDate >= startDate && checkInDate <= endDate;
      })
    );
  }, [comparisonPrices, dateRange]);

  // Calculate analytics
  const analytics = useMemo(() => {
    if (!filteredPrimaryPrices.length || !hotels) return null;

    const primaryHotel = hotels.find(h => h.id === selectedPrimaryHotel);
    if (!primaryHotel) return null;

    const comparisonData = selectedComparisonHotels.map((hotelId, index) => {
      const hotel = hotels.find(h => h.id === hotelId);
      const prices = filteredComparisonPrices[index] || [];
      
      if (!hotel || !prices.length) return null;

      const primaryAvg = filteredPrimaryPrices.reduce((sum, p) => sum + p.price, 0) / filteredPrimaryPrices.length;
      const comparisonAvg = prices.reduce((sum, p) => sum + p.price, 0) / prices.length;
      const difference = comparisonAvg - primaryAvg;
      const percentageDiff = primaryAvg > 0 ? (difference / primaryAvg) * 100 : 0;

      return {
        hotel,
        avgPrice: Math.round(comparisonAvg * 100) / 100,
        difference: Math.round(difference * 100) / 100,
        percentageDiff: Math.round(percentageDiff * 100) / 100,
        trend: difference > 0 ? 'higher' : difference < 0 ? 'lower' : 'same',
        priceCount: prices.length
      };
    }).filter(Boolean);

    return {
      primaryHotel,
      primaryAvg: filteredPrimaryPrices.reduce((sum, p) => sum + p.price, 0) / filteredPrimaryPrices.length,
      comparisonData,
      totalDays: filteredPrimaryPrices.length
    };
  }, [filteredPrimaryPrices, filteredComparisonPrices, selectedPrimaryHotel, hotels]);

  // Chart data
  const chartData = useMemo(() => {
    if (!analytics) return [];

    const dateMap = new Map();
    
    filteredPrimaryPrices.forEach((price: any) => {
      const date = new Date(price.check_in_date).toLocaleDateString();
      if (!dateMap.has(date)) {
        dateMap.set(date, { date, [analytics.primaryHotel.name]: price.price });
      } else {
        dateMap.get(date)[analytics.primaryHotel.name] = price.price;
      }
    });

    analytics.comparisonData.forEach(({ hotel }: any) => {
      const hotelPrices = filteredComparisonPrices.find((prices: any[], index: number) => 
        selectedComparisonHotels[index] === hotel.id
      ) || [];
      
      hotelPrices.forEach((price: any) => {
        const date = new Date(price.check_in_date).toLocaleDateString();
        if (!dateMap.has(date)) {
          dateMap.set(date, { date });
        }
        dateMap.get(date)[hotel.name] = price.price;
      });
    });

    return Array.from(dateMap.values()).sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  }, [analytics, filteredPrimaryPrices, filteredComparisonPrices, selectedComparisonHotels]);

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'higher': return <TrendingUp color="error" />;
      case 'lower': return <TrendingDown color="success" />;
      default: return <TrendingFlat color="action" />;
    }
  };

  const getTrendColor = (trend: string) => {
    switch (trend) {
      case 'higher': return 'error';
      case 'lower': return 'success';
      default: return 'default';
    }
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress size={60} />
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 1400, mx: 'auto', p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h3" gutterBottom sx={{ fontWeight: 'bold', color: 'primary.main' }}>
          <CompareArrows sx={{ mr: 2, verticalAlign: 'middle' }} />
          Hotel Price Comparison
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Compare hotel prices and analyze pricing strategies across different properties
        </Typography>
      </Box>

      {/* Selection Panel */}
      <Paper sx={{ p: 3, mb: 4, borderRadius: 2 }}>
        <Typography variant="h6" gutterBottom sx={{ mb: 3 }}>
          Select Hotels to Compare
        </Typography>
        
        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <FormControl fullWidth>
              <InputLabel>Primary Hotel</InputLabel>
              <Select
                value={selectedPrimaryHotel}
                label="Primary Hotel"
                onChange={(e) => setSelectedPrimaryHotel(e.target.value as number | '')}
              >
                <MenuItem value="">
                  <em>Choose your reference hotel</em>
                </MenuItem>
                {hotels?.map((hotel) => (
                  <MenuItem key={hotel.id} value={hotel.id}>
                    <Box display="flex" alignItems="center" gap={1}>
                      <HotelIcon color="primary" />
                      {hotel.name}
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} md={4}>
            <FormControl fullWidth>
              <InputLabel>Comparison Hotels</InputLabel>
              <Select
                multiple
                value={selectedComparisonHotels}
                label="Comparison Hotels"
                onChange={(e) => setSelectedComparisonHotels(e.target.value as number[])}
                renderValue={(selected) => (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {selected.map((hotelId) => {
                      const hotel = hotels?.find(h => h.id === hotelId);
                      return <Chip key={hotelId} label={hotel?.name || hotelId} size="small" />;
                    })}
                  </Box>
                )}
              >
                {hotels?.filter(hotel => hotel.id !== selectedPrimaryHotel).map((hotel) => (
                  <MenuItem key={hotel.id} value={hotel.id}>
                    <Box display="flex" alignItems="center" gap={1}>
                      <HotelIcon color="secondary" />
                      {hotel.name}
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} md={4}>
            <Box display="flex" gap={1}>
              <TextField
                label="Start Date"
                type="date"
                value={dateRange.start}
                onChange={(e) => setDateRange(prev => ({ ...prev, start: e.target.value }))}
                InputLabelProps={{ shrink: true }}
                size="small"
                fullWidth
              />
              <TextField
                label="End Date"
                type="date"
                value={dateRange.end}
                onChange={(e) => setDateRange(prev => ({ ...prev, end: e.target.value }))}
                InputLabelProps={{ shrink: true }}
                size="small"
                fullWidth
              />
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {!selectedPrimaryHotel && (
        <Alert severity="info" sx={{ mb: 4 }}>
          <Typography variant="body1">
            Please select a primary hotel to start the comparison analysis.
          </Typography>
        </Alert>
      )}

      {selectedPrimaryHotel && analytics && (
        <>
          {/* View Mode Toggle */}
          <Box sx={{ mb: 3 }}>
            <Stack direction="row" spacing={1}>
              <Button
                variant={viewMode === 'overview' ? 'contained' : 'outlined'}
                startIcon={<AnalyticsIcon />}
                onClick={() => setViewMode('overview')}
              >
                Overview
              </Button>
              <Button
                variant={viewMode === 'charts' ? 'contained' : 'outlined'}
                startIcon={<TimelineIcon />}
                onClick={() => setViewMode('charts')}
              >
                Charts
              </Button>
              <Button
                variant={viewMode === 'detailed' ? 'contained' : 'outlined'}
                startIcon={<TableChartIcon />}
                onClick={() => setViewMode('detailed')}
              >
                Detailed
              </Button>
            </Stack>
          </Box>

          {/* Overview Mode */}
          {viewMode === 'overview' && (
            <Grid container spacing={3}>
              {/* Primary Hotel Card */}
              <Grid item xs={12} md={4}>
                <Card sx={{ height: '100%', border: '2px solid', borderColor: 'primary.main' }}>
                  <CardContent>
                    <Box display="flex" alignItems="center" gap={2} sx={{ mb: 2 }}>
                      <Avatar sx={{ bgcolor: 'primary.main' }}>
                        <HotelIcon />
                      </Avatar>
                      <Box>
                        <Typography variant="h6" fontWeight="bold">
                          {analytics.primaryHotel.name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Primary Reference
                        </Typography>
                      </Box>
                    </Box>
                    
                    <Divider sx={{ my: 2 }} />
                    
                    <Box textAlign="center">
                      <Typography variant="h3" color="primary.main" fontWeight="bold">
                        €{Math.round(analytics.primaryAvg * 100) / 100}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Average Price ({analytics.totalDays} days)
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              {/* Comparison Hotels */}
              {analytics.comparisonData.map(({ hotel, avgPrice, difference, percentageDiff, trend, priceCount }: any) => (
                <Grid item xs={12} md={4} key={hotel.id}>
                  <Card sx={{ height: '100%', border: '1px solid', borderColor: 'divider' }}>
                    <CardContent>
                      <Box display="flex" alignItems="center" gap={2} sx={{ mb: 2 }}>
                        <Avatar sx={{ bgcolor: 'secondary.main' }}>
                          <HotelIcon />
                        </Avatar>
                        <Box flex={1}>
                          <Typography variant="h6" fontWeight="bold">
                            {hotel.name}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Comparison Hotel
                          </Typography>
                        </Box>
                        <Chip 
                          icon={getTrendIcon(trend)}
                          label={`${percentageDiff > 0 ? '+' : ''}${percentageDiff}%`}
                          color={getTrendColor(trend) as any}
                          size="small"
                        />
                      </Box>
                      
                      <Divider sx={{ my: 2 }} />
                      
                      <Box textAlign="center">
                        <Typography variant="h4" color="text.primary" fontWeight="bold">
                          €{avgPrice}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                          Average Price ({priceCount} days)
                        </Typography>
                        <Typography 
                          variant="body1" 
                          color={trend === 'higher' ? 'error.main' : trend === 'lower' ? 'success.main' : 'text.secondary'}
                          fontWeight="bold"
                        >
                          {difference > 0 ? '+' : ''}€{difference} vs Primary
                        </Typography>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          )}

          {/* Charts Mode */}
          {viewMode === 'charts' && (
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Paper sx={{ p: 3, borderRadius: 2 }}>
                  <Typography variant="h6" gutterBottom>
                    Price Trends Over Time
                  </Typography>
                  <ResponsiveContainer width="100%" height={400}>
                    <LineChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <RechartsTooltip />
                      <Legend />
                      <Line 
                        type="monotone" 
                        dataKey={analytics.primaryHotel.name} 
                        stroke="#1976d2" 
                        strokeWidth={3}
                        dot={{ fill: '#1976d2', strokeWidth: 2, r: 4 }}
                      />
                      {analytics.comparisonData.map(({ hotel }: any, index: number) => (
                        <Line 
                          key={hotel.id}
                          type="monotone" 
                          dataKey={hotel.name} 
                          stroke={COLORS[index % COLORS.length]}
                          strokeWidth={2}
                          dot={{ fill: COLORS[index % COLORS.length], strokeWidth: 2, r: 3 }}
                        />
                      ))}
                    </LineChart>
                  </ResponsiveContainer>
                </Paper>
              </Grid>

              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 3, borderRadius: 2 }}>
                  <Typography variant="h6" gutterBottom>
                    Average Price Comparison
                  </Typography>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={[
                      { name: analytics.primaryHotel.name, price: Math.round(analytics.primaryAvg * 100) / 100 },
                      ...analytics.comparisonData.map(({ hotel, avgPrice }: any) => ({
                        name: hotel.name,
                        price: avgPrice
                      }))
                    ]}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <RechartsTooltip />
                      <Bar dataKey="price" fill="#1976d2" />
                    </BarChart>
                  </ResponsiveContainer>
                </Paper>
              </Grid>

              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 3, borderRadius: 2 }}>
                  <Typography variant="h6" gutterBottom>
                    Price Difference Distribution
                  </Typography>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={analytics.comparisonData.map(({ hotel, percentageDiff }: any) => ({
                          name: hotel.name,
                          value: Math.abs(percentageDiff)
                        }))}
                        cx="50%"
                        cy="50%"
                        outerRadius={80}
                        dataKey="value"
                        label={({ name, value }) => `${name}: ${value.toFixed(1)}%`}
                      >
                        {analytics.comparisonData.map((entry: any, index: number) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <RechartsTooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </Paper>
              </Grid>
            </Grid>
          )}

          {/* Detailed Mode */}
          {viewMode === 'detailed' && (
            <Paper sx={{ borderRadius: 2 }}>
              <Box sx={{ p: 3, borderBottom: 1, borderColor: 'divider' }}>
                <Typography variant="h6">
                  Detailed Price Analysis
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Comprehensive breakdown of price differences and trends
                </Typography>
              </Box>
              
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow sx={{ backgroundColor: 'grey.50' }}>
                      <TableCell><strong>Hotel</strong></TableCell>
                      <TableCell><strong>Average Price</strong></TableCell>
                      <TableCell><strong>vs Primary</strong></TableCell>
                      <TableCell><strong>Percentage</strong></TableCell>
                      <TableCell><strong>Trend</strong></TableCell>
                      <TableCell><strong>Data Points</strong></TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    <TableRow sx={{ backgroundColor: 'primary.50' }}>
                      <TableCell>
                        <Box display="flex" alignItems="center" gap={1}>
                          <HotelIcon color="primary" />
                          <strong>{analytics.primaryHotel.name}</strong>
                          <Chip label="Primary" size="small" color="primary" />
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Typography variant="h6" color="primary.main">
                          €{Math.round(analytics.primaryAvg * 100) / 100}
                        </Typography>
                      </TableCell>
                      <TableCell>-</TableCell>
                      <TableCell>-</TableCell>
                      <TableCell>-</TableCell>
                      <TableCell>{analytics.totalDays}</TableCell>
                    </TableRow>
                    
                    {analytics.comparisonData.map(({ hotel, avgPrice, difference, percentageDiff, trend, priceCount }: any) => (
                      <TableRow key={hotel.id}>
                        <TableCell>
                          <Box display="flex" alignItems="center" gap={1}>
                            <HotelIcon color="secondary" />
                            {hotel.name}
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Typography variant="h6">
                            €{avgPrice}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Box display="flex" alignItems="center" gap={1}>
                            <Typography 
                              variant="body1" 
                              color={trend === 'higher' ? 'error.main' : trend === 'lower' ? 'success.main' : 'text.secondary'}
                              fontWeight="bold"
                            >
                              {difference > 0 ? '+' : ''}€{difference}
                            </Typography>
                            {getTrendIcon(trend)}
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Chip 
                            label={`${percentageDiff > 0 ? '+' : ''}${percentageDiff}%`}
                            color={getTrendColor(trend) as any}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          {getTrendIcon(trend)}
                        </TableCell>
                        <TableCell>{priceCount}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          )}
        </>
      )}
    </Box>
  );
};

export default HotelComparison; 