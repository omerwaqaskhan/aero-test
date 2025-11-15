import React from 'react';
import { Square, Users, Bed } from 'lucide-react';

const RoomCard = ({ room, offer, onBook }) => {
  const formatPrice = (price, currency = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(price);
  };

  // Get room image from hotel images or use placeholder
  const roomImage = room?.images?.[0] || offer?.hotel?.images?.[0] || null;

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden flex flex-col">
      {/* Top Section - Room Image */}
      <div className="w-full h-48 bg-gray-200 flex items-center justify-center">
        {roomImage ? (
          <img
            src={roomImage}
            alt={room?.room_type_name || 'Room'}
            className="w-full h-full object-cover"
            onError={(e) => {
              e.target.style.display = 'none';
              e.target.parentElement.classList.add('bg-gray-200');
            }}
          />
        ) : (
          <div className="w-full h-full bg-gray-200 flex items-center justify-center text-gray-400 text-sm">
            Room image
          </div>
        )}
      </div>

      {/* Room Content */}
      <div className="p-4 flex flex-col flex-1">
        {/* Room Title */}
        <h3 className="text-lg font-semibold text-gray-900 mb-3">
          {room?.room_type_name || offer?.room_type || 'Standard Room'}
        </h3>
        
        {/* Room Information */}
        <div className="space-y-2 mb-3">
          {room?.occupancy?.size || offer?.room_size ? (
            <div className="flex items-center space-x-2 text-sm text-gray-700">
              <Square className="w-4 h-4 text-gray-900" />
              <span>{room?.occupancy?.size || offer?.room_size} sqm</span>
            </div>
          ) : null}
          {room?.occupancy?.max_guests || offer?.guests ? (
            <div className="flex items-center space-x-2 text-sm text-gray-700">
              <Users className="w-4 h-4 text-gray-900" />
              <span>{room?.occupancy?.max_guests || offer?.guests} {room?.occupancy?.max_guests === 1 || offer?.guests === 1 ? 'person' : 'people'}</span>
            </div>
          ) : null}
          {room?.occupancy?.bed_type || offer?.bed_type ? (
            <div className="flex items-center space-x-2 text-sm text-gray-700">
              <Bed className="w-4 h-4 text-gray-900" />
              <span>{room?.occupancy?.bed_type || offer?.bed_type}</span>
            </div>
          ) : null}
        </div>
        
        {/* Cancellation policy info */}
        {offer?.cancellation_policy && (
          <div className="mb-4">
            {offer.cancellation_policy.free_cancellation ? (
              <p className="text-xs text-green-600 font-medium">
                ✓ Free cancellation
              </p>
            ) : (
              <p className="text-xs text-gray-500">
                Cancellation policy applies
              </p>
            )}
          </div>
        )}
        
        {/* Booking Button */}
        {offer && (
          <button
            onClick={() => onBook && onBook(offer)}
            className="w-full bg-blue-600 text-white py-2 rounded-md hover:bg-blue-700 transition-colors text-base font-medium mt-auto"
          >
            Book now for {formatPrice(offer.price, offer.currency)}
          </button>
        )}
      </div>
    </div>
  );
};

export default RoomCard;

