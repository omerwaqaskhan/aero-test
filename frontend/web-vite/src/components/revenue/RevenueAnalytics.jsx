import { useState, useEffect } from 'react';
import { apiClient } from '../../lib/api-client';

export default function RevenueAnalytics() {
  const [analytics, setAnalytics] = useState(null);
  const [monthlyData, setMonthlyData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics();
    fetchMonthlyData();
  }, []);

  const fetchAnalytics = async () => {
    try {
      const response = await apiClient.get('/v1/revenue/analytics');
      setAnalytics(response.data);
    } catch (err) {
      console.error('Error fetching analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchMonthlyData = async () => {
    try {
      const response = await apiClient.get('/v1/revenue/analytics/monthly?months=12');
      setMonthlyData(response.data);
    } catch (err) {
      console.error('Error fetching monthly data:', err);
    }
  };

  if (loading) {
    return <div className="text-center py-8">Loading analytics...</div>;
  }

  if (!analytics) {
    return <div className="text-center py-8 text-gray-500">No analytics data available</div>;
  }

  const revenueTypes = [
    { name: 'Subscriptions', key: 'subscription', color: 'blue' },
    { name: 'Leads', key: 'lead', color: 'green' },
    { name: 'Listings', key: 'listing', color: 'purple' },
    { name: 'Sponsorships', key: 'sponsorship', color: 'orange' },
    { name: 'Ads', key: 'ads', color: 'yellow' }
  ];

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Revenue Analytics</h2>

      {/* Total Revenue */}
      <div className="mb-8">
        <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg p-6 text-white">
          <p className="text-blue-100 text-sm mb-2">Total Revenue</p>
          <p className="text-4xl font-bold">${analytics.total_revenue.toFixed(2)}</p>
        </div>
      </div>

      {/* Revenue by Type */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Revenue by Type</h3>
        <div className="space-y-3">
          {revenueTypes.map((type) => {
            const amount = analytics.by_type[type.key] || 0;
            const percentage = analytics.total_revenue > 0 
              ? (amount / analytics.total_revenue * 100).toFixed(1) 
              : 0;

            return (
              <div key={type.key} className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className={`w-4 h-4 bg-${type.color}-500 rounded mr-3`}></div>
                  <span className="text-gray-700">{type.name}</span>
                </div>
                <div className="text-right">
                  <span className="font-semibold text-gray-900">${amount.toFixed(2)}</span>
                  <span className="text-gray-500 text-sm ml-2">({percentage}%)</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Monthly Revenue Chart */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Monthly Revenue (Last 12 Months)</h3>
        <div className="space-y-2">
          {monthlyData.map((month) => (
            <div key={month.month} className="flex items-center justify-between p-3 bg-gray-50 rounded">
              <span className="text-gray-700 font-medium">{month.month}</span>
              <span className="font-bold text-gray-900">${month.total.toFixed(2)}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

