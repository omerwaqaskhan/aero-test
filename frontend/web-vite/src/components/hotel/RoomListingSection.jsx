import React, { useMemo } from 'react';
import RoomCard from './RoomCard';

const RoomListingSection = ({ rooms, offers, onBook }) => {
  // Match rooms with their specific offers (one-to-one matching)
  // Only show rooms that have matching offers, or show all unique rooms without duplicating offer data
  const displayItems = useMemo(() => {
    const items = [];
    const usedOfferIds = new Set();
    
    // First, match rooms with their specific offers
    for (const room of rooms) {
      const matchingOffer = offers.find(offer => offer.room_id === room.id);
      if (matchingOffer) {
        items.push({ room, offer: matchingOffer });
        usedOfferIds.add(matchingOffer.id);
      } else {
        // Room without a matching offer - show it without offer data
        items.push({ room, offer: null });
      }
    }
    
    // If we have offers that weren't matched to rooms, add them as separate items
    // But only if we don't have many rooms already (to avoid duplicates)
    if (items.length < 10) {
      for (const offer of offers) {
        if (!usedOfferIds.has(offer.id)) {
          // Check if we already have a room with this room_id
          const existingRoom = rooms.find(r => r.id === offer.room_id);
          if (!existingRoom) {
            items.push({ room: null, offer });
          }
        }
      }
    }
    
    // Deduplicate by room ID to avoid showing the same room twice
    const seenRoomIds = new Set();
    const uniqueItems = [];
    for (const item of items) {
      if (item.room) {
        if (!seenRoomIds.has(item.room.id)) {
          seenRoomIds.add(item.room.id);
          uniqueItems.push(item);
        }
      } else {
        // Offers without rooms - deduplicate by offer ID
        if (!seenRoomIds.has(item.offer.id)) {
          seenRoomIds.add(item.offer.id);
          uniqueItems.push(item);
        }
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

