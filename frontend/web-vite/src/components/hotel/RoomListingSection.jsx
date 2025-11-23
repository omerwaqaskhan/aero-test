import React, { useMemo } from 'react';
import RoomCard from './RoomCard';

const RoomListingSection = ({ rooms, offers, onBook }) => {
  // Match rooms with their specific offers (one-to-one matching)
  // Show all unique rooms - only deduplicate by room ID, not by room type name
  // (Different rooms can have the same type name, e.g., multiple "Standard Room" options)
  const displayItems = useMemo(() => {
    const items = [];
    const usedOfferIds = new Set();
    const seenRoomIds = new Set(); // Track room IDs to avoid duplicates
    
    // First, match rooms with their specific offers
    for (const room of rooms) {
      const roomId = room?.id;
      
      // Skip if we've already seen this room ID (by ID, not by name)
      if (roomId && seenRoomIds.has(roomId)) {
        continue;
      }
      
      const matchingOffer = offers.find(offer => offer.room_id === room.id);
      if (matchingOffer) {
        items.push({ room, offer: matchingOffer });
        usedOfferIds.add(matchingOffer.id);
        if (roomId) seenRoomIds.add(roomId);
      } else {
        // Room without a matching offer - show it without offer data
        items.push({ room, offer: null });
        if (roomId) seenRoomIds.add(roomId);
      }
    }
    
    // If we have offers that weren't matched to rooms, add them as separate items
    for (const offer of offers) {
      if (!usedOfferIds.has(offer.id)) {
        // Check if we already have a room with this room_id
        const existingRoom = rooms.find(r => r.id === offer.room_id);
        if (!existingRoom) {
          // Offer without a matching room - show it
          items.push({ room: null, offer });
          usedOfferIds.add(offer.id);
        }
      }
    }
    
    // Final deduplication by room ID and offer ID only
    const finalSeenRoomIds = new Set();
    const finalSeenOfferIds = new Set();
    const uniqueItems = [];
    for (const item of items) {
      if (item.room) {
        const roomId = item.room.id;
        
        // Skip if we've seen this room ID
        if (roomId && finalSeenRoomIds.has(roomId)) {
          continue;
        }
        
        finalSeenRoomIds.add(roomId);
        uniqueItems.push(item);
      } else if (item.offer) {
        // Offers without rooms - deduplicate by offer ID only
        const offerId = item.offer.id;
        
        if (offerId && finalSeenOfferIds.has(offerId)) {
          continue;
        }
        
        finalSeenOfferIds.add(offerId);
        uniqueItems.push(item);
      }
    }
    
    return uniqueItems;
  }, [rooms, offers]);

  if (displayItems.length === 0) {
    return (
      <div className="bg-white p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Rooms</h2>
        <div className="text-center py-12 text-gray-500">
          <p>No rooms available at this time.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Rooms</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {displayItems.map((item, index) => (
          <RoomCard
            key={item.room?.id || item.offer?.id || `item-${index}`}
            room={item.room}
            offer={item.offer}
            onBook={onBook}
          />
        ))}
      </div>
    </div>
  );
};

export default RoomListingSection;

