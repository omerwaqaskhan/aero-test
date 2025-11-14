import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams, Link } from 'react-router-dom';
import Navigation from '../components/layout/navigation';
import Footer from '../components/layout/footer';
import { apiClient } from '../lib/api-client';
import HotelImageGallery from '../components/hotel/HotelImageGallery';
import NavigationTabs from '../components/hotel/NavigationTabs';
import PropertyOverviewSection from '../components/hotel/PropertyOverviewSection';
import RoomListingSection from '../components/hotel/RoomListingSection';
import ReviewsSection from '../components/hotel/ReviewsSection';
import LeadCaptureModal from '../components/revenue/LeadCaptureModal';
import AdSlot from '../components/revenue/AdSlot';

const HotelDetailsPage = () => {
  const { hotelId } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [hotel, setHotel] = useState(null);
  const [rooms, setRooms] = useState([]);
  const [offers, setOffers] = useState([]);
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('Overview');
  const [showLeadModal, setShowLeadModal] = useState(false);
  const [selectedDates, setSelectedDates] = useState({
    checkIn: searchParams.get('check_in') || '',
    checkOut: searchParams.get('check_out') || '',
    guests: parseInt(searchParams.get('guests') || '1'),
    rooms: parseInt(searchParams.get('rooms') || '1'),
  });

  useEffect(() => {
    fetchHotelDetails();
  }, [hotelId, selectedDates.checkIn, selectedDates.checkOut]);

  const fetchHotelDetails = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (selectedDates.checkIn) params.append('check_in', selectedDates.checkIn);
      if (selectedDates.checkOut) params.append('check_out', selectedDates.checkOut);
      params.append('guests', selectedDates.guests);
      params.append('rooms', selectedDates.rooms);

      const response = await apiClient.get(`/v1/search-booking/hotels/${hotelId}?${params.toString()}`);
      
      if (response.data) {
        // Ensure hotel data is properly set with validated images
        const hotelData = response.data.hotel;
        // Filter and validate images
        const validImages = (hotelData?.images || []).filter(img => {
          if (!img || typeof img !== 'string') return false;
          try {
            new URL(img);
            return true;
          } catch {
            return false;
          }
        });
        
        setHotel({ 
          ...hotelData, 
          images: validImages,
          review_count: reviews.length 
        });
        setRooms(response.data.rooms || []);
        setOffers(response.data.offers || []);
        setReviews(response.data.reviews || []);
      }
    } catch (err) {
      console.error('Error fetching hotel details:', err);
      setError(err.message || 'Failed to fetch hotel details');
    } finally {
      setLoading(false);
    }
  };

  const handleBook = (offer) => {
    // Show lead capture modal instead of direct redirect
    setShowLeadModal(true);
  };

  const handleLeadSuccess = (leadData) => {
    console.log('Lead created successfully:', leadData);
    setShowLeadModal(false);
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'Overview':
        return <PropertyOverviewSection hotel={hotel} />;
      case 'Rooms':
        return <RoomListingSection rooms={rooms} offers={offers} onBook={handleBook} />;
      case 'Amenities':
        return (
          <div className="bg-white p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Amenities</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {hotel.amenities?.map((amenity, index) => (
                <div key={index} className="flex items-center space-x-2 text-gray-700">
                  <span className="w-2 h-2 bg-blue-600 rounded-full"></span>
                  <span>{amenity}</span>
                </div>
              ))}
            </div>
          </div>
        );
      case 'Policies':
        return (
          <div className="bg-white p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Policies</h2>
            <div className="space-y-4">
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">Check-in</h3>
                <p className="text-gray-700">From 3:00 PM</p>
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">Check-out</h3>
                <p className="text-gray-700">Until 11:00 AM</p>
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">Cancellation</h3>
                <p className="text-gray-700">Free cancellation available for most bookings</p>
              </div>
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Loading hotel details...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !hotel) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center">
            <p className="text-red-600 text-lg mb-4">{error || 'Hotel not found'}</p>
            <button
              onClick={() => navigate('/hotels')}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
            >
              Back to Hotels
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      
      <HotelImageGallery hotel={hotel} />
      
      {/* Claim Hotel Banner */}
      <div className="bg-blue-50 border-b border-blue-200">
        <div className="container mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-700">
              Are you the owner of this hotel?
            </p>
            <Link
              to={`/hotels/${hotelId}/claim`}
              className="px-4 py-2 bg-blue-600 text-white text-sm font-semibold rounded-lg hover:bg-blue-700 transition-colors"
            >
              Claim This Hotel
            </Link>
          </div>
        </div>
      </div>
      
      <NavigationTabs activeTab={activeTab} onTabChange={setActiveTab} />
      
      <div className="container mx-auto">
        <div className="flex flex-col lg:flex-row gap-6">
          <div className="flex-1 lg:w-3/4">
            {renderTabContent()}
            
            {activeTab === 'Overview' && (
              <>
                <RoomListingSection rooms={rooms} offers={offers} onBook={handleBook} />
                <ReviewsSection hotel={hotel} reviews={reviews} />
              </>
            )}
          </div>
          
          {/* Ad Sidebar */}
          <div className="w-full lg:w-1/4 lg:min-w-[280px]">
            <div className="sticky top-4">
              <AdSlot adSlot="hotel_details_sidebar" pageType="hotel_details" />
            </div>
          </div>
        </div>
      </div>

      <Footer />

      {showLeadModal && hotel && (
        <LeadCaptureModal
          hotel={hotel}
          dates={selectedDates}
          onClose={() => setShowLeadModal(false)}
          onSuccess={handleLeadSuccess}
        />
      )}
    </div>
  );
};

export default HotelDetailsPage;
