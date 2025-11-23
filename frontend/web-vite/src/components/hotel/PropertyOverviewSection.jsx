import React, { useMemo } from 'react';
import RoomCard from './RoomCard';

const PropertyOverviewSection = ({ hotel, rooms = [], offers = [], onBook, onViewMoreRooms }) => {
  // Show description or property_overview if available
  const description = hotel?.description || hotel?.property_overview || null;

  // Only show amenities that actually exist in hotel.amenities (real data only)
  const displayAmenities = hotel?.amenities?.length > 0
    ? hotel.amenities.slice(0, 6) // Show first 6 real amenities
    : [];

  // Prepare room cards for overview (show 3-4 rooms)
  // Deduplicate by room_type_name to avoid showing duplicate room types
  const previewRooms = useMemo(() => {
    const items = [];
    const usedOfferIds = new Set();
    const seenRoomNames = new Set(); // Track room types to avoid duplicates
    
    // Match rooms with their specific offers
    for (const room of rooms) {
      if (items.length >= 4) break; // Limit to 4 rooms
      
      const roomNameLower = room?.room_type_name?.toLowerCase() || '';
      
      // Skip if we've already seen this room type
      if (roomNameLower && seenRoomNames.has(roomNameLower)) {
        continue;
      }
      
      const matchingOffer = offers.find(offer => offer.room_id === room.id);
      if (matchingOffer) {
        items.push({ room, offer: matchingOffer });
        usedOfferIds.add(matchingOffer.id);
        if (roomNameLower) seenRoomNames.add(roomNameLower);
      } else {
        items.push({ room, offer: null });
        if (roomNameLower) seenRoomNames.add(roomNameLower);
      }
    }
    
    // If we have fewer than 4 rooms, add offers without rooms
    if (items.length < 4) {
      for (const offer of offers) {
        if (items.length >= 4) break;
        if (!usedOfferIds.has(offer.id)) {
          const existingRoom = rooms.find(r => r.id === offer.room_id);
          if (!existingRoom) {
            // Check if we already have an offer with the same room_type
            const offerRoomType = offer.room_type?.toLowerCase() || '';
            if (!offerRoomType || !seenRoomNames.has(offerRoomType)) {
              items.push({ room: null, offer });
              usedOfferIds.add(offer.id);
              if (offerRoomType) seenRoomNames.add(offerRoomType);
            }
          }
        }
      }
    }
    
    return items.slice(0, 4); // Max 4 rooms in preview
  }, [rooms, offers]);

  const hasMoreRooms = rooms.length > 4 || offers.length > previewRooms.length;

  return (
    <div className="bg-white p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Property overview</h2>
      
      {/* Description */}
      {description ? (
        <div className="mb-6">
          <p className="text-gray-700 leading-relaxed whitespace-pre-line">{description}</p>
        </div>
      ) : (
        <div className="mb-6">
          <p className="text-gray-500 italic">Description: Not Available</p>
        </div>
      )}

      {/* Room Preview */}
      {previewRooms.length > 0 && (
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Available Rooms</h3>
            {hasMoreRooms && (
              <button
                onClick={onViewMoreRooms}
                className="text-blue-600 hover:text-blue-700 font-medium text-sm transition-colors"
              >
                View more rooms →
              </button>
            )}
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {previewRooms.map((item, index) => (
              <RoomCard
                key={item.room?.id || item.offer?.id || `preview-${index}`}
                room={item.room}
                offer={item.offer}
                onBook={onBook}
              />
            ))}
          </div>
        </div>
      )}

      {/* Amenities */}
      {displayAmenities.length > 0 ? (
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Key Amenities</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {displayAmenities.map((amenity, index) => (
              <div key={index} className="flex items-center space-x-2 text-gray-700">
                <span className="w-2 h-2 bg-blue-600 rounded-full"></span>
                <span>{amenity}</span>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Key Amenities</h3>
          <p className="text-gray-500 italic">Not Available</p>
        </div>
      )}
      
      {/* Map */}
      <div className="mt-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Location</h3>
        {hotel?.latitude && hotel?.longitude ? (
          <div className="rounded-lg overflow-hidden border border-gray-200 shadow-sm">
            <iframe
              width="100%"
              height="400"
              style={{ border: 0 }}
              loading="lazy"
              allowFullScreen
              referrerPolicy="no-referrer-when-downgrade"
              src={`https://www.openstreetmap.org/export/embed.html?bbox=${hotel.longitude - 0.01},${hotel.latitude - 0.01},${hotel.longitude + 0.01},${hotel.latitude + 0.01}&layer=mapnik&marker=${hotel.latitude},${hotel.longitude}`}
              title={`${hotel.name} location`}
            />
            <div className="p-3 bg-gray-50 border-t border-gray-200 flex items-center justify-between">
              <p className="text-sm text-gray-600">
                <strong>{hotel.name}</strong>
                {hotel.city && hotel.country && (
                  <span className="ml-2">• {hotel.city}, {hotel.country}</span>
                )}
              </p>
              <div className="flex gap-3">
                <a
                  href={`https://www.openstreetmap.org/?mlat=${hotel.latitude}&mlon=${hotel.longitude}&zoom=15`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-blue-600 hover:text-blue-700"
                >
                  OpenStreetMap →
                </a>
                <a
                  href={`https://www.google.com/maps/search/?api=1&query=${hotel.latitude},${hotel.longitude}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-blue-600 hover:text-blue-700"
                >
                  Google Maps →
                </a>
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-gray-100 rounded-lg w-full h-64 flex items-center justify-center">
            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-2 bg-gray-200 rounded-lg flex items-center justify-center">
                <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              <p className="text-gray-500 text-sm">Location information not available</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PropertyOverviewSection;

