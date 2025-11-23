import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronLeft, MapPin, Star } from 'lucide-react';

const HotelDetailsHeader = ({ hotel }) => {
  const navigate = useNavigate();

  return (
    <div className="bg-white border-b border-gray-200">
      <div className="container mx-auto px-6 py-6">
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <button
              onClick={() => navigate(-1)}
              className="mb-4 text-2xl text-black hover:text-blue-600 transition-colors"
            >
              <ChevronLeft className="w-6 h-6" />
            </button>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">{hotel.name}</h1>
            <div className="flex items-center gap-2 text-base text-gray-600">
              <MapPin className="w-4 h-4" />
              <span>
                {hotel.stars > 0 ? `${hotel.stars}-star hotel` : ''} located in the heart of {hotel.city}
              </span>
            </div>
          </div>
          {hotel.rating && (
            <div className="flex flex-col items-end">
              <div className="flex items-center">
                <div className="bg-green-700 text-white text-sm font-medium rounded-l-full pl-3 pr-2 py-1">
                  Excellent
                </div>
                <div className="bg-green-500 text-white text-lg font-bold rounded-r-full pr-3 pl-1 py-1">
                  {hotel.rating.toFixed(1)}
                </div>
              </div>
              <span className="text-xs text-gray-500 mt-1">
                {hotel.review_count || 0} reviews
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default HotelDetailsHeader;

