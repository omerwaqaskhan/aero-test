import { useState, useEffect } from 'react';
import Navigation from '../components/layout/navigation';
import Footer from '../components/layout/footer';
import RevenueAnalytics from '../components/revenue/RevenueAnalytics';
import { apiClient } from '../lib/api-client';
import { useAuth } from '../contexts/auth-context';

export default function AdminDashboardPage() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Check if user is admin
    if (!user) {
      setError('Please log in to access admin dashboard');
      setLoading(false);
      return;
    }

    // Check if user has admin role
    const userRole = user.role || user.user_role;
    if (userRole !== 'super_admin' && userRole !== 'tenant_admin') {
      setError('Access denied. Admin privileges required.');
      setLoading(false);
      return;
    }

    setLoading(false);
  }, [user]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <div className="container mx-auto px-4 py-16">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Loading...</p>
          </div>
        </div>
        <Footer />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <div className="container mx-auto px-4 py-16">
          <div className="max-w-2xl mx-auto bg-white rounded-lg shadow-lg p-8 text-center">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Access Denied</h2>
            <p className="text-gray-600">{error}</p>
          </div>
        </div>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      
      <div className="container mx-auto px-4 py-16">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Admin Dashboard</h1>
          <p className="text-gray-600">Revenue analytics and system overview</p>
        </div>

        <RevenueAnalytics />
      </div>

      <Footer />
    </div>
  );
}

