import React, { useState } from 'react';
import ReviewCard from './ReviewCard';
import ReviewForm from '../user/ReviewForm';
import { useAuth } from '../../contexts/auth-context';
import { X } from 'lucide-react';

const ReviewsSection = ({ hotel, reviews }) => {
  const { user } = useAuth();
  const [showAllReviews, setShowAllReviews] = useState(false);
  const [showReviewForm, setShowReviewForm] = useState(false);
  
  const categories = [
    { name: 'Cleanliness', rating: 10 },
    { name: 'Amenities', rating: 7 },
    { name: 'Location', rating: 9 },
    { name: 'Comfort', rating: 8 },
    { name: 'WiFi Connection', rating: 9 },
  ];

  const overallRating = hotel.rating || 9.6;
  
  // Show first 2 reviews by default, or all if showAllReviews is true
  const displayedReviews = showAllReviews ? reviews : reviews.slice(0, 2);
  const hasMoreReviews = reviews.length > 2;

  return (
    <div className="bg-white p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-gray-900">Reviews</h2>
        {user && (
          <button
            onClick={() => setShowReviewForm(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
          >
            Write a Review
          </button>
        )}
      </div>
      <div className="flex flex-col md:flex-row gap-8">
        {/* Left Column - Overall Score and Category Ratings */}
        <div className="w-full md:w-1/3">
          <div className="text-5xl font-bold text-blue-600 mb-6">
            {overallRating.toFixed(1)}/10
          </div>
          <div className="space-y-3">
            {categories.map((category, index) => (
              <div key={index} className="mb-2">
                <div className="flex justify-between items-center text-sm text-gray-700 mb-1">
                  <span>{category.name}</span>
                  <span className="font-medium">{category.rating}/10</span>
                </div>
                <div className="bg-gray-200 h-2 rounded-full w-full">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all"
                    style={{ width: `${(category.rating / 10) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column - Individual Reviews */}
        <div className="w-full md:w-2/3">
          {displayedReviews.length > 0 ? (
            <>
              <div className="space-y-6">
                {displayedReviews.map((review) => (
                  <ReviewCard key={review.id} review={review} />
                ))}
              </div>
              
              {/* More Views Button */}
              {hasMoreReviews && !showAllReviews && (
                <button
                  onClick={() => setShowAllReviews(true)}
                  className="mt-6 w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors text-base font-medium"
                >
                  More views
                </button>
              )}
              
              {showAllReviews && hasMoreReviews && (
                <button
                  onClick={() => setShowAllReviews(false)}
                  className="mt-6 w-full bg-gray-200 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-300 transition-colors text-base font-medium"
                >
                  Show less
                </button>
              )}
            </>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <p>No reviews available yet.</p>
            </div>
          )}
        </div>
      </div>

      {/* Review Form Modal */}
      {showReviewForm && hotel && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 p-6 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-gray-900">Write a Review</h2>
              <button
                onClick={() => setShowReviewForm(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
            <ReviewForm
              hotel={hotel}
              onSuccess={() => {
                setShowReviewForm(false);
                alert('Review submitted successfully!');
                window.location.reload(); // Refresh to show new review
              }}
              onClose={() => setShowReviewForm(false)}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default ReviewsSection;

