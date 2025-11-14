import { useEffect } from 'react';
import { apiClient } from '../../lib/api-client';

export default function AdSlot({ adSlot, pageType }) {
  useEffect(() => {
    // Record ad impression
    const recordImpression = async () => {
      try {
        // In production, this would get actual revenue from AdSense
        const estimatedRevenue = 0.01; // $0.01 per impression (example)
        
        await apiClient.post('/v1/revenue/ads/impression', {
          ad_slot: adSlot,
          page_type: pageType,
          revenue: estimatedRevenue
        });
      } catch (err) {
        console.error('Error recording ad impression:', err);
      }
    };

    recordImpression();
  }, [adSlot, pageType]);

  const handleAdClick = async () => {
    try {
      // In production, this would get actual revenue from AdSense
      const estimatedRevenue = 0.10; // $0.10 per click (example)
      
      await apiClient.post('/v1/revenue/ads/click', {
        ad_slot: adSlot,
        page_type: pageType,
        revenue: estimatedRevenue
      });
    } catch (err) {
      console.error('Error recording ad click:', err);
    }
  };

  return (
    <div 
      className="ad-slot bg-gray-100 border-2 border-dashed border-gray-300 rounded-lg p-4 text-center min-h-[200px] max-h-[400px] flex items-center justify-center w-full"
      onClick={handleAdClick}
    >
      <div className="w-full">
        <p className="text-gray-500 text-sm mb-2 font-medium">Advertisement</p>
        <p className="text-gray-400 text-xs mb-1">
          {adSlot}
        </p>
        <p className="text-gray-300 text-xs">
          (AdSense placeholder)
        </p>
      </div>
    </div>
  );
}

