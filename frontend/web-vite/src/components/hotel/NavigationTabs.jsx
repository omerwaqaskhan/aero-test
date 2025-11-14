import React from 'react';

const NavigationTabs = ({ activeTab, onTabChange }) => {
  const tabs = ['Overview', 'Rooms', 'Amenities', 'Policies'];

  return (
    <div className="flex border-b border-gray-200 bg-white px-6">
      {tabs.map((tab) => (
        <button
          key={tab}
          onClick={() => onTabChange(tab)}
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

