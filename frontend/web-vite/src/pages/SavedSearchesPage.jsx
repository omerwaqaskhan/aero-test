import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navigation from '../components/layout/navigation';
import Footer from '../components/layout/footer';
import { apiClient } from '../lib/api-client';
import { useAuth } from '../contexts/auth-context';
import { Search, Calendar, Users, Bed, Trash2, Bell, BellOff } from 'lucide-react';

export default function SavedSearchesPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [savedSearches, setSavedSearches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!user) {
      navigate('/login?redirect=/saved-searches');
      return;
    }
    fetchSavedSearches();
  }, [user]);

  const fetchSavedSearches = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/v1/user/saved-searches');
      setSavedSearches(response.data);
    } catch (err) {
      console.error('Error fetching saved searches:', err);
      setError('Failed to load saved searches');
    } finally {
      setLoading(false);
    }
  };

  const deleteSearch = async (searchId) => {
    try {
      await apiClient.delete(`/v1/user/saved-searches/${searchId}`);
      setSavedSearches(savedSearches.filter((s) => s.id !== searchId));
    } catch (err) {
      console.error('Error deleting saved search:', err);
      alert('Failed to delete saved search. Please try again.');
    }
  };

  const runSearch = (search) => {
    const params = new URLSearchParams({
      destination: search.destination,
    });
    if (search.check_in) params.append('check_in', search.check_in);
    if (search.check_out) params.append('check_out', search.check_out);
    if (search.guests) params.append('guests', search.guests);
    if (search.rooms) params.append('rooms', search.rooms);
    
    // Add filters
    if (search.filters) {
      Object.entries(search.filters).forEach(([key, value]) => {
        if (value !== null && value !== undefined) {
          if (Array.isArray(value)) {
            value.forEach((v) => params.append(key, v));
          } else {
            params.append(key, value);
          }
        }
      });
    }
    
    navigate(`/search?${params.toString()}`);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Loading saved searches...</p>
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
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Saved Searches</h1>
          <p className="text-gray-600">Quick access to your favorite search queries</p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {savedSearches.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <Search className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">No saved searches</h3>
            <p className="text-gray-600 mb-6">
              Save your search queries to quickly access them later!
            </p>
            <button
              onClick={() => navigate('/search')}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
            >
              Start Searching
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {savedSearches.map((search) => (
              <div
                key={search.id}
                className="bg-white rounded-lg shadow hover:shadow-md transition-shadow p-6"
              >
                <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
                  {/* Left: Search Info */}
                  <div className="flex-1">
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h3 className="text-xl font-semibold text-gray-900 mb-1">
                          {search.name || search.destination}
                        </h3>
                        <p className="text-sm text-gray-500">
                          Saved on {new Date(search.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      {search.notification_enabled && (
                        <span className="px-3 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-full flex items-center gap-1">
                          <Bell className="w-3 h-3" />
                          Notifications On
                        </span>
                      )}
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                      <div className="flex items-start gap-2">
                        <Search className="w-4 h-4 text-gray-400 mt-0.5" />
                        <div>
                          <p className="text-xs text-gray-500">Destination</p>
                          <p className="text-sm font-medium text-gray-900">{search.destination}</p>
                        </div>
                      </div>
                      {search.check_in && (
                        <div className="flex items-start gap-2">
                          <Calendar className="w-4 h-4 text-gray-400 mt-0.5" />
                          <div>
                            <p className="text-xs text-gray-500">Check-in</p>
                            <p className="text-sm font-medium text-gray-900">
                              {new Date(search.check_in).toLocaleDateString()}
                            </p>
                          </div>
                        </div>
                      )}
                      {search.check_out && (
                        <div className="flex items-start gap-2">
                          <Calendar className="w-4 h-4 text-gray-400 mt-0.5" />
                          <div>
                            <p className="text-xs text-gray-500">Check-out</p>
                            <p className="text-sm font-medium text-gray-900">
                              {new Date(search.check_out).toLocaleDateString()}
                            </p>
                          </div>
                        </div>
                      )}
                      <div className="flex items-start gap-2">
                        <Users className="w-4 h-4 text-gray-400 mt-0.5" />
                        <div>
                          <p className="text-xs text-gray-500">Guests</p>
                          <p className="text-sm font-medium text-gray-900">{search.guests || 1}</p>
                        </div>
                      </div>
                    </div>

                    {Object.keys(search.filters || {}).length > 0 && (
                      <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                        <p className="text-xs text-gray-500 mb-2">Filters:</p>
                        <div className="flex flex-wrap gap-2">
                          {Object.entries(search.filters).map(([key, value]) => (
                            <span
                              key={key}
                              className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded"
                            >
                              {key}: {Array.isArray(value) ? value.join(', ') : value}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Right: Actions */}
                  <div className="flex flex-col gap-2 md:min-w-[200px]">
                    <button
                      onClick={() => runSearch(search)}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium flex items-center justify-center gap-2"
                    >
                      <Search className="w-4 h-4" />
                      Run Search
                    </button>
                    <button
                      onClick={() => deleteSearch(search.id)}
                      className="px-4 py-2 border border-red-300 text-red-600 rounded-lg hover:bg-red-50 transition-colors text-sm font-medium flex items-center justify-center gap-2"
                    >
                      <Trash2 className="w-4 h-4" />
                      Delete
                    </button>
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

