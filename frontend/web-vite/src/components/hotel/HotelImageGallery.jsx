import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronLeft, ChevronRight, MapPin } from 'lucide-react';
import FavoriteButton from '../user/FavoriteButton';

const HotelImageGallery = ({ hotel }) => {
  const navigate = useNavigate();
  const [selectedImageIndex, setSelectedImageIndex] = useState(0);

  const images = hotel?.images || [];
  // Filter and validate images - ensure they're valid URLs and hotel-specific
  const validImages = images.filter(img => {
    if (!img || typeof img !== 'string') return false;
    // Must be a valid URL
    try {
      new URL(img);
      return true;
    } catch {
      return false;
    }
  });
  const hasImages = validImages.length > 0;

  // Reset image index when hotel changes
  useEffect(() => {
    setSelectedImageIndex(0);
  }, [hotel?.id]);

  // Ensure selectedImageIndex is valid
  useEffect(() => {
    if (selectedImageIndex >= validImages.length && validImages.length > 0) {
      setSelectedImageIndex(0);
    }
  }, [validImages.length, selectedImageIndex]);

  const nextImage = () => {
    if (hasImages) {
      setSelectedImageIndex((prev) => (prev + 1) % validImages.length);
    }
  };

  const prevImage = () => {
    if (hasImages) {
      setSelectedImageIndex((prev) => (prev - 1 + validImages.length) % validImages.length);
    }
  };

  // Function to upgrade image quality
  const upgradeImageUrl = (url) => {
    if (!url) return url;
    
    // Booking.com image quality upgrade
    if (url.includes('bstatic.com')) {
      // Replace max300, max500, etc. with max1920x1080
      url = url.replace(/\/max\d+\//g, '/max1920x1080/');
      url = url.replace(/\/max\d+x\d+\//g, '/max1920x1080/');
    }
    
    // Expedia image quality upgrade
    if (url.includes('expedia.com') || url.includes('media.expedia.com')) {
      url = url.replace(/[?&]w=\d+/g, '?w=1920');
      url = url.replace(/[?&]h=\d+/g, '&h=1080');
      if (!url.includes('w=')) {
        url += (url.includes('?') ? '&' : '?') + 'w=1920&h=1080';
      }
    }
    
    // Hotels.com image quality upgrade
    if (url.includes('hotels.com') || url.includes('media.hotels.com')) {
      url = url.replace(/[?&]size=\w+/g, '?size=large');
      if (!url.includes('size=')) {
        url += (url.includes('?') ? '&' : '?') + 'size=large';
      }
    }
    
    return url;
  };

  return (
    <div className="relative w-full h-[40vh] min-h-[350px] max-h-[500px] bg-gray-200 overflow-hidden">
      {/* Main Image */}
      {hasImages ? (
        <img
          src={upgradeImageUrl(validImages[selectedImageIndex])}
          alt={`${hotel?.name || 'Hotel'} - Image ${selectedImageIndex + 1}`}
          className="w-full h-full object-cover"
          loading="eager"
          decoding="async"
          fetchpriority="high"
          key={`${hotel?.id}-${selectedImageIndex}`}
          onError={(e) => {
            // Try original URL if upgraded fails
            const originalUrl = validImages[selectedImageIndex];
            if (e.target.src !== originalUrl && originalUrl) {
              e.target.src = originalUrl;
            } else {
              e.target.src = '/images/bg.jpg';
            }
          }}
        />
      ) : (
        <div className="w-full h-full flex items-center justify-center text-gray-400">
          <p>No images available</p>
        </div>
      )}

      {/* Back Button - Top Left */}
      <button
        onClick={() => navigate(-1)}
        className="absolute top-6 left-6 bg-white/90 hover:bg-white p-2 rounded-full shadow-lg transition-all z-10"
      >
        <ChevronLeft className="w-6 h-6 text-black" />
      </button>

      {/* Favorite Button - Top Right */}
      {hotel?.id && (
        <div className="absolute top-6 right-6 z-10">
          <FavoriteButton hotelId={hotel.id} />
        </div>
      )}

      {/* Image Navigation Arrows */}
      {hasImages && validImages.length > 1 && (
        <>
          <button
            onClick={prevImage}
            className="absolute left-4 top-1/2 -translate-y-1/2 bg-white/90 hover:bg-white p-2 rounded-full shadow-lg transition-all z-10"
          >
            <ChevronLeft className="w-5 h-5 text-gray-900" />
          </button>
          <button
            onClick={nextImage}
            className="absolute right-4 top-1/2 -translate-y-1/2 bg-white/90 hover:bg-white p-2 rounded-full shadow-lg transition-all z-10"
          >
            <ChevronRight className="w-5 h-5 text-gray-900" />
          </button>
        </>
      )}

      {/* Image Dots Indicator */}
      {hasImages && validImages.length > 1 && (
        <div className="absolute bottom-24 left-1/2 -translate-x-1/2 flex gap-2 z-10">
          {validImages.map((_, index) => (
            <button
              key={`${hotel?.id}-dot-${index}`}
              onClick={() => setSelectedImageIndex(index)}
              className={`w-2 h-2 rounded-full transition-all ${
                index === selectedImageIndex ? 'bg-white w-8' : 'bg-white/50'
              }`}
            />
          ))}
        </div>
      )}

      {/* Hotel Info Overlay - Bottom */}
      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 via-black/50 to-transparent p-6">
        <div className="container mx-auto px-6">
          <div className="flex justify-between items-end">
            {/* Left Bottom - Hotel Name and Description */}
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-white mb-2">{hotel.name}</h1>
              <div className="flex items-center gap-2 text-white/90 text-base">
                <MapPin className="w-4 h-4" />
                <span>
                  {hotel.stars > 0 ? `${hotel.stars}-star hotel` : ''} located in the heart of {hotel.city}
                </span>
              </div>
            </div>

            {/* Right Bottom - Rating and Reviews */}
            {hotel.rating && (
              <div className="flex flex-col items-end">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-green-400 font-semibold text-lg">Excellent</span>
                  <span className="text-white/70 text-sm">{hotel.review_count || 0} reviews</span>
                </div>
                <div className="bg-green-500 rounded-lg px-4 py-2">
                  <span className="text-white text-2xl font-bold">{hotel.rating.toFixed(1)}</span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default HotelImageGallery;

