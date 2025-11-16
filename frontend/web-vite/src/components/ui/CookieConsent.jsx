import { useState, useEffect } from 'react';
import { X, Cookie } from 'lucide-react';

export default function CookieConsent() {
  const [showBanner, setShowBanner] = useState(false);

  useEffect(() => {
    // Check if user has already consented
    const consent = localStorage.getItem('cookie_consent');
    if (!consent) {
      // Show banner after a short delay for better UX
      setTimeout(() => setShowBanner(true), 1000);
    }
  }, []);

  const handleAccept = () => {
    localStorage.setItem('cookie_consent', 'accepted');
    localStorage.setItem('cookie_consent_date', new Date().toISOString());
    setShowBanner(false);
  };

  const handleReject = () => {
    localStorage.setItem('cookie_consent', 'rejected');
    localStorage.setItem('cookie_consent_date', new Date().toISOString());
    setShowBanner(false);
  };

  if (!showBanner) {
    return null;
  }

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 shadow-2xl z-50 p-4 md:p-6">
      <div className="max-w-7xl mx-auto relative">
        <div className="flex flex-col md:flex-row items-start md:items-center gap-4 pr-8">
          <div className="flex items-start gap-3 flex-1 min-w-0">
            <Cookie className="w-6 h-6 text-blue-600 mt-1 flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <h3 className="text-lg font-semibold text-gray-900 mb-1">
                We use cookies
              </h3>
              <p className="text-sm text-gray-600">
                We use cookies to enhance your browsing experience, analyze site traffic, and personalize content. 
                By clicking "Accept All", you consent to our use of cookies. 
                <a 
                  href="/privacy-policy" 
                  className="text-blue-600 hover:text-blue-700 underline ml-1"
                >
                  Learn more
                </a>
              </p>
            </div>
          </div>
          <div className="flex gap-3 flex-shrink-0 w-full md:w-auto">
            <button
              onClick={handleReject}
              className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors text-sm font-medium whitespace-nowrap"
            >
              Reject
            </button>
            <button
              onClick={handleAccept}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium whitespace-nowrap"
            >
              Accept All
            </button>
          </div>
        </div>
        <button
          onClick={handleReject}
          className="absolute top-4 right-0 text-gray-400 hover:text-gray-600 transition-colors p-1"
          aria-label="Close"
        >
          <X className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
}

