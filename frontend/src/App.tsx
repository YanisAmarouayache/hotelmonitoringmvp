import { Routes, Route } from 'react-router-dom'
import { Box, Container } from '@mui/material'
import Layout from './components/Layout'
import HotelList from './pages/HotelList'
import HotelDetails from './pages/HotelDetails'
import AddHotel from './pages/AddHotel'
import Analytics from './pages/Analytics'
import Settings from './pages/Settings'

function App() {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <Layout>
        <Container maxWidth="xl" sx={{ mt: 4, mb: 4, flex: 1 }}>
          <Routes>
            <Route path="/" element={<HotelList />} />
            <Route path="/hotels" element={<HotelList />} />
            <Route path="/hotels/:id" element={<HotelDetails />} />
            <Route path="/add-hotel" element={<AddHotel />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </Container>
      </Layout>
    </Box>
  )
}

export default App 