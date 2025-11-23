import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navigation from '../components/layout/navigation';
import Footer from '../components/layout/footer';
import { apiClient } from '../lib/api-client';
import { useAuth } from '../contexts/auth-context';
import { Heart, MapPin, Star, Trash2 } from 'lucide-react';
import { HotelCardSkeleton } from '../components/ui/SkeletonLoader';
import { useToast } from '../hooks/use-toast-context';

export default function FavoritesPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { success, error: showError } = useToast();
  const [favorites, setFavorites] = useState([]);
  const [hotels, setHotels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!user) {
      navigate('/login?redirect=/favorites');
      return;
    }
    fetchFavorites();
  }, [user]);

  const fetchFavorites = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/v1/user/favorites');
      setFavorites(response.data);
      
      // Fetch hotel details for each favorite
      const hotelPromises = response.data.map((fav) =>
        apiClient.get(`/v1/search-booking/hotels/${fav.hotel_id}`).catch(() => null)
      );
      const hotelResponses = await Promise.all(hotelPromises);
      setHotels(hotelResponses.filter(Boolean).map((r) => r.data.hotel));
    } catch (err) {
      console.error('Error fetching favorites:', err);
      setError('Failed to load favorites');
      showError('Error', 'Failed to load favorites. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const removeFavorite = async (hotelId) => {
    try {
      await apiClient.delete(`/v1/user/favorites/${hotelId}`);
      setFavorites(favorites.filter((f) => f.hotel_id !== hotelId));
      setHotels(hotels.filter((h) => h.id !== hotelId));
      success('Success', 'Removed from favorites');
    } catch (err) {
      console.error('Error removing favorite:', err);
      showError('Error', 'Failed to remove favorite. Please try again.');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <div className="container mx-auto px-4 py-8">
          <div className="mb-6">
            <div className="h-8 bg-gray-200 rounded w-64 mb-2 animate-pulse"></div>
            <div className="h-4 bg-gray-200 rounded w-96 animate-pulse"></div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <HotelCardSkeleton key={i} />
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
          <h1 className="text-3xl font-bold text-gray-900 mb-2">My Favorites</h1>
          <p className="text-gray-600">Hotels you've saved for later</p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {hotels.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <Heart className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">No favorites yet</h3>
            <p className="text-gray-600 mb-6">
              Start exploring hotels and add them to your favorites!
            </p>
            <button
              onClick={() => navigate('/hotels')}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
            >
              Browse Hotels
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {hotels.map((hotel) => (
              <div
                key={hotel.id}
                className="bg-white rounded-lg shadow hover:shadow-md transition-shadow overflow-hidden cursor-pointer group"
                onClick={() => {
                  const slug = hotel.name ? hotel.name.toLowerCase().replace(/\s+/g, '-').replace(/[^\w-]/g, '') : hotel.id;
                  navigate(`/hotels/${slug}`);
                }}
              >
                {/* Hotel Image */}
                <div className="relative h-48 bg-gradient-to-br from-blue-100 to-purple-100 overflow-hidden">
                  {hotel.images && hotel.images.length > 0 ? (
                    <img
                      src={hotel.images[0]}
                      alt={hotel.name}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                      onError={(e) => {
                        e.target.style.display = 'none';
                      }}
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <span className="text-4xl text-gray-300 font-bold">
                        {hotel.name?.charAt(0).toUpperCase() || 'H'}
                      </span>
                    </div>
                  )}
                  
                  {/* Remove Favorite Button */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      removeFavorite(hotel.id);
                    }}
                    className="absolute top-2 right-2 p-2 bg-white/90 hover:bg-white rounded-full shadow-lg transition-all z-10"
                    title="Remove from favorites"
                  >
                    <Trash2 className="w-4 h-4 text-red-600" />
                  </button>

                  {/* Stars Badge */}
                  {hotel.stars > 0 && (
                    <div className="absolute top-2 left-2 bg-white/95 backdrop-blur-sm px-2 py-1 rounded-md flex items-center gap-1 shadow-sm">
                      <Star className="w-3.5 h-3.5 text-yellow-400 fill-current" />
                      <span className="text-xs font-semibold text-gray-900">{hotel.stars}</span>
                    </div>
                  )}
                </div>

                {/* Hotel Info */}
                <div className="p-4">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-1 group-hover:text-blue-600 transition-colors">
                    {hotel.name?.replace('Opens in new window', '').trim() || 'Hotel'}
                  </h3>
                  
                  <div className="flex items-center text-gray-500 mb-3 text-sm">
                    <MapPin className="w-4 h-4 mr-1 flex-shrink-0" />
                    <span className="truncate">
                      {hotel.city}, {hotel.country}
                    </span>
                  </div>

                  {hotel.rating && (
                    <div className="flex items-center gap-1 mb-3">
                      <Star className="w-4 h-4 text-yellow-400 fill-current" />
                      <span className="text-sm font-medium text-gray-900">
                        {hotel.rating.toFixed(1)}
                      </span>
                    </div>
                  )}

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      const slug = hotel.name ? hotel.name.toLowerCase().replace(/\s+/g, '-').replace(/[^\w-]/g, '') : hotel.id;
                      navigate(`/hotels/${slug}`);
                    }}
                    className="w-full bg-blue-600 text-white py-2 px-3 rounded-md hover:bg-blue-700 transition-colors text-sm font-medium"
                  >
                    View Details
                  </button>
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

