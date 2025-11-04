import React, { useState } from 'react';
import { Search, MapPin, Calendar, Users, ChevronDown } from 'lucide-react';

const SearchForm = ({ onSearch }) => {
  const [searchData, setSearchData] = useState({
    destination: '',
    checkIn: '',
    checkOut: '',
    guests: 1,
    rooms: 1
  });

  const [showGuestsDropdown, setShowGuestsDropdown] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (onSearch) {
      onSearch(searchData);
    }
  };

  const updateGuests = (type, value) => {
    setSearchData(prev => ({
      ...prev,
      guests: Math.max(1, prev.guests + (type === 'increment' ? 1 : -1))
    }));
  };

  return (
    <div className="bg-white rounded-2xl shadow-2xl p-8 -mt-12 relative z-10 border border-gray-200">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-gray-900">Search hotels</h2>
        <p className="text-gray-700 text-lg font-medium">Compare prices across 300+ booking sites</p>
      </div>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          {/* Destination */}
          <div className="relative md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-2">Destination</label>
            <div className="relative">
              <MapPin className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Where are you going?"
                className="w-full pl-10 pr-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                value={searchData.destination}
                onChange={(e) => setSearchData({...searchData, destination: e.target.value})}
                required
              />
            </div>
          </div>

          {/* Check-in Date */}
          <div className="relative">
            <label className="block text-sm font-medium text-gray-700 mb-2">Check-in</label>
            <div className="relative">
              <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="date"
                className="w-full pl-10 pr-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                value={searchData.checkIn}
                onChange={(e) => setSearchData({...searchData, checkIn: e.target.value})}
                min={new Date().toISOString().split('T')[0]}
                required
              />
            </div>
          </div>

          {/* Check-out Date */}
          <div className="relative">
            <label className="block text-sm font-medium text-gray-700 mb-2">Check-out</label>
            <div className="relative">
              <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="date"
                className="w-full pl-10 pr-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                value={searchData.checkOut}
                onChange={(e) => setSearchData({...searchData, checkOut: e.target.value})}
                min={searchData.checkIn || new Date().toISOString().split('T')[0]}
                required
              />
            </div>
          </div>

          {/* Guests */}
          <div className="relative">
            <label className="block text-sm font-medium text-gray-700 mb-2">Guests</label>
            <div className="relative">
              <Users className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <button
                type="button"
                onClick={() => setShowGuestsDropdown(!showGuestsDropdown)}
                className="w-full pl-10 pr-10 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all text-left flex items-center justify-between"
              >
                <span>{searchData.guests} {searchData.guests === 1 ? 'Guest' : 'Guests'}</span>
                <ChevronDown className="w-4 h-4 text-gray-400" />
              </button>
              
              {showGuestsDropdown && (
                <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-300 rounded-lg shadow-lg z-20 p-4">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-sm font-medium text-gray-700">Adults</span>
                    <div className="flex items-center space-x-3">
                      <button
                        type="button"
                        onClick={() => updateGuests('decrement')}
                        className="w-8 h-8 rounded-full border border-gray-300 flex items-center justify-center hover:bg-gray-50"
                        disabled={searchData.guests <= 1}
                      >
                        -
                      </button>
                      <span className="w-8 text-center">{searchData.guests}</span>
                      <button
                        type="button"
                        onClick={() => updateGuests('increment')}
                        className="w-8 h-8 rounded-full border border-gray-300 flex items-center justify-center hover:bg-gray-50"
                      >
                        +
                      </button>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => setShowGuestsDropdown(false)}
                    className="w-full bg-gradient-to-r from-blue-600 to-teal-600 text-white py-2 rounded-xl hover:from-blue-700 hover:to-teal-700 transition-all font-semibold"
                  >
                    Done
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Search Button */}
        <div className="pt-6">
          <button
            type="submit"
            className="w-full bg-blue-600 text-white px-8 py-5 rounded-xl hover:bg-blue-700 transition-all duration-300 transform hover:scale-105 shadow-lg hover:shadow-xl flex items-center justify-center space-x-3 font-bold text-lg"
          >
            <Search className="w-6 h-6" />
            <span>Search Now</span>
          </button>
        </div>
      </form>

      {/* Providers Strip */}
      <div className="mt-6 flex flex-wrap items-center justify-center gap-6 opacity-70">
        {['Booking.com','Expedia','Hotels.com','Agoda','Trip.com'].map((name) => (
          <span key={name} className="text-sm text-gray-500">{name}</span>
        ))}
      </div>

      {/* Popular Searches */}
      <div className="mt-6 pt-6 border-t border-gray-100">
        <p className="text-sm text-gray-600 mb-3">Popular destinations:</p>
        <div className="flex flex-wrap gap-2">
          {['Paris', 'London', 'New York', 'Tokyo', 'Dubai', 'Barcelona'].map((city) => (
            <button
              key={city}
              onClick={() => setSearchData({...searchData, destination: city})}
              className="px-4 py-2 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-lg text-sm font-medium transition-all border border-blue-200 hover:border-blue-300"
            >
              {city}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default SearchForm;

