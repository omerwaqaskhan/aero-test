import React, { useState } from 'react';
import { Search, MapPin, Calendar, Users, Star, ArrowRight, Shield, Clock, Award, Heart, ChevronRight, User as UserIcon } from 'lucide-react';
import Navigation from '../components/layout/navigation';
import Footer from '../components/layout/footer';
import HeroSection from '../components/ui/hero-section';
import SearchForm from '../components/ui/search-form';
import DestinationCard from '../components/ui/destination-card';
import TestimonialCard from '../components/ui/testimonial-card';
import FeatureCard from '../components/ui/feature-card';
import SubscriptionUpgrade from '../components/revenue/SubscriptionUpgrade';
import { useAuth } from '../contexts/auth-context';

export default function DashboardPage() {
  const { user } = useAuth();
  const [searchData, setSearchData] = useState({
    destination: '',
    checkIn: '',
    checkOut: '',
    guests: 1
  });

  const featuredDestinations = [
    {
      id: 1,
      name: 'Paris',
      country: 'France',
      image: 'https://images.unsplash.com/photo-1502602898657-3e91760cbb34?q=80&w=1600&auto=format&fit=crop',
      price: '€89',
      originalPrice: '€120',
      rating: 4.8,
      reviews: 2847,
      hotels: 1247,
      discount: 26,
      description: 'The City of Light awaits with its romantic charm and world-class attractions.'
    },
    {
      id: 2,
      name: 'Tokyo',
      country: 'Japan',
      image: 'https://images.unsplash.com/photo-1549692520-acc6669e2f0c?q=80&w=1600&auto=format&fit=crop',
      price: '¥12,500',
      originalPrice: '¥15,000',
      rating: 4.9,
      reviews: 1923,
      hotels: 892,
      discount: 17,
      description: 'Experience the perfect blend of traditional culture and modern innovation.'
    },
    {
      id: 3,
      name: 'New York',
      country: 'USA',
      image: 'https://images.unsplash.com/photo-1468436139062-f60a71c5c892?q=80&w=1600&auto=format&fit=crop',
      price: '$156',
      originalPrice: '$200',
      rating: 4.7,
      reviews: 4521,
      hotels: 2156,
      discount: 22,
      description: 'The city that never sleeps offers endless entertainment and iconic landmarks.'
    },
    {
      id: 4,
      name: 'London',
      country: 'UK',
      image: 'https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?q=80&w=1600&auto=format&fit=crop',
      price: '£98',
      originalPrice: '£130',
      rating: 4.6,
      reviews: 3245,
      hotels: 1834,
      discount: 25,
      description: 'Rich history meets modern sophistication in this vibrant capital city.'
    },
    {
      id: 5,
      name: 'Dubai',
      country: 'UAE',
      image: 'https://images.unsplash.com/photo-1512453979798-5e66bb9276e4?q=80&w=1600&auto=format&fit=crop',
      price: 'AED 450',
      originalPrice: 'AED 600',
      rating: 4.8,
      reviews: 1876,
      hotels: 567,
      discount: 25,
      description: 'Luxury and innovation combine in this futuristic desert metropolis.'
    },
    {
      id: 6,
      name: 'Barcelona',
      country: 'Spain',
      image: 'https://images.unsplash.com/photo-1539037116277-4db20889f2d4?q=80&w=1600&auto=format&fit=crop',
      price: '€75',
      originalPrice: '€95',
      rating: 4.5,
      reviews: 2134,
      hotels: 789,
      discount: 21,
      description: 'Art, architecture, and Mediterranean charm in one beautiful city.'
    }
  ];

  const testimonials = [
    {
      id: 1,
      name: 'Sarah Johnson',
      location: 'New York',
      rating: 5,
      text: 'Found the perfect hotel in minutes! The search filters are amazing and saved me so much time.',
      avatar: '/images/avatar1.jpg'
    },
    {
      id: 2,
      name: 'Michael Chen',
      location: 'San Francisco',
      rating: 5,
      text: 'Best hotel booking platform I\'ve used. Great prices and excellent customer service.',
      avatar: '/images/avatar2.jpg'
    },
    {
      id: 3,
      name: 'Emma Wilson',
      location: 'London',
      rating: 5,
      text: 'Love how easy it is to compare prices across different hotels. Highly recommended!',
      avatar: '/images/avatar3.jpg'
    }
  ];

  const features = [
    {
      icon: <Shield className="w-8 h-8" />,
      title: 'Secure Booking',
      description: 'Your data and payments are protected with bank-level security',
      color: 'blue'
    },
    {
      icon: <Clock className="w-8 h-8" />,
      title: '24/7 Support',
      description: 'Round-the-clock customer support to help with your bookings',
      color: 'green'
    },
    {
      icon: <Award className="w-8 h-8" />,
      title: 'Best Price Guarantee',
      description: 'We guarantee the best prices or we\'ll match the difference',
      color: 'purple'
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <Navigation />

      {/* Welcome Banner for Logged-in Users */}
      <div className="bg-gradient-to-r from-blue-600 via-teal-600 to-cyan-600 text-white py-5 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-center">
            <div className="flex items-center space-x-3">
              <UserIcon className="w-7 h-7" />
              <div>
                <h2 className="text-xl font-bold">
                  Welcome back, {user?.first_name || user?.email?.split('@')[0]}!
                </h2>
                <p className="text-blue-50 text-sm font-light">Ready to plan your next adventure?</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Hero Section */}
      <HeroSection onSearch={() => document.getElementById('search')?.scrollIntoView({ behavior: 'smooth' })} />

      {/* Search Section */}
      <section id="search" className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-5xl mx-auto">
            <SearchForm />
          </div>
        </div>
      </section>

      {/* Subscription Section */}
      {user && (
        <section className="py-16 bg-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <SubscriptionUpgrade user={user} />
          </div>
        </section>
      )}

      {/* Features Section */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-teal-600 bg-clip-text text-transparent mb-4">Why Choose AeroWay?</h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto font-light">
              We make travel booking simple, secure, and affordable
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <FeatureCard key={index} feature={feature} index={index} />
            ))}
          </div>
        </div>
      </section>

      {/* Featured Destinations */}
      <section id="destinations" className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-teal-600 bg-clip-text text-transparent mb-4">Popular Destinations</h2>
            <p className="text-xl text-gray-600 font-light">Discover amazing places to stay around the world</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {featuredDestinations.map((destination) => (
              <DestinationCard 
                key={destination.id} 
                destination={destination}
                onFavorite={(id) => console.log('Favorite destination:', id)}
              />
            ))}
          </div>
          
          {/* View All Button */}
          <div className="text-center mt-8">
            <button className="inline-flex items-center bg-gradient-to-r from-blue-600 to-teal-600 text-white px-8 py-4 rounded-xl hover:from-blue-700 hover:to-teal-700 transition-all font-bold shadow-lg hover:shadow-xl">
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
            <h2 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-teal-600 bg-clip-text text-transparent mb-4">What Our Users Say</h2>
            <p className="text-xl text-gray-600 font-light">Real reviews from satisfied customers</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {testimonials.map((testimonial) => (
              <TestimonialCard key={testimonial.id} testimonial={testimonial} />
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-br from-blue-600 via-teal-600 to-cyan-700 relative overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-10 left-10 w-32 h-32 bg-white rounded-full blur-2xl"></div>
          <div className="absolute bottom-10 right-10 w-40 h-40 bg-white rounded-full blur-2xl"></div>
        </div>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
          <h2 className="text-4xl font-bold text-white mb-4">Ready to Start Your Journey?</h2>
          <p className="text-xl text-blue-50 mb-10 max-w-2xl mx-auto font-light">
            Join millions of travelers who trust AeroWay for their flight and hotel bookings
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button 
              onClick={() => document.getElementById('search')?.scrollIntoView({ behavior: 'smooth' })}
              className="border-2 border-white text-white px-10 py-4 rounded-xl font-bold hover:bg-white hover:text-blue-600 transition-all backdrop-blur-sm bg-white/20 shadow-lg"
            >
              Start Searching
            </button>
            <button className="border-2 border-white text-white px-10 py-4 rounded-xl font-bold hover:bg-white hover:text-blue-600 transition-all backdrop-blur-sm bg-white/20 shadow-lg">
              View My Bookings
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <Footer />
    </div>
  );
}
