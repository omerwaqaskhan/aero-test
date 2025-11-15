import React from 'react';

const PropertyOverviewSection = ({ hotel }) => {
  // Show description or property_overview if available
  const description = hotel?.description || hotel?.property_overview || null;

  // Only show amenities that actually exist in hotel.amenities (real data only)
  const displayAmenities = hotel?.amenities?.length > 0
    ? hotel.amenities.slice(0, 6) // Show first 6 real amenities
    : [];

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
      
      {/* Map Placeholder */}
      <div className="mt-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Location</h3>
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
  );
};

export default PropertyOverviewSection;

