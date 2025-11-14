import React from 'react';
import RoomCard from './RoomCard';

const RoomListingSection = ({ rooms, offers, onBook }) => {
  // Match rooms with offers
  const roomsWithOffers = rooms.map(room => {
    const roomOffer = offers.find(offer => offer.room_id === room.id) || offers[0];
    return { room, offer: roomOffer };
  });

  // If no rooms, create mock rooms from offers
  const displayItems = roomsWithOffers.length > 0 
    ? roomsWithOffers 
    : offers.map(offer => ({ room: null, offer }));

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
            key={item.room?.id || item.offer?.id || index}
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

