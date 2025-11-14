import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronLeft, ChevronRight, MapPin } from 'lucide-react';

const HotelImageGallery = ({ hotel }) => {
  const navigate = useNavigate();
  const [selectedImageIndex, setSelectedImageIndex] = useState(0);

  const images = hotel?.images || [];
  const hasImages = images.length > 0;

  const nextImage = () => {
    if (hasImages) {
      setSelectedImageIndex((prev) => (prev + 1) % images.length);
    }
  };

  const prevImage = () => {
    if (hasImages) {
      setSelectedImageIndex((prev) => (prev - 1 + images.length) % images.length);
    }
  };

  return (
    <div className="relative w-full h-[30vh] bg-gray-200 overflow-hidden">
      {/* Main Image */}
      {hasImages ? (
        <img
          src={images[selectedImageIndex]}
          alt={hotel.name}
          className="w-full h-full object-cover"
          onError={(e) => {
            e.target.src = '/images/bg.jpg';
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

      {/* Image Navigation Arrows */}
      {hasImages && images.length > 1 && (
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
      {hasImages && images.length > 1 && (
        <div className="absolute bottom-24 left-1/2 -translate-x-1/2 flex gap-2 z-10">
          {images.map((_, index) => (
            <button
              key={index}
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

