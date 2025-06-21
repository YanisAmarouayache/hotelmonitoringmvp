import React, { useState } from 'react';
import { Box, Typography, Tabs, Tab } from '@mui/material';

const Analytics: React.FC = () => {
  const [tab, setTab] = useState(0);

  return (
    <Box>
      <Typography variant="h4" mb={2}>Analytics</Typography>
      <Tabs value={tab} onChange={(_, v) => setTab(v)}>
        <Tab label="Price Evolution" />
        <Tab label="Market Comparison" />
        <Tab label="Booking Pace" />
      </Tabs>
      <Box mt={3}>
        {tab === 0 && <Typography>Price Evolution Chart (Coming soon)</Typography>}
        {tab === 1 && <Typography>Market Comparison Table (Coming soon)</Typography>}
        {tab === 2 && <Typography>Booking Pace Visualization (Coming soon)</Typography>}
      </Box>
    </Box>
  );
};

export default Analytics; 