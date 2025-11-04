import React from 'react';
import { Star, Quote } from 'lucide-react';

const TestimonialCard = ({ testimonial }) => {
  const { name, location, rating, text, avatar, verified = false } = testimonial;

  return (
    <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-all duration-300 transform hover:-translate-y-1 relative">
      {/* Quote Icon */}
      <div className="absolute top-4 right-4 text-gray-200">
        <Quote className="w-8 h-8" />
      </div>

      {/* Rating */}
      <div className="flex items-center mb-4">
        {[...Array(5)].map((_, i) => (
          <Star 
            key={i} 
            className={`w-4 h-4 ${
              i < rating ? 'text-yellow-400 fill-current' : 'text-gray-300'
            }`} 
          />
        ))}
      </div>

      {/* Testimonial Text */}
      <p className="text-gray-600 italic mb-6 leading-relaxed">
        "{text}"
      </p>

      {/* User Info */}
      <div className="flex items-center">
        <div className="w-12 h-12 bg-gradient-to-br from-blue-400 to-purple-500 rounded-full flex items-center justify-center text-white font-semibold text-lg">
          {name.charAt(0)}
        </div>
        <div className="ml-4">
          <div className="flex items-center">
            <h4 className="font-semibold text-gray-900">{name}</h4>
            {verified && (
              <div className="ml-2 w-4 h-4 bg-blue-500 rounded-full flex items-center justify-center">
                <svg className="w-2 h-2 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              </div>
            )}
          </div>
          <p className="text-sm text-gray-600">{location}</p>
        </div>
      </div>
    </div>
  );
};

export default TestimonialCard;

