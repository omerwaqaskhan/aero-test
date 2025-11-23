import React from 'react';
import { Search, Shield } from 'lucide-react';

const HeroSection = ({ onSearch }) => {
  return (
    <section
      className="relative text-white overflow-hidden min-h-[70vh] flex items-center"
      style={{
        backgroundImage: "linear-gradient(rgba(8, 47, 73, 0.72), rgba(6, 78, 59, 0.72)), url('/images/background.jpg')",
        backgroundSize: 'cover',
        backgroundPosition: 'center'
      }}
    >
      {/* Overlay for subtle vignette */}
      <div className="absolute inset-0 pointer-events-none" />

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 w-full">
        <div className="text-center">
          <div className="mb-6">
            <span className="inline-flex items-center gap-2 bg-black/30 backdrop-blur-md text-white px-6 py-2 rounded-full text-sm font-semibold mb-4 border border-white/30">
              Compare hotel prices on 300+ booking sites
            </span>
          </div>
          
          <h1 className="text-4xl md:text-6xl lg:text-7xl font-extrabold mb-6 leading-tight">
            <span className="block text-white drop-shadow-lg">Find your perfect stay</span>
            <span className="block text-white/90 text-2xl md:text-3xl font-semibold mt-3">with LuftWay — the hotel price comparison</span>
          </h1>
          
          <p className="text-lg md:text-xl mb-10 text-white/95 max-w-3xl mx-auto leading-relaxed font-medium drop-shadow-md">
            Search once and compare deals from Booking.com, Expedia, hotels and more — fast, simple, unbiased.
          </p>
          
          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12 max-w-4xl mx-auto">
            <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-lg">
              <div className="text-4xl font-bold text-gray-900 mb-2">5M+</div>
              <div className="text-gray-600 text-base font-medium">Properties</div>
            </div>
            <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-lg">
              <div className="text-4xl font-bold text-gray-900 mb-2">300+</div>
              <div className="text-gray-600 text-base font-medium">Booking sites</div>
            </div>
            <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-lg">
              <div className="text-4xl font-bold text-gray-900 mb-2">190+</div>
              <div className="text-gray-600 text-base font-medium">Countries</div>
            </div>
            <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-lg">
              <div className="text-4xl font-bold text-gray-900 mb-2">24/7</div>
              <div className="text-gray-600 text-base font-medium">Support</div>
            </div>
          </div>
          
          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button 
              onClick={() => onSearch && onSearch()}
              className="bg-gradient-to-r from-blue-600 to-teal-600 text-white hover:from-blue-700 hover:to-teal-700 px-10 py-4 rounded-xl font-bold text-lg transition-all duration-300 transform hover:scale-105 shadow-2xl hover:shadow-3xl flex items-center justify-center gap-2 focus:outline-none focus:ring-2 focus:ring-white/80 focus:ring-offset-2 focus:ring-offset-transparent"
            >
              <Search className="w-5 h-5" />
              Search Now
            </button>
            <button className="border-2 border-white/70 text-white hover:bg-white/20 px-10 py-4 rounded-xl font-bold text-lg transition-all duration-300 backdrop-blur-sm bg-white/10 flex items-center justify-center gap-2 focus:outline-none focus:ring-2 focus:ring-white/70 focus:ring-offset-2 focus:ring-offset-transparent">
              <Shield className="w-5 h-5" />
              Learn More
            </button>
          </div>
        </div>
      </div>

      {/* Scroll Indicator */}
      <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 animate-bounce">
        <div className="w-6 h-10 border-2 border-white border-opacity-50 rounded-full flex justify-center">
          <div className="w-1 h-3 bg-white bg-opacity-50 rounded-full mt-2 animate-pulse"></div>
        </div>
      </div>
    </section>
  );
};

export default HeroSection;

