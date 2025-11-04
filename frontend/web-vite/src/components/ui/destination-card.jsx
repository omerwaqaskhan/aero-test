import React from 'react';
import { Star, MapPin, Heart } from 'lucide-react';

const DestinationCard = ({ destination, onFavorite, isFavorite = false }) => {
  const {
    id,
    name,
    image,
    price,
    originalPrice,
    rating,
    reviews,
    hotels,
    country,
    description,
    discount
  } = destination;

  return (
    <div className="bg-white rounded-xl shadow-sm hover:shadow-lg transition-all duration-300 transform hover:-translate-y-1 overflow-hidden group">
      {/* Image Container */}
      <div className="relative h-48 overflow-hidden">
        {/* Actual image for reliable rendering */}
        <img
          src={image}
          alt={`${name}, ${country}`}
          className="absolute inset-0 w-full h-full object-cover transition-transform duration-500 group-hover:scale-110 z-10"
          onError={(e) => {
            e.currentTarget.onerror = null;
            e.currentTarget.src = '/images/bg.jpg';
          }}
          loading="lazy"
          crossOrigin="anonymous"
        />

        {/* Fallback gradient background if image fails */}
        <div className="absolute inset-0 bg-gradient-to-br from-blue-400 via-purple-500 to-pink-500 z-0" />

        {/* Subtle dark overlay for text contrast */}
        <div className="absolute inset-0 bg-black/20 group-hover:bg-black/30 transition-colors z-20" />

        {/* Discount Badge */}
        {discount && (
          <div className="absolute top-3 left-3 bg-gradient-to-r from-blue-600 to-teal-600 text-white px-3 py-1.5 rounded-full text-xs font-bold shadow-lg z-30">
            -{discount}%
          </div>
        )}

        {/* Favorite Button */}
        <button
          onClick={() => onFavorite && onFavorite(id)}
          className="absolute top-3 right-3 p-2 bg-white/90 hover:bg-white rounded-full transition-all duration-200 shadow-md hover:shadow-lg z-30"
        >
          <Heart 
            className={`w-5 h-5 ${isFavorite ? 'text-blue-600 fill-current' : 'text-gray-600'}`} 
          />
        </button>

        {/* Price */}
        <div className="absolute bottom-3 right-3 bg-white/95 px-3 py-2 rounded-lg z-30">
          <div className="text-right">
            <div className="text-lg font-bold text-gray-900">{price}</div>
            {originalPrice && (
              <div className="text-sm text-gray-500 line-through">{originalPrice}</div>
            )}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {/* Location */}
        <div className="flex items-center text-gray-600 mb-2">
          <MapPin className="w-4 h-4 mr-1" />
          <span className="text-sm">{country}</span>
        </div>

        {/* Title */}
        <h3 className="text-lg font-semibold text-gray-900 mb-2 group-hover:text-blue-600 transition-colors">
          {name}
        </h3>

        {/* Description */}
        {description && (
          <p className="text-sm text-gray-600 mb-3 line-clamp-2">{description}</p>
        )}

        {/* Rating and Reviews */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-1">
            <Star className="w-4 h-4 text-yellow-400 fill-current" />
            <span className="text-sm font-medium text-gray-900">{rating}</span>
            {reviews && (
              <span className="text-sm text-gray-500">({reviews} reviews)</span>
            )}
          </div>
          <span className="text-sm text-gray-500">{hotels} hotels</span>
        </div>

        {/* Action Button */}
        <button className="w-full bg-gray-100 hover:bg-gradient-to-r hover:from-blue-600 hover:to-teal-600 hover:text-white text-gray-700 py-3 px-4 rounded-xl transition-all duration-200 font-semibold">
          View Hotels
        </button>
      </div>
    </div>
  );
};

export default DestinationCard;

