import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navigation from '../components/layout/navigation';
import Footer from '../components/layout/footer';
import { apiClient } from '../lib/api-client';
import { useAuth } from '../contexts/auth-context';

export default function HotelOwnerDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [listing, setListing] = useState(null);
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    if (!user?.email) {
      setError('Please log in to access your dashboard');
      setLoading(false);
      return;
    }
    fetchListing();
  }, [user]);

  useEffect(() => {
    if (listing?.hotel_id) {
      fetchLeads(listing.hotel_id);
    }
  }, [listing]);

  const fetchListing = async () => {
    try {
      const response = await apiClient.get('/v1/revenue/owners/listings', {
        params: { owner_email: user.email }
      });
      setListing(response.data);
    } catch (err) {
      if (err.response?.status === 404) {
        setError('No listing found. Please claim a hotel first.');
      } else {
        setError('Failed to load listing');
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchLeads = async (hotelId) => {
    try {
      const response = await apiClient.get('/v1/revenue/owners/leads', {
        params: { hotel_id: hotelId, limit: 50 }
      });
      setLeads(response.data);
    } catch (err) {
      console.error('Error fetching leads:', err);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <div className="container mx-auto px-4 py-16">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Loading...</p>
          </div>
        </div>
        <Footer />
      </div>
    );
  }

  if (error && !listing) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <div className="container mx-auto px-4 py-16">
          <div className="max-w-2xl mx-auto bg-white rounded-lg shadow-lg p-8 text-center">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">No Listing Found</h2>
            <p className="text-gray-600 mb-6">{error}</p>
            <button
              onClick={() => navigate('/search')}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors"
            >
              Search Hotels to Claim
            </button>
          </div>
        </div>
        <Footer />
      </div>
    );
  }

  const stats = {
    totalLeads: leads.length,
    newLeads: leads.filter(l => l.status === 'new' || l.status === 'sent').length,
    responded: leads.filter(l => l.status === 'responded').length,
    booked: leads.filter(l => l.status === 'booked').length
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Hotel Owner Dashboard</h1>
          <p className="text-gray-600">Manage your listing and respond to inquiries</p>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow-sm mb-6">
          <div className="border-b border-gray-200">
            <nav className="flex -mb-px">
              <button
                onClick={() => setActiveTab('overview')}
                className={`px-6 py-4 text-sm font-medium border-b-2 ${
                  activeTab === 'overview'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Overview
              </button>
              <button
                onClick={() => setActiveTab('leads')}
                className={`px-6 py-4 text-sm font-medium border-b-2 ${
                  activeTab === 'leads'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Leads ({stats.totalLeads})
              </button>
              <button
                onClick={() => setActiveTab('listing')}
                className={`px-6 py-4 text-sm font-medium border-b-2 ${
                  activeTab === 'listing'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Listing Details
              </button>
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="bg-white rounded-lg shadow p-6">
                <div className="text-sm text-gray-600 mb-1">Total Leads</div>
                <div className="text-3xl font-bold text-gray-900">{stats.totalLeads}</div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="text-sm text-gray-600 mb-1">New Leads</div>
                <div className="text-3xl font-bold text-blue-600">{stats.newLeads}</div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="text-sm text-gray-600 mb-1">Responded</div>
                <div className="text-3xl font-bold text-yellow-600">{stats.responded}</div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="text-sm text-gray-600 mb-1">Booked</div>
                <div className="text-3xl font-bold text-green-600">{stats.booked}</div>
              </div>
            </div>

            {/* Recent Leads */}
            <div className="bg-white rounded-lg shadow">
              <div className="p-6 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">Recent Leads</h2>
              </div>
              <div className="p-6">
                {leads.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">No leads yet</p>
                ) : (
                  <div className="space-y-4">
                    {leads.slice(0, 5).map((lead) => (
                      <div key={lead.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-semibold text-gray-900">{lead.name || lead.email}</p>
                            <p className="text-sm text-gray-600">
                              {new Date(lead.check_in).toLocaleDateString()} - {new Date(lead.check_out).toLocaleDateString()}
                            </p>
                          </div>
                          <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                            lead.status === 'new' || lead.status === 'sent' ? 'bg-blue-100 text-blue-800' :
                            lead.status === 'responded' ? 'bg-yellow-100 text-yellow-800' :
                            lead.status === 'booked' ? 'bg-green-100 text-green-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {lead.status}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'leads' && (
          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">All Leads</h2>
            </div>
            <div className="p-6">
              {leads.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No leads yet</p>
              ) : (
                <div className="space-y-4">
                  {leads.map((lead) => (
                    <div key={lead.id} className="border border-gray-200 rounded-lg p-6 hover:bg-gray-50">
                      <div className="flex items-start justify-between mb-4">
                        <div>
                          <h3 className="font-semibold text-gray-900 text-lg">{lead.name || 'Guest'}</h3>
                          <p className="text-sm text-gray-600">{lead.email}</p>
                          {lead.phone && <p className="text-sm text-gray-600">{lead.phone}</p>}
                        </div>
                        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                          lead.status === 'new' || lead.status === 'sent' ? 'bg-blue-100 text-blue-800' :
                          lead.status === 'responded' ? 'bg-yellow-100 text-yellow-800' :
                          lead.status === 'booked' ? 'bg-green-100 text-green-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {lead.status}
                        </span>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                        <div>
                          <p className="text-sm text-gray-600">Check-in</p>
                          <p className="font-semibold">{new Date(lead.check_in).toLocaleDateString()}</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Check-out</p>
                          <p className="font-semibold">{new Date(lead.check_out).toLocaleDateString()}</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Guests</p>
                          <p className="font-semibold">{lead.guests || 'N/A'}</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Rooms</p>
                          <p className="font-semibold">{lead.rooms || 'N/A'}</p>
                        </div>
                      </div>
                      {lead.budget_range && (
                        <div className="mb-4">
                          <p className="text-sm text-gray-600">Budget</p>
                          <p className="font-semibold">{lead.budget_range}</p>
                        </div>
                      )}
                      {lead.special_requests && (
                        <div className="mb-4">
                          <p className="text-sm text-gray-600">Special Requests</p>
                          <p className="text-gray-900">{lead.special_requests}</p>
                        </div>
                      )}
                      <div className="flex gap-3">
                        <a
                          href={`mailto:${lead.email}`}
                          className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-semibold hover:bg-blue-700 transition-colors"
                        >
                          Reply via Email
                        </a>
                        {lead.phone && (
                          <a
                            href={`tel:${lead.phone}`}
                            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg text-sm font-semibold hover:bg-gray-300 transition-colors"
                          >
                            Call
                          </a>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'listing' && listing && (
          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">Listing Details</h2>
            </div>
            <div className="p-6 space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <p className="text-sm text-gray-600 mb-1">Package</p>
                  <p className="font-semibold text-lg capitalize">{listing.package}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 mb-1">Status</p>
                  <span className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${
                    listing.status === 'active' ? 'bg-green-100 text-green-800' :
                    listing.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {listing.status}
                  </span>
                </div>
                <div>
                  <p className="text-sm text-gray-600 mb-1">Verified</p>
                  <p className="font-semibold">{listing.verified ? 'Yes' : 'No'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 mb-1">Owner Email</p>
                  <p className="font-semibold">{listing.owner_email}</p>
                </div>
                {listing.owner_name && (
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Owner Name</p>
                    <p className="font-semibold">{listing.owner_name}</p>
                  </div>
                )}
                {listing.current_period_end && (
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Subscription Ends</p>
                    <p className="font-semibold">{new Date(listing.current_period_end).toLocaleDateString()}</p>
                  </div>
                )}
              </div>
              <div className="pt-6 border-t border-gray-200">
                <button
                  onClick={() => navigate(`/hotels/${listing.hotel_id}`)}
                  className="px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors"
                >
                  View Hotel Page
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      <Footer />
    </div>
  );
}

