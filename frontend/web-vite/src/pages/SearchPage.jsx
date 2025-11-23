import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import Navigation from '../components/layout/navigation';
import Footer from '../components/layout/footer';
// Removed SearchForm import - using compact inline form instead
import { apiClient } from '../lib/api-client';
import { useAuth } from '../contexts/auth-context';
import { Bookmark } from 'lucide-react';
import { Search, Map, List, Filter, X, MapPin, Calendar, Users } from 'lucide-react';
import AdSlot from '../components/revenue/AdSlot';
import { ToastContainer } from '../components/ui/Toast';

export default function SearchPage() {
  const { user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [viewMode, setViewMode] = useState('list'); // 'list' or 'map'
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [savingSearch, setSavingSearch] = useState(false);
  const [toasts, setToasts] = useState([]);
  const [filters, setFilters] = useState({
    minPrice: null,
    maxPrice: null,
    stars: [],
    amenities: [],
    ratingMin: null
  });

  // Toast helper functions
  const addToast = (toast) => {
    const id = Date.now().toString();
    setToasts((prev) => [...prev, { ...toast, id }]);
  };

  const removeToast = (id) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  };

  // Get search params from URL
  const destination = searchParams.get('destination') || '';
  const checkIn = searchParams.get('check_in') || searchParams.get('checkIn') || '';
  const checkOut = searchParams.get('check_out') || searchParams.get('checkOut') || '';
  const guests = parseInt(searchParams.get('guests') || '1');
  const rooms = parseInt(searchParams.get('rooms') || '1');

  // Define performSearch before useEffect hooks that use it
  const performSearch = useCallback(async () => {
    setLoading(true);
    setError(null);

    // Get current values from searchParams
    const currentDestination = searchParams.get('destination') || '';
    const currentCheckIn = searchParams.get('check_in') || searchParams.get('checkIn') || '';
    const currentCheckOut = searchParams.get('check_out') || searchParams.get('checkOut') || '';
    const currentGuests = parseInt(searchParams.get('guests') || '1');
    const currentRooms = parseInt(searchParams.get('rooms') || '1');

    try {
      const params = new URLSearchParams({
        destination: currentDestination,
        check_in: currentCheckIn,
        check_out: currentCheckOut,
        guests: currentGuests.toString(),
        rooms: currentRooms.toString(),
        sort_by: 'price',
        sort_order: 'asc',
        page: '1',
        page_size: '20'
      });

      // Add filters
      if (filters.minPrice) params.append('min_price', filters.minPrice);
      if (filters.maxPrice) params.append('max_price', filters.maxPrice);
      if (filters.stars.length > 0) {
        filters.stars.forEach(star => params.append('stars', star));
      }
      if (filters.amenities.length > 0) {
        filters.amenities.forEach(amenity => params.append('amenities', amenity));
      }
      if (filters.ratingMin) params.append('rating_min', filters.ratingMin);

      // Use full path since baseURL is /api
      const response = await apiClient.get(`/v1/search-booking/search?${params}`);
      console.log('Search response:', response);
      if (response.data && response.data.results) {
        setResults(response.data.results || []);
      } else {
        // Handle case where response structure might be different
        setResults(response.data || []);
      }
    } catch (err) {
      console.error('Search error:', err);
      console.error('Error details:', {
        message: err.message,
        status: err.status,
        details: err.details,
        response: err.response
      });
      
      // Better error message handling
      let errorMessage = 'Failed to search hotels';
      if (err.message) {
        errorMessage = err.message;
      } else if (err.details && typeof err.details === 'string') {
        errorMessage = err.details;
      } else if (err.details && err.details.detail) {
        errorMessage = err.details.detail;
      } else if (err.details && err.details.message) {
        errorMessage = err.details.message;
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [searchParams, filters]);

  // Set default dates if destination is provided but dates are missing
  useEffect(() => {
    if (destination && !checkIn && !checkOut) {
      const today = new Date();
      const tomorrow = new Date(today);
      tomorrow.setDate(tomorrow.getDate() + 1);
      const dayAfterTomorrow = new Date(today);
      dayAfterTomorrow.setDate(dayAfterTomorrow.getDate() + 3);
      
      const defaultCheckIn = tomorrow.toISOString().split('T')[0];
      const defaultCheckOut = dayAfterTomorrow.toISOString().split('T')[0];
      
      // Update URL params with default dates
      const newParams = new URLSearchParams(searchParams);
      newParams.set('check_in', defaultCheckIn);
      newParams.set('check_out', defaultCheckOut);
      setSearchParams(newParams, { replace: true });
    }
  }, [destination, checkIn, checkOut, searchParams, setSearchParams]);

  useEffect(() => {
    // Get fresh values from searchParams after they might have been updated
    const currentCheckIn = searchParams.get('check_in') || searchParams.get('checkIn') || '';
    const currentCheckOut = searchParams.get('check_out') || searchParams.get('checkOut') || '';
    const currentDestination = searchParams.get('destination') || '';
    
    if (currentDestination && currentCheckIn && currentCheckOut) {
      performSearch();
    }
  }, [searchParams, performSearch]);
  
  // Separate effect for filters to avoid infinite loop
  useEffect(() => {
    const currentCheckIn = searchParams.get('check_in') || searchParams.get('checkIn') || '';
    const currentCheckOut = searchParams.get('check_out') || searchParams.get('checkOut') || '';
    const currentDestination = searchParams.get('destination') || '';
    
    if (currentDestination && currentCheckIn && currentCheckOut && Object.values(filters).some(v => v !== null && v !== undefined && (Array.isArray(v) ? v.length > 0 : true))) {
      performSearch();
    }
  }, [filters, searchParams, performSearch]);

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const clearFilters = () => {
    setFilters({
      minPrice: null,
      maxPrice: null,
      stars: [],
      amenities: [],
      ratingMin: null
    });
  };

  const saveSearch = async () => {
    if (!user) {
      window.location.href = '/login?redirect=' + encodeURIComponent(window.location.pathname + window.location.search);
      return;
    }

    setSavingSearch(true);
    try {
      const searchFilters = {};
      if (filters.minPrice) searchFilters.min_price = filters.minPrice;
      if (filters.maxPrice) searchFilters.max_price = filters.maxPrice;
      if (filters.stars.length > 0) searchFilters.stars = filters.stars;
      if (filters.amenities.length > 0) searchFilters.amenities = filters.amenities;
      if (filters.ratingMin) searchFilters.rating_min = filters.ratingMin;

      // Generate a meaningful name
      let searchName = destination || 'Search';
      if (checkIn && checkOut) {
        searchName = `${destination} - ${checkIn} to ${checkOut}`;
      } else if (checkIn) {
        searchName = `${destination} - ${checkIn}`;
      }

      const payload = {
        destination: destination || '',
        guests: guests || 1,
        rooms: rooms || 1,
        filters: searchFilters,
        name: searchName,
        notification_enabled: false,
      };

      // Only include dates if they're valid and not empty
      if (checkIn && typeof checkIn === 'string' && checkIn.trim() !== '') {
        payload.check_in = checkIn.trim();
      } else if (checkIn && checkIn !== null && checkIn !== '') {
        payload.check_in = checkIn;
      }
      if (checkOut && typeof checkOut === 'string' && checkOut.trim() !== '') {
        payload.check_out = checkOut.trim();
      } else if (checkOut && checkOut !== null && checkOut !== '') {
        payload.check_out = checkOut;
      }

      const response = await apiClient.post('/v1/user/saved-searches', payload);

      // Check if it was an update (has created_at different from updated_at) or new save
      const isUpdate = response.data?.updated_at && response.data?.created_at && 
                       response.data.updated_at !== response.data.created_at;

      addToast({
        type: 'success',
        title: isUpdate ? 'Search Updated!' : 'Search Saved!',
        description: isUpdate 
          ? `Your saved search for "${destination}" has been updated.`
          : `Your search for "${destination}" has been saved successfully.`,
        duration: 4000
      });
    } catch (err) {
      console.error('Error saving search:', err);
      const errorMessage = err?.details?.detail || err?.message || 'Failed to save search. Please try again.';
      addToast({
        type: 'error',
        title: 'Failed to Save Search',
        description: errorMessage,
        duration: 5000
      });
    } finally {
      setSavingSearch(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <ToastContainer toasts={toasts} onRemove={removeToast} />
      <Navigation />
      
      {/* Compact Search Bar */}
      <div className="bg-white shadow-sm border-b sticky top-16 z-40">
        <div className="container mx-auto px-4 py-3">
          <form 
            onSubmit={(e) => {
              e.preventDefault();
              const params = new URLSearchParams({
                destination: e.target.destination.value,
                check_in: e.target.check_in.value,
                check_out: e.target.check_out.value,
                guests: e.target.guests.value || '1',
                rooms: e.target.rooms.value || '1'
              });
              window.location.href = `/search?${params.toString()}`;
            }}
            className="flex items-center gap-2 flex-wrap"
          >
            {/* Destination */}
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <MapPin className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4 pointer-events-none" />
                <input
                  type="text"
                  name="destination"
                  placeholder="Destination"
                  defaultValue={destination}
                  className="w-full pl-10 pr-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-left"
                />
              </div>
            </div>

            {/* Check-in */}
            <div className="min-w-[140px]">
              <input
                type="date"
                name="check_in"
                defaultValue={checkIn}
                min={new Date().toISOString().split('T')[0]}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-left"
              />
            </div>

            {/* Check-out */}
            <div className="min-w-[140px]">
              <input
                type="date"
                name="check_out"
                defaultValue={checkOut}
                min={checkIn || new Date().toISOString().split('T')[0]}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-left"
              />
            </div>

            {/* Guests */}
            <div className="min-w-[100px]">
              <input
                type="number"
                name="guests"
                min="1"
                max="10"
                defaultValue={guests}
                placeholder="Guests"
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-center"
              />
            </div>

            {/* Rooms */}
            <div className="min-w-[100px]">
              <input
                type="number"
                name="rooms"
                min="1"
                max="5"
                defaultValue={rooms}
                placeholder="Rooms"
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-center"
              />
            </div>

            {/* Search Button */}
            <button
              type="submit"
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium text-sm flex items-center gap-2 whitespace-nowrap"
            >
              <Search className="w-4 h-4" />
              <span>Search</span>
            </button>
          </form>
        </div>
      </div>

      {/* Results Section */}
      <div className="container mx-auto px-4 py-8">
        {loading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Searching hotels...</p>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {!loading && !error && (
          <>
            {/* Results Header */}
            <div className="flex items-center justify-between mb-6">
              <div>
                <p className="text-gray-600">
                  {results.length} hotels found for {destination} • {checkIn} to {checkOut}
                </p>
              </div>
              
              <div className="flex items-center gap-4">
                {/* Save Search Button */}
                {user && (
                  <button
                    onClick={saveSearch}
                    disabled={savingSearch}
                    className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    <Bookmark className="w-4 h-4" />
                    {savingSearch ? 'Saving...' : 'Save Search'}
                  </button>
                )}
                {/* View Mode Toggle */}
                <div className="flex items-center bg-white rounded-lg border border-gray-200 p-1">
                  <button
                    onClick={() => setViewMode('list')}
                    className={`p-2 rounded ${viewMode === 'list' ? 'bg-blue-600 text-white' : 'text-gray-600'}`}
                  >
                    <List size={20} />
                  </button>
                  <button
                    onClick={() => setViewMode('map')}
                    className={`p-2 rounded ${viewMode === 'map' ? 'bg-blue-600 text-white' : 'text-gray-600'}`}
                  >
                    <Map size={20} />
                  </button>
                </div>

                {/* Filters Button */}
                <button
                  onClick={() => setFiltersOpen(!filtersOpen)}
                  className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-50"
                >
                  <Filter size={20} />
                  <span>Filters</span>
                </button>
              </div>
            </div>

            {/* Filters Sidebar */}
            {filtersOpen && (
              <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold">Filters</h3>
                  <button
                    onClick={clearFilters}
                    className="text-sm text-blue-600 hover:text-blue-700"
                  >
                    Clear all
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {/* Price Range */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Min Price
                    </label>
                    <input
                      type="number"
                      value={filters.minPrice || ''}
                      onChange={(e) => handleFilterChange('minPrice', e.target.value || null)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      placeholder="$0"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Max Price
                    </label>
                    <input
                      type="number"
                      value={filters.maxPrice || ''}
                      onChange={(e) => handleFilterChange('maxPrice', e.target.value || null)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      placeholder="$1000"
                    />
                  </div>

                  {/* Star Rating */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Star Rating
                    </label>
                    <div className="flex gap-2">
                      {[1, 2, 3, 4, 5].map(star => (
                        <button
                          key={star}
                          onClick={() => {
                            const newStars = filters.stars.includes(star)
                              ? filters.stars.filter(s => s !== star)
                              : [...filters.stars, star];
                            handleFilterChange('stars', newStars);
                          }}
                          className={`px-3 py-1 rounded ${
                            filters.stars.includes(star)
                              ? 'bg-blue-600 text-white'
                              : 'bg-gray-100 text-gray-700'
                          }`}
                        >
                          {star}⭐
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Rating Min */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Min Rating
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="5"
                      step="0.1"
                      value={filters.ratingMin || ''}
                      onChange={(e) => handleFilterChange('ratingMin', e.target.value || null)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      placeholder="0.0"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Results List */}
            {viewMode === 'list' && (
              <div className="flex flex-col lg:flex-row gap-6">
                <div className="flex-1 lg:w-3/4 space-y-4">
                {results.length === 0 ? (
                  <div className="text-center py-12">
                    <Search size={48} className="mx-auto text-gray-400 mb-4" />
                    <p className="text-gray-600">No hotels found. Try adjusting your search criteria.</p>
                  </div>
                ) : (
                  results.map((result) => (
                    <div
                      key={result.hotel.id}
                      className="bg-white rounded-lg border border-gray-200 overflow-hidden hover:shadow-xl transition-all duration-300"
                    >
                      <div className="flex flex-col md:flex-row h-full">
                        {/* Hotel Image */}
                        <div className="md:w-64 h-48 md:h-auto relative flex-shrink-0">
                          {result.hotel.images && result.hotel.images.length > 0 ? (
                            <img
                              src={result.hotel.images[0]}
                              alt={result.hotel.name.replace('Opens in new window', '').trim()}
                              className="w-full h-full object-cover"
                              onError={(e) => {
                                e.target.src = '/images/bg.jpg';
                              }}
                            />
                          ) : (
                            <div className="w-full h-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center">
                              <span className="text-white text-2xl font-bold">
                                {result.hotel.name.charAt(0).toUpperCase()}
                              </span>
                            </div>
                          )}
                          {result.is_sponsored && (
                            <div className="absolute top-2 left-2">
                              <span className="px-2 py-1 text-xs font-semibold bg-gradient-to-r from-yellow-400 to-orange-500 text-white rounded-full shadow-lg">
                                Sponsored
                              </span>
                            </div>
                          )}
                        </div>

                        {/* Hotel Info */}
                        <div className="flex-1 p-6 flex flex-col">
                          <div className="flex items-start justify-between mb-4">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-2">
                                <h3 className="text-xl font-bold text-gray-900 hover:text-blue-600 transition-colors cursor-pointer">
                                  {result.hotel.name.replace('Opens in new window', '').trim()}
                                </h3>
                              </div>
                              <p className="text-gray-600 mb-3 flex items-center gap-1">
                                <MapPin size={16} className="text-gray-400" />
                                {result.hotel.city}, {result.hotel.country}
                              </p>
                              <div className="flex items-center gap-4 mb-3">
                                {result.hotel.stars > 0 && (
                                  <span className="text-yellow-500 text-sm">
                                    {'⭐'.repeat(Math.min(result.hotel.stars, 5))}
                                  </span>
                                )}
                                {result.average_rating && (
                                  <span className="text-sm text-gray-700 font-medium">
                                    {result.average_rating.toFixed(1)} ⭐ ({result.review_count} {result.review_count === 1 ? 'review' : 'reviews'})
                                  </span>
                                )}
                              </div>
                              {result.hotel.amenities && result.hotel.amenities.length > 0 && (
                                <div className="flex flex-wrap gap-2 mb-4">
                                  {result.hotel.amenities.slice(0, 5).map((amenity, idx) => (
                                    <span
                                      key={idx}
                                      className="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded-md border border-blue-200"
                                    >
                                      {amenity}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </div>

                            {/* Price Section */}
                            <div className="text-right ml-6 min-w-[120px]">
                              {result.best_price ? (
                                <>
                                  <div className="text-3xl font-bold text-blue-600 mb-1">
                                    ${result.best_price.toFixed(2)}
                                  </div>
                                  <div className="text-sm text-gray-600 mb-2">per night</div>
                                  {result.offers && result.offers.length > 1 && (
                                    <div className="text-xs text-blue-600 font-medium">
                                      {result.offers.length} offers
                                    </div>
                                  )}
                                </>
                              ) : (
                                <div className="text-center">
                                  <div className="text-sm text-gray-500 mb-2">No offers for these dates</div>
                                  <div className="text-xs text-gray-400">Try different dates</div>
                                </div>
                              )}
                            </div>
                          </div>
                          
                          {/* Action Buttons */}
                          <div className="flex items-center gap-3 mt-auto pt-4 border-t border-gray-100">
                            <a
                              href={`/hotels/${result.hotel.slug || result.hotel.id}?check_in=${checkIn}&check_out=${checkOut}&guests=${guests}&rooms=${rooms}`}
                              className="px-4 py-2 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors text-sm"
                            >
                              {result.best_price ? 'View Details & Book' : 'View Hotel Details'}
                            </a>
                            {result.best_price && (
                              <button className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors text-sm">
                                Compare Prices
                              </button>
                            )}
                          </div>

                          {/* Offers with Details */}
                          {result.offers && result.offers.length > 0 && (
                            <div className="mt-4 pt-4 border-t border-gray-200">
                              <div className="mb-2 text-sm font-semibold text-gray-700">
                                Available Offers ({result.offers.length})
                              </div>
                              <div className="space-y-2">
                                {result.offers.slice(0, 3).map((offer) => {
                                  // Check if offer dates match search dates
                                  const offerCheckIn = new Date(offer.check_in);
                                  const offerCheckOut = new Date(offer.check_out);
                                  const searchCheckIn = new Date(checkIn);
                                  const searchCheckOut = new Date(checkOut);
                                  const datesMatch = offerCheckIn.getTime() === searchCheckIn.getTime() && 
                                                   offerCheckOut.getTime() === searchCheckOut.getTime();
                                  
                                  return (
                                    <div
                                      key={offer.id}
                                      className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200 hover:bg-gray-100 transition-colors"
                                    >
                                      <div className="flex-1">
                                        <div className="flex items-center gap-3">
                                          <div className="font-semibold text-blue-600">
                                            ${offer.price.toFixed(2)}/night
                                          </div>
                                          {offer.availability_count !== undefined && offer.availability_count > 0 && (
                                            <span className="text-xs text-gray-600">
                                              {offer.availability_count} {offer.availability_count === 1 ? 'room' : 'rooms'} available
                                            </span>
                                          )}
                                          {!datesMatch && (
                                            <span className="text-xs text-orange-600 bg-orange-50 px-2 py-1 rounded">
                                              Dates: {offer.check_in} to {offer.check_out}
                                            </span>
                                          )}
                                        </div>
                                        {offer.room_type && (
                                          <div className="text-xs text-gray-600 mt-1">
                                            {offer.room_type}
                                          </div>
                                        )}
                                        {offer.cancellation_policy && offer.cancellation_policy.free_cancellation && (
                                          <div className="text-xs text-green-600 mt-1">
                                            ✓ Free cancellation
                                          </div>
                                        )}
                                      </div>
                                      <button
                                        onClick={async () => {
                                          try {
                                            const response = await apiClient.post('/v1/search-booking/bookings/click', {
                                              offer_id: offer.id,
                                              provider: offer.provider,
                                              affiliate_link: `https://example.com/book/${offer.id}`
                                            });
                                            // In production, redirect to affiliate link
                                            window.open(`https://example.com/book/${offer.id}`, '_blank');
                                          } catch (err) {
                                            console.error('Click tracking error:', err);
                                          }
                                        }}
                                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium ml-4"
                                      >
                                        Book Now
                                      </button>
                                    </div>
                                  );
                                })}
                              </div>
                              {result.offers.length > 3 && (
                                <div className="mt-2 text-sm text-blue-600 text-center">
                                  +{result.offers.length - 3} more offers available
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))
                )}
                </div>
                
                {/* Ad Sidebar */}
                <div className="w-full lg:w-1/4 lg:min-w-[280px]">
                  <div className="sticky top-4">
                    <AdSlot adSlot="search_sidebar" pageType="search" />
                  </div>
                </div>
              </div>
            )}

            {/* Map View */}
            {viewMode === 'map' && (
              <div className="bg-white rounded-lg border border-gray-200 h-96 flex items-center justify-center">
                <p className="text-gray-600">Map view coming soon...</p>
              </div>
            )}
          </>
        )}
      </div>

      <Footer />
    </div>
  );
}

