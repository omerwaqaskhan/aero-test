import React from 'react';

const FeatureCard = ({ feature, index }) => {
  const { icon, title, description, color = 'blue' } = feature;

  const colorClasses = {
    blue: 'text-blue-600 bg-blue-50',
    green: 'text-green-600 bg-green-50',
    purple: 'text-purple-600 bg-purple-50',
    red: 'text-red-600 bg-red-50',
    yellow: 'text-yellow-600 bg-yellow-50',
    indigo: 'text-indigo-600 bg-indigo-50'
  };

  return (
    <div 
      className="text-center p-6 bg-white rounded-xl shadow-sm hover:shadow-md transition-all duration-300 transform hover:-translate-y-1 group"
      style={{
        animationDelay: `${index * 100}ms`
      }}
    >
      {/* Icon Container */}
      <div className={`inline-flex items-center justify-center w-16 h-16 rounded-full mb-4 ${colorClasses[color]} group-hover:scale-110 transition-transform duration-300`}>
        {icon}
      </div>

      {/* Title */}
      <h3 className="text-xl font-semibold text-gray-900 mb-3 group-hover:text-gray-700 transition-colors">
        {title}
      </h3>

      {/* Description */}
      <p className="text-gray-600 leading-relaxed">
        {description}
      </p>

      {/* Hover Effect Line */}
      <div className="mt-4 h-1 bg-gradient-to-r from-transparent via-gray-200 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
    </div>
  );
};

export default FeatureCard;

