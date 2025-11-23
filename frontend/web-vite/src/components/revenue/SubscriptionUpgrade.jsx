import { useState, useEffect } from 'react';
import { apiClient } from '../../lib/api-client';
import stripePromise from '../../lib/stripe';

export default function SubscriptionUpgrade({ user }) {
  const [subscription, setSubscription] = useState(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    if (user?.id) {
      fetchSubscription();
    }
  }, [user]);

  const fetchSubscription = async () => {
    try {
      const response = await apiClient.get(`/v1/revenue/subscriptions/${user.id}`);
      setSubscription(response.data);
    } catch (err) {
      console.error('Error fetching subscription:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpgrade = async (tier) => {
    if (!user?.id || !user?.email) {
      alert('Please log in to upgrade your subscription');
      return;
    }

    setProcessing(true);
    try {
      // Create checkout session
      const successUrl = `${window.location.origin}/dashboard?subscription=success`;
      const cancelUrl = `${window.location.origin}/dashboard?subscription=cancelled`;
      
      const response = await apiClient.post('/v1/revenue/checkout/create-session', null, {
        params: {
          tier: tier,
          user_id: user.id,
          user_email: user.email,
          success_url: successUrl,
          cancel_url: cancelUrl
        }
      });

      const { url } = response.data;
      
      // Redirect to Stripe Checkout
      if (url) {
        window.location.href = url;
      } else {
        throw new Error('No checkout URL received');
      }
    } catch (err) {
      console.error('Error creating checkout session:', err);
      alert('Failed to start checkout. Please try again.');
      setProcessing(false);
    }
  };

  if (loading) {
    return <div className="text-center py-4">Loading...</div>;
  }

  const currentTier = subscription?.tier || 'free';

  const plans = [
    {
      tier: 'free',
      name: 'Free',
      price: '$0',
      features: [
        'Basic hotel search',
        'Compare hotels',
        'View reviews'
      ]
    },
    {
      tier: 'premium',
      name: 'Premium',
      price: '$9.99/month',
      features: [
        'All free features',
        'Price alerts',
        'Unlimited saved searches',
        'AI trip planning',
        'Ad-free experience'
      ]
    },
    {
      tier: 'pro',
      name: 'Pro',
      price: '$19.99/month',
      features: [
        'All premium features',
        'Concierge support',
        'Group booking tools',
        'Priority customer service',
        'API access'
      ]
    }
  ];

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Subscription Plans</h2>
      
      <div className="grid md:grid-cols-3 gap-6">
        {plans.map((plan) => {
          const isCurrent = currentTier === plan.tier;
          const isUpgrade = getTierValue(plan.tier) > getTierValue(currentTier);
          
          return (
            <div
              key={plan.tier}
              className={`border-2 rounded-lg p-6 ${
                isCurrent ? 'border-blue-600 bg-blue-50' : 'border-gray-200'
              }`}
            >
              <div className="text-center mb-4">
                <h3 className="text-xl font-bold text-gray-900">{plan.name}</h3>
                <div className="text-3xl font-bold text-blue-600 mt-2">{plan.price}</div>
                {isCurrent && (
                  <span className="inline-block mt-2 px-3 py-1 bg-blue-600 text-white text-sm rounded-full">
                    Current Plan
                  </span>
                )}
              </div>

              <ul className="space-y-2 mb-6">
                {plan.features.map((feature, idx) => (
                  <li key={idx} className="flex items-start">
                    <svg className="w-5 h-5 text-green-500 mr-2 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span className="text-gray-700">{feature}</span>
                  </li>
                ))}
              </ul>

              {isCurrent ? (
                <button
                  disabled
                  className="w-full px-4 py-2 bg-gray-300 text-gray-600 rounded-lg cursor-not-allowed"
                >
                  Current Plan
                </button>
              ) : isUpgrade ? (
                <button
                  onClick={() => handleUpgrade(plan.tier)}
                  disabled={processing}
                  className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {processing ? 'Processing...' : 'Upgrade'}
                </button>
              ) : (
                <button
                  onClick={() => handleUpgrade(plan.tier)}
                  disabled={processing}
                  className="w-full px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {processing ? 'Processing...' : 'Downgrade'}
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function getTierValue(tier) {
  const values = { free: 0, premium: 1, pro: 2 };
  return values[tier] || 0;
}

