import { Routes, Route, Navigate } from 'react-router-dom'
import LandingPage from './pages/LandingPage.jsx'
import LoginPage from './pages/LoginPage.jsx'
import RegisterPage from './pages/RegisterPage.jsx'
import ForgotPasswordPage from './pages/ForgotPasswordPage.jsx'
import ResetPasswordPage from './pages/ResetPasswordPage.jsx'
import VerifyEmailPage from './pages/VerifyEmailPage.jsx'
import DashboardPage from './pages/DashboardPage.jsx'
import SearchPage from './pages/SearchPage.jsx'
import HotelsPage from './pages/HotelsPage.jsx'
import HotelDetailsPage from './pages/HotelDetailsPage.jsx'
import ClaimHotelPage from './pages/ClaimHotelPage.jsx'
import AdminDashboardPage from './pages/AdminDashboardPage.jsx'
import HotelOwnerDashboard from './pages/HotelOwnerDashboard.jsx'
import MonitoringDashboard from './pages/MonitoringDashboard.jsx'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/home" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />
      <Route path="/verify-email" element={<VerifyEmailPage />} />
      <Route path="/dashboard" element={<DashboardPage />} />
      <Route path="/search" element={<SearchPage />} />
      <Route path="/hotels" element={<HotelsPage />} />
      <Route path="/hotels/:hotelId" element={<HotelDetailsPage />} />
      <Route path="/hotels/:hotelId/claim" element={<ClaimHotelPage />} />
      <Route path="/admin" element={<AdminDashboardPage />} />
      <Route path="/monitoring" element={<MonitoringDashboard />} />
      <Route path="/owner/dashboard" element={<HotelOwnerDashboard />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}