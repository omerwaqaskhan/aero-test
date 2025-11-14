import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navigation from '../components/layout/navigation';
import { apiClient } from '../lib/api-client';
import { MapPin, Star, DollarSign, Filter, Search } from 'lucide-react';

const HotelsPage = () => {
  const navigate = useNavigate();
  const [hotels, setHotels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    city: '',
    country: '',
    minStars: 0,
    maxStars: 5,
    minRating: 0,
    maxRating: 5,
  });
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchHotels();
  }, []);

  const fetchHotels = async () => {
    setLoading(true);
    setError(null);
    try {
      // Call backend API to get all hotels
      const response = await apiClient.get('/v1/search-booking/hotels');
      console.log('Hotels response:', response);
      
      if (response.data && response.data.hotels) {
        setHotels(response.data.hotels || []);
      } else {
        setHotels(response.data || []);
      }
    } catch (err) {
      console.error('Error fetching hotels:', err);
      setError(err.message || 'Failed to fetch hotels');
    } finally {
      setLoading(false);
    }
  };

  const filteredHotels = hotels.filter(hotel => {
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      if (!hotel.name?.toLowerCase().includes(query) &&
          !hotel.city?.toLowerCase().includes(query) &&
          !hotel.country?.toLowerCase().includes(query)) {
        return false;
      }
    }
    
    if (filters.city && hotel.city?.toLowerCase() !== filters.city.toLowerCase()) {
      return false;
    }
    
    if (filters.country && hotel.country?.toLowerCase() !== filters.country.toLowerCase()) {
      return false;
    }
    
    if (hotel.stars < filters.minStars || hotel.stars > filters.maxStars) {
      return false;
    }
    
    if (hotel.rating && (hotel.rating < filters.minRating || hotel.rating > filters.maxRating)) {
      return false;
    }
    
    return true;
  });

  const uniqueCities = [...new Set(hotels.map(h => h.city).filter(Boolean))].sort();
  const uniqueCountries = [...new Set(hotels.map(h => h.country).filter(Boolean))].sort();

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      
      {/* Search and Filters */}
      <div className="bg-white shadow-sm border-b sticky top-16 z-40">
        <div className="container mx-auto px-4 py-6">
          <div className="flex flex-col md:flex-row gap-4">
            {/* Search Bar */}
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search hotels by name, city, or country..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* Filters */}
            <div className="flex gap-4 flex-wrap">
              <select
                value={filters.city}
                onChange={(e) => setFilters({...filters, city: e.target.value})}
                className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Cities</option>
                {uniqueCities.map(city => (
                  <option key={city} value={city}>{city}</option>
                ))}
              </select>

              <select
                value={filters.country}
                onChange={(e) => setFilters({...filters, country: e.target.value})}
                className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Countries</option>
                {uniqueCountries.map(country => (
                  <option key={country} value={country}>{country}</option>
                ))}
              </select>

              <select
                value={filters.minStars}
                onChange={(e) => setFilters({...filters, minStars: parseInt(e.target.value)})}
                className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="0">Min Stars</option>
                {[1, 2, 3, 4, 5].map(star => (
                  <option key={star} value={star}>{star}+ Stars</option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="container mx-auto px-4 py-8">
        {loading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Loading hotels...</p>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {!loading && !error && (
          <>
            {/* Results Count */}
            <div className="mb-6">
              <p className="text-gray-600">
                Showing <span className="font-semibold text-gray-900">{filteredHotels.length}</span> of{' '}
                <span className="font-semibold text-gray-900">{hotels.length}</span> hotels
              </p>
            </div>

            {/* Hotels Grid */}
            {filteredHotels.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredHotels.map((hotel) => (
                  <div
                    key={hotel.id}
                    className="bg-white rounded-xl shadow-sm hover:shadow-lg transition-all duration-300 overflow-hidden cursor-pointer"
                    onClick={() => navigate(`/hotels/${hotel.id}`)}
                  >
                    {/* Hotel Image */}
                    <div className="relative h-48 bg-gradient-to-br from-blue-400 via-purple-500 to-pink-500 overflow-hidden">
                      {hotel.images && hotel.images.length > 0 ? (
                        <img
                          src={hotel.images[0]}
                          alt={hotel.name}
                          className="w-full h-full object-cover"
                          onError={(e) => {
                            e.target.style.display = 'none';
                          }}
                        />
                      ) : null}
                      
                      {/* Stars Badge */}
                      {hotel.stars > 0 && (
                        <div className="absolute top-3 right-3 bg-white/90 px-3 py-1 rounded-full flex items-center gap-1">
                          <Star className="w-4 h-4 text-yellow-400 fill-current" />
                          <span className="text-sm font-semibold text-gray-900">{hotel.stars}</span>
                        </div>
                      )}
                    </div>

                    {/* Hotel Info */}
                    <div className="p-4">
                      <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2">
                        {hotel.name}
                      </h3>
                      
                      <div className="flex items-center text-gray-600 mb-3">
                        <MapPin className="w-4 h-4 mr-1" />
                        <span className="text-sm">
                          {hotel.city}, {hotel.country}
                        </span>
                      </div>

                      {/* Rating */}
                      {hotel.rating && (
                        <div className="flex items-center gap-2 mb-3">
                          <div className="flex items-center">
                            <Star className="w-4 h-4 text-yellow-400 fill-current" />
                            <span className="text-sm font-medium text-gray-900 ml-1">
                              {hotel.rating.toFixed(1)}
                            </span>
                          </div>
                        </div>
                      )}

                      {/* Amenities */}
                      {hotel.amenities && hotel.amenities.length > 0 && (
                        <div className="flex flex-wrap gap-2 mb-3">
                          {hotel.amenities.slice(0, 3).map((amenity, idx) => (
                            <span
                              key={idx}
                              className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded"
                            >
                              {amenity}
                            </span>
                          ))}
                          {hotel.amenities.length > 3 && (
                            <span className="text-xs text-gray-500">
                              +{hotel.amenities.length - 3} more
                            </span>
                          )}
                        </div>
                      )}

                      {/* View Details Button */}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/hotels/${hotel.id}`);
                        }}
                        className="w-full bg-gradient-to-r from-blue-600 to-teal-600 text-white py-2 px-4 rounded-lg hover:from-blue-700 hover:to-teal-700 transition-all font-semibold"
                      >
                        View Details
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <p className="text-gray-600 text-lg">No hotels found matching your criteria.</p>
                <button
                  onClick={() => {
                    setSearchQuery('');
                    setFilters({
                      city: '',
                      country: '',
                      minStars: 0,
                      maxStars: 5,
                      minRating: 0,
                      maxRating: 5,
                    });
                  }}
                  className="mt-4 text-blue-600 hover:text-blue-700 font-semibold"
                >
                  Clear Filters
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default HotelsPage;

