import React from 'react';
import { useNavigate, useParams, useLocation } from 'react-router-dom';

const NavigationTabs = ({ activeTab, onTabChange }) => {
  const tabs = ['Overview', 'Rooms', 'Amenities', 'Policies'];
  const { hotelSlug } = useParams();
  const navigate = useNavigate();
  const location = useLocation();

  const handleTabClick = (tab) => {
    if (onTabChange) {
      onTabChange(tab);
    } else {
      // Fallback navigation if onTabChange not provided
      const tabSlug = tab.toLowerCase();
      const newPath = tabSlug === 'overview' 
        ? `/hotels/${hotelSlug}`
        : `/hotels/${hotelSlug}/${tabSlug}`;
      navigate(newPath + location.search);
    }
  };

  return (
    <div className="flex border-b border-gray-200 bg-white px-6">
      {tabs.map((tab) => (
        <button
          key={tab}
          onClick={() => handleTabClick(tab)}
          className={`px-4 py-3 text-base font-medium transition-colors ${
            activeTab === tab
              ? 'font-semibold text-gray-900 border-b-2 border-blue-600 -mb-px'
              : 'text-gray-700 hover:text-blue-600'
          }`}
        >
          {tab}
        </button>
      ))}
    </div>
  );
};

export default NavigationTabs;

