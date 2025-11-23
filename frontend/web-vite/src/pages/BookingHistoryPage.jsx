import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navigation from '../components/layout/navigation';
import Footer from '../components/layout/footer';
import { apiClient } from '../lib/api-client';
import { useAuth } from '../contexts/auth-context';
import { Calendar, MapPin, Users, Bed, DollarSign, CheckCircle, XCircle, Clock, FileText } from 'lucide-react';
import { BookingCardSkeleton } from '../components/ui/SkeletonLoader';
import { useToast } from '../hooks/use-toast-context';

export default function BookingHistoryPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { success, error: showError } = useToast();
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all'); // all, pending, confirmed, cancelled, completed

  useEffect(() => {
    if (!user) {
      navigate('/login?redirect=/bookings');
      return;
    }
    fetchBookings();
  }, [user, filter]);

  const fetchBookings = async () => {
    try {
      setLoading(true);
      const params = filter !== 'all' ? { status: filter } : {};
      const response = await apiClient.get('/v1/user/bookings', { params });
      setBookings(response.data);
    } catch (err) {
      console.error('Error fetching bookings:', err);
      setError('Failed to load bookings');
      showError('Error', 'Failed to load bookings. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const cancelBooking = async (bookingId) => {
    if (!confirm('Are you sure you want to cancel this booking?')) return;

    try {
      await apiClient.patch(`/v1/user/bookings/${bookingId}/status`, {
        status: 'cancelled'
      });
      fetchBookings();
      success('Success', 'Booking cancelled successfully');
    } catch (err) {
      console.error('Error cancelling booking:', err);
      showError('Error', 'Failed to cancel booking. Please try again.');
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'confirmed':
        return 'bg-green-100 text-green-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'cancelled':
        return 'bg-red-100 text-red-800';
      case 'completed':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'confirmed':
        return <CheckCircle className="w-4 h-4" />;
      case 'pending':
        return <Clock className="w-4 h-4" />;
      case 'cancelled':
        return <XCircle className="w-4 h-4" />;
      default:
        return <FileText className="w-4 h-4" />;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <div className="container mx-auto px-4 py-8">
          <div className="mb-6">
            <div className="h-8 bg-gray-200 rounded w-48 mb-2 animate-pulse"></div>
            <div className="h-4 bg-gray-200 rounded w-64 animate-pulse"></div>
          </div>
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <BookingCardSkeleton key={i} />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      
      <div className="container mx-auto px-4 py-8">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">My Bookings</h1>
          <p className="text-gray-600">View and manage your hotel bookings</p>
        </div>

        {/* Filter Tabs */}
        <div className="mb-6 flex gap-2 border-b border-gray-200">
          {['all', 'pending', 'confirmed', 'completed', 'cancelled'].map((status) => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={`px-4 py-2 font-medium text-sm capitalize transition-colors ${
                filter === status
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              {status}
            </button>
          ))}
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {bookings.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <Calendar className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">No bookings found</h3>
            <p className="text-gray-600 mb-6">
              {filter === 'all'
                ? "You haven't made any bookings yet."
                : `No ${filter} bookings found.`}
            </p>
            <button
              onClick={() => navigate('/search')}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
            >
              Search Hotels
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {bookings.map((booking) => (
              <div
                key={booking.id}
                className="bg-white rounded-lg shadow hover:shadow-md transition-shadow p-6"
              >
                <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
                  {/* Left: Booking Info */}
                  <div className="flex-1">
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <h3 className="text-xl font-semibold text-gray-900">
                            Booking #{booking.booking_reference || booking.id.slice(0, 8)}
                          </h3>
                          <span
                            className={`px-3 py-1 rounded-full text-xs font-medium flex items-center gap-1 ${getStatusColor(
                              booking.status
                            )}`}
                          >
                            {getStatusIcon(booking.status)}
                            {booking.status}
                          </span>
                        </div>
                        <p className="text-sm text-gray-500">
                          Booked on {new Date(booking.booked_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                      <div className="flex items-start gap-3">
                        <Calendar className="w-5 h-5 text-gray-400 mt-0.5" />
                        <div>
                          <p className="text-sm text-gray-500">Check-in</p>
                          <p className="font-medium text-gray-900">
                            {new Date(booking.check_in).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-start gap-3">
                        <Calendar className="w-5 h-5 text-gray-400 mt-0.5" />
                        <div>
                          <p className="text-sm text-gray-500">Check-out</p>
                          <p className="font-medium text-gray-900">
                            {new Date(booking.check_out).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-start gap-3">
                        <Users className="w-5 h-5 text-gray-400 mt-0.5" />
                        <div>
                          <p className="text-sm text-gray-500">Guests</p>
                          <p className="font-medium text-gray-900">{booking.guests}</p>
                        </div>
                      </div>
                      <div className="flex items-start gap-3">
                        <Bed className="w-5 h-5 text-gray-400 mt-0.5" />
                        <div>
                          <p className="text-sm text-gray-500">Rooms</p>
                          <p className="font-medium text-gray-900">{booking.rooms}</p>
                        </div>
                      </div>
                    </div>

                    {booking.special_requests && (
                      <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                        <p className="text-sm text-gray-500 mb-1">Special Requests</p>
                        <p className="text-sm text-gray-900">{booking.special_requests}</p>
                      </div>
                    )}
                  </div>

                  {/* Right: Price and Actions */}
                  <div className="md:text-right">
                    <div className="mb-4">
                      <div className="flex items-center gap-2 md:justify-end mb-1">
                        <DollarSign className="w-5 h-5 text-gray-400" />
                        <span className="text-2xl font-bold text-gray-900">
                          {booking.currency} {parseFloat(booking.total_price).toFixed(2)}
                        </span>
                      </div>
                      <p className="text-sm text-gray-500">
                        {booking.taxes_included ? 'Taxes included' : 'Taxes not included'}
                      </p>
                    </div>

                    <div className="flex flex-col gap-2">
                      <button
                        onClick={async () => {
                          try {
                            // Fetch hotel to get name for slug
                            const hotelRes = await apiClient.get(`/v1/search-booking/hotels/${booking.hotel_id}`);
                            if (hotelRes.data?.hotel?.name) {
                              const slug = hotelRes.data.hotel.name.toLowerCase().replace(/\s+/g, '-').replace(/[^\w-]/g, '');
                              navigate(`/hotels/${slug}`);
                            } else {
                              navigate(`/hotels/${booking.hotel_id}`);
                            }
                          } catch {
                            navigate(`/hotels/${booking.hotel_id}`);
                          }
                        }}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                      >
                        View Hotel
                      </button>
                      {booking.status === 'pending' || booking.status === 'confirmed' ? (
                        <button
                          onClick={() => cancelBooking(booking.id)}
                          className="px-4 py-2 border border-red-300 text-red-600 rounded-lg hover:bg-red-50 transition-colors text-sm font-medium"
                        >
                          Cancel Booking
                        </button>
                      ) : null}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <Footer />
    </div>
  );
}

