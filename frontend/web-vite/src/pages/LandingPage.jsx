import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';
import Navigation from '../components/layout/navigation';
import Footer from '../components/layout/footer';
import HeroSection from '../components/ui/hero-section';
import SearchForm from '../components/ui/search-form';
import DestinationCard from '../components/ui/destination-card';
import FeatureCard from '../components/ui/feature-card';
import TestimonialCard from '../components/ui/testimonial-card';
import { Shield, Clock, Award } from 'lucide-react';

const LandingPage = () => {
  const navigate = useNavigate();
  const featuredDestinations = [
    { id: 1, name: 'Paris', country: 'France', image: 'https://images.unsplash.com/photo-1502602898657-3e91760cbb34?q=80&w=1600&auto=format&fit=crop', price: '€89', rating: 4.8, reviews: 2847, hotels: 1247, discount: 26, description: 'Romance, art, and culture at every corner.' },
    { id: 2, name: 'Tokyo', country: 'Japan', image: 'https://images.unsplash.com/photo-1549692520-acc6669e2f0c?q=80&w=1600&auto=format&fit=crop', price: '¥12,500', rating: 4.9, reviews: 1923, hotels: 892, discount: 17, description: 'Tradition meets innovation in Japan’s capital.' },
    { id: 3, name: 'New York', country: 'USA', image: 'https://images.unsplash.com/photo-1468436139062-f60a71c5c892?q=80&w=1600&auto=format&fit=crop', price: '$156', rating: 4.7, reviews: 4521, hotels: 2156, discount: 22, description: 'Iconic skyline, endless things to do.' },
  ];

  const testimonials = [
    { name: 'Sophie Martin', location: 'Lyon, France', rating: 5, text: 'I found an incredible deal in minutes. LuftWay has become my first stop for hotels.', verified: true },
    { name: 'Akira Tanaka', location: 'Osaka, Japan', rating: 5, text: 'Clean design, blazing fast search, and great filters. Beats other comparators I tried.' },
    { name: 'Daniel Perez', location: 'Miami, USA', rating: 4, text: 'Loved how easy it was to compare across sites. Saved me serious money.' },
  ];

  const features = [
    { icon: <Shield className="w-8 h-8" />, title: 'Trusted Comparison', description: 'We compare prices from 300+ booking sites to bring you the best deals', color: 'blue' },
    { icon: <Clock className="w-8 h-8" />, title: 'Save Time', description: 'One quick search shows you prices across the web', color: 'green' },
    { icon: <Award className="w-8 h-8" />, title: 'Smart Filters', description: 'Find exactly what you need with powerful, easy filters', color: 'purple' },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />

      {/* Hero */}
      <HeroSection onSearch={() => document.getElementById('search')?.scrollIntoView({ behavior: 'smooth' })} />

      {/* Search */}
      <section id="search" className="py-12 bg-white">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <SearchForm />
        </div>
      </section>

      {/* Provider Logos */}
      <section className="py-6 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-wrap items-center justify-center gap-8 opacity-60 text-sm text-gray-600">
            <span>Booking.com</span>
            <span>Expedia</span>
            <span>Hotels.com</span>
            <span>Agoda</span>
            <span>Trip.com</span>
          </div>
        </div>
      </section>

      {/* Why LuftWay */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-teal-600 bg-clip-text text-transparent mb-4">Why choose LuftWay?</h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">Search once. Compare everywhere. Book the deal that’s right for you.</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <FeatureCard key={index} feature={feature} index={index} />
            ))}
          </div>
        </div>
      </section>

      {/* Popular Destinations */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-teal-600 bg-clip-text text-transparent mb-4">Popular destinations</h2>
            <p className="text-lg text-gray-600">Discover great places to stay around the world</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {featuredDestinations.map((destination) => (
              <DestinationCard key={destination.id} destination={destination} />
            ))}
          </div>
          
          {/* View All Button */}
          <div className="text-center mt-8">
            <button 
              onClick={() => navigate('/hotels')}
              className="inline-flex items-center bg-gradient-to-r from-blue-600 to-teal-600 text-white px-8 py-4 rounded-xl hover:from-blue-700 hover:to-teal-700 transition-all font-bold shadow-lg hover:shadow-xl"
            >
              View All Destinations
              <ChevronRight className="ml-2 w-5 h-5" />
            </button>
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-teal-600 bg-clip-text text-transparent mb-4">Loved by travelers</h2>
            <p className="text-lg text-gray-600">Real reviews from people who saved with LuftWay</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {testimonials.map((t, idx) => (
              <TestimonialCard key={idx} testimonial={t} />
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 bg-gradient-to-br from-blue-600 via-teal-600 to-cyan-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">Start comparing hotel prices with LuftWay</h2>
          <p className="text-white/90 mb-8">Millions of travelers use us to find their perfect stay</p>
          <a href="#search" className="inline-block bg-white text-blue-600 px-8 py-3 rounded-lg font-bold hover:bg-blue-50 transition-colors">Search hotels</a>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default LandingPage;