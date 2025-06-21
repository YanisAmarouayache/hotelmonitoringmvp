import React from 'react';
import { Box, Typography, Paper, Stack, Button } from '@mui/material';

const Settings: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" mb={2}>Settings</Typography>
      <Stack spacing={3}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6">Criteria Weighting</Typography>
          <Typography color="text.secondary">(Coming soon) Adjust the importance of hotel features per season.</Typography>
        </Paper>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6">Event Input</Typography>
          <Typography color="text.secondary">(Coming soon) Register notable events for a city/date.</Typography>
          <Button variant="outlined" sx={{ mt: 1 }}>Add Event</Button>
        </Paper>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6">Historical Data Upload</Typography>
          <Typography color="text.secondary">(Coming soon) Upload your hotel's historical data (CSV/JSON).</Typography>
          <Button variant="outlined" sx={{ mt: 1 }}>Upload Data</Button>
        </Paper>
      </Stack>
    </Box>
  );
};

export default Settings; 