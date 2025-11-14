import React from 'react';
import { Plus, Minus } from 'lucide-react';

const ReviewCard = ({ review }) => {
  const getRatingBadge = (rating) => {
    if (rating >= 8) {
      return (
        <div className="flex items-center gap-1">
          <span className="text-green-600 font-semibold text-sm">Excellent</span>
          <span className="bg-green-100 text-green-800 text-sm font-bold rounded-full px-2 py-0.5">
            {rating.toFixed(0)}
          </span>
        </div>
      );
    } else if (rating >= 5) {
      return (
        <div className="flex items-center gap-1">
          <span className="text-orange-600 font-semibold text-sm">Average</span>
          <span className="bg-yellow-100 text-orange-800 text-sm font-bold rounded-full px-2 py-0.5">
            {rating.toFixed(1)}
          </span>
        </div>
      );
    } else {
      return (
        <div className="flex items-center gap-1">
          <span className="text-red-600 font-semibold text-sm">Poor</span>
          <span className="bg-red-100 text-red-800 text-sm font-bold rounded-full px-2 py-0.5">
            {rating.toFixed(1)}
          </span>
        </div>
      );
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      day: 'numeric',
      month: 'long',
      year: 'numeric'
    });
  };

  return (
    <div className="border-b border-gray-200 pb-6 last:border-0 last:pb-0">
      <h3 className="text-lg font-semibold text-gray-900 mb-1">
        {review.title || 'Great stay!'}
      </h3>
      <p className="text-sm text-gray-600 mb-2">{review.author || 'Guest'}</p>
      <p className="text-gray-800 text-base leading-relaxed mb-3">
        {review.text || 'No review text available.'}
      </p>
      
      {/* Pros */}
      {review.pros && review.pros.length > 0 && (
        <div className="mb-2 space-y-1">
          {review.pros.map((pro, index) => (
            <div key={index} className="flex items-center space-x-1 text-green-700 text-sm">
              <Plus className="w-4 h-4" />
              <span>{pro}</span>
            </div>
          ))}
        </div>
      )}
      
      {/* Cons */}
      {review.cons && review.cons.length > 0 && (
        <div className="mb-3 space-y-1">
          {review.cons.map((con, index) => (
            <div key={index} className="flex items-center space-x-1 text-orange-700 text-sm">
              <Minus className="w-4 h-4" />
              <span>{con}</span>
            </div>
          ))}
        </div>
      )}
      
      {/* Rating Badge and Date */}
      <div className="flex justify-between items-center mt-3">
        {getRatingBadge(review.rating)}
        <span className="text-xs text-gray-500">
          Reviewed on {formatDate(review.fetched_at)}
        </span>
      </div>
    </div>
  );
};

export default ReviewCard;

