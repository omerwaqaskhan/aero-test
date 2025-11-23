import { useState, useEffect } from 'react';
import { Star, X } from 'lucide-react';
import { apiClient } from '../../lib/api-client';

export default function ReviewForm({ hotel, bookingId, onSuccess, onClose }) {
  const [formData, setFormData] = useState({
    rating: 0,
    title: '',
    text: '',
    category_ratings: {
      cleanliness: 0,
      service: 0,
      value: 0,
      location: 0,
    },
    pros: [],
    cons: [],
  });
  const [proInput, setProInput] = useState('');
  const [conInput, setConInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (formData.rating === 0) {
      setError('Please select a rating');
      return;
    }

    setLoading(true);
    try {
      await apiClient.post('/v1/user/reviews', {
        hotel_id: hotel.id,
        booking_id: bookingId || null,
        rating: formData.rating,
        title: formData.title || null,
        text: formData.text || null,
        category_ratings: formData.category_ratings,
        pros: formData.pros,
        cons: formData.cons,
      });

      if (onSuccess) onSuccess();
      if (onClose) onClose();
    } catch (err) {
      console.error('Error submitting review:', err);
      setError(err.response?.data?.detail || 'Failed to submit review');
    } finally {
      setLoading(false);
    }
  };

  const addPro = () => {
    if (proInput.trim()) {
      setFormData({
        ...formData,
        pros: [...formData.pros, proInput.trim()],
      });
      setProInput('');
    }
  };

  const removePro = (index) => {
    setFormData({
      ...formData,
      pros: formData.pros.filter((_, i) => i !== index),
    });
  };

  const addCon = () => {
    if (conInput.trim()) {
      setFormData({
        ...formData,
        cons: [...formData.cons, conInput.trim()],
      });
      setConInput('');
    }
  };

  const removeCon = (index) => {
    setFormData({
      ...formData,
      cons: formData.cons.filter((_, i) => i !== index),
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded text-sm">
          {error}
        </div>
      )}

      {/* Overall Rating */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Overall Rating <span className="text-red-500">*</span>
        </label>
        <div className="flex gap-1">
          {[1, 2, 3, 4, 5].map((star) => (
            <button
              key={star}
              type="button"
              onClick={() => setFormData({ ...formData, rating: star })}
              className="focus:outline-none"
            >
              <Star
                className={`w-8 h-8 ${
                  star <= formData.rating
                    ? 'text-yellow-400 fill-current'
                    : 'text-gray-300'
                }`}
              />
            </button>
          ))}
        </div>
      </div>

      {/* Title */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Review Title
        </label>
        <input
          type="text"
          value={formData.title}
          onChange={(e) => setFormData({ ...formData, title: e.target.value })}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          placeholder="Summarize your experience"
          maxLength={500}
        />
      </div>

      {/* Review Text */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Your Review
        </label>
        <textarea
          value={formData.text}
          onChange={(e) => setFormData({ ...formData, text: e.target.value })}
          rows={5}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          placeholder="Share your experience..."
        />
      </div>

      {/* Category Ratings */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">
          Category Ratings
        </label>
        <div className="space-y-3">
          {['cleanliness', 'service', 'value', 'location'].map((category) => (
            <div key={category}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm text-gray-700 capitalize">{category}</span>
                <span className="text-sm text-gray-500">
                  {formData.category_ratings[category] || 0}/5
                </span>
              </div>
              <div className="flex gap-1">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    onClick={() =>
                      setFormData({
                        ...formData,
                        category_ratings: {
                          ...formData.category_ratings,
                          [category]: star,
                        },
                      })
                    }
                    className="focus:outline-none"
                  >
                    <Star
                      className={`w-5 h-5 ${
                        star <= (formData.category_ratings[category] || 0)
                          ? 'text-yellow-400 fill-current'
                          : 'text-gray-300'
                      }`}
                    />
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Pros */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Pros</label>
        <div className="flex gap-2 mb-2">
          <input
            type="text"
            value={proInput}
            onChange={(e) => setProInput(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                addPro();
              }
            }}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Add a positive point"
          />
          <button
            type="button"
            onClick={addPro}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
          >
            Add
          </button>
        </div>
        <div className="flex flex-wrap gap-2">
          {formData.pros.map((pro, index) => (
            <span
              key={index}
              className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm flex items-center gap-2"
            >
              {pro}
              <button
                type="button"
                onClick={() => removePro(index)}
                className="text-green-600 hover:text-green-800"
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
        </div>
      </div>

      {/* Cons */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Cons</label>
        <div className="flex gap-2 mb-2">
          <input
            type="text"
            value={conInput}
            onChange={(e) => setConInput(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                addCon();
              }
            }}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Add a negative point"
          />
          <button
            type="button"
            onClick={addCon}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
          >
            Add
          </button>
        </div>
        <div className="flex flex-wrap gap-2">
          {formData.cons.map((con, index) => (
            <span
              key={index}
              className="px-3 py-1 bg-red-100 text-red-800 rounded-full text-sm flex items-center gap-2"
            >
              {con}
              <button
                type="button"
                onClick={() => removeCon(index)}
                className="text-red-600 hover:text-red-800"
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
        </div>
      </div>

      <div className="flex gap-3 pt-4">
        <button
          type="submit"
          disabled={loading}
          className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
        >
          {loading ? 'Submitting...' : 'Submit Review'}
        </button>
        {onClose && (
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
          >
            Cancel
          </button>
        )}
      </div>
    </form>
  );
}

