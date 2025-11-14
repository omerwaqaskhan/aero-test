import React from 'react';
import { Wifi, AirVent, Bath, Key, Car, Clock } from 'lucide-react';

const PropertyOverviewSection = ({ hotel }) => {
  // Define the specific amenities to display with their icons
  const amenityList = [
    { name: 'Free Wifi', icon: Wifi },
    { name: 'Air conditioning', icon: AirVent },
    { name: 'Private bathroom', icon: Bath },
    { name: 'Key card access', icon: Key },
    { name: 'Free parking', icon: Car },
    { name: '24-hour front desk', icon: Clock },
  ];

  // Check if hotel has these amenities, otherwise show all
  const displayAmenities = hotel.amenities?.length > 0
    ? amenityList.filter(amenity => 
        hotel.amenities.some(h => 
          h.toLowerCase().includes(amenity.name.toLowerCase()) ||
          amenity.name.toLowerCase().includes(h.toLowerCase())
        )
      )
    : amenityList;

  // Split into two columns
  const leftColumn = displayAmenities.slice(0, 4);
  const rightColumn = displayAmenities.slice(4, 6);

  return (
    <div className="bg-white p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Property overview</h2>
      <div className="flex flex-col md:flex-row gap-8">
        {/* Left Section - Amenities */}
        <div className="flex-1">
          <div className="grid grid-cols-2 gap-y-3 gap-x-8">
            {/* Left Column */}
            <div className="space-y-3">
              {leftColumn.map((amenity, index) => {
                const Icon = amenity.icon;
                return (
                  <div key={index} className="flex items-center space-x-2 text-gray-700 text-base">
                    <Icon className="w-5 h-5 text-gray-900" />
                    <span>{amenity.name}</span>
                  </div>
                );
              })}
            </div>
            {/* Right Column */}
            <div className="space-y-3">
              {rightColumn.map((amenity, index) => {
                const Icon = amenity.icon;
                return (
                  <div key={index} className="flex items-center space-x-2 text-gray-700 text-base">
                    <Icon className="w-5 h-5 text-gray-900" />
                    <span>{amenity.name}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
        
        {/* Right Section - Map Placeholder */}
        <div className="w-full md:w-96">
          <div className="bg-gray-100 rounded-lg w-full h-64 flex items-center justify-center">
            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-2 bg-gray-200 rounded-lg flex items-center justify-center">
                <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              <p className="text-gray-400 text-sm">Map view coming soon</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PropertyOverviewSection;

