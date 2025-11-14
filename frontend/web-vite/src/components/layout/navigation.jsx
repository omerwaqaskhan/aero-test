import React, { useEffect, useState } from 'react';
import { Menu, X, Search, User, LogOut, Plane } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/auth-context';

const Navigation = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);
  const navigate = useNavigate();
  const { user, logout, isAuthenticated } = useAuth();

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  const handleLogout = async () => {
    await logout();
  };

  useEffect(() => {
    const onScroll = () => setIsScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <nav className={`${isScrolled ? 'bg-white shadow-sm' : 'bg-white/60 backdrop-blur supports-[backdrop-filter]:bg-white/60'} sticky top-0 z-50 transition-colors`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex items-center">
            <a href="/" className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-teal-600 bg-clip-text text-transparent hover:from-blue-700 hover:to-teal-700 transition-all">
              LuftWay
            </a>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:block">
            <div className="ml-10 flex items-baseline space-x-8">
              <a 
                href="/" 
                className="text-gray-700 hover:text-blue-600 px-3 py-2 text-sm font-medium transition-colors"
              >
                Home
              </a>
              <a 
                href="/hotels"
                onClick={(e) => {
                  e.preventDefault();
                  navigate('/hotels');
                }}
                className="text-gray-700 hover:text-blue-600 px-3 py-2 text-sm font-medium transition-colors"
              >
                Hotels
              </a>
              <a 
                href="#news" 
                className="text-gray-700 hover:text-blue-600 px-3 py-2 text-sm font-medium transition-colors"
              >
                News
              </a>
              <a 
                href="#contacts" 
                className="text-gray-700 hover:text-blue-600 px-3 py-2 text-sm font-medium transition-colors"
              >
                Contacts
              </a>
            </div>
          </div>

          {/* Desktop Auth Buttons */}
          <div className="hidden md:flex items-center space-x-4">
            {isAuthenticated ? (
              <>
                <a
                  href="/favorites"
                  onClick={(e) => {
                    e.preventDefault();
                    navigate('/favorites');
                  }}
                  className="text-gray-700 hover:text-blue-600 px-3 py-2 text-sm font-medium transition-colors"
                >
                  Favorites
                </a>
                <a
                  href="/bookings"
                  onClick={(e) => {
                    e.preventDefault();
                    navigate('/bookings');
                  }}
                  className="text-gray-700 hover:text-blue-600 px-3 py-2 text-sm font-medium transition-colors"
                >
                  Bookings
                </a>
                <a
                  href="/saved-searches"
                  onClick={(e) => {
                    e.preventDefault();
                    navigate('/saved-searches');
                  }}
                  className="text-gray-700 hover:text-blue-600 px-3 py-2 text-sm font-medium transition-colors"
                >
                  Saved Searches
                </a>
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-gray-800 rounded-full flex items-center justify-center text-white font-semibold text-sm">
                    {user?.first_name?.charAt(0) || user?.email?.charAt(0).toUpperCase()}
                  </div>
                  <span className="text-gray-700 text-sm font-medium">
                    {user?.first_name || user?.email?.split('@')[0]}
                  </span>
                </div>
                {(user?.role === 'super_admin' || user?.role === 'tenant_admin' || user?.user_role === 'super_admin' || user?.user_role === 'tenant_admin') && (
                  <>
                    <a
                      href="/admin"
                      onClick={(e) => {
                        e.preventDefault();
                        navigate('/admin');
                      }}
                      className="text-gray-700 hover:text-blue-600 px-3 py-2 text-sm font-medium transition-colors"
                    >
                      Admin
                    </a>
                    <a
                      href="/monitoring"
                      onClick={(e) => {
                        e.preventDefault();
                        navigate('/monitoring');
                      }}
                      className="text-gray-700 hover:text-blue-600 px-3 py-2 text-sm font-medium transition-colors"
                    >
                      Monitoring
                    </a>
                  </>
                )}
                <button 
                  onClick={handleLogout}
                  className="flex items-center space-x-2 text-gray-700 hover:text-blue-600 px-4 py-2 text-sm font-medium transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Logout</span>
                </button>
              </>
            ) : (
              <button
              onClick={() => navigate('/login')}
              className="bg-gray-800 hover:bg-gray-900 text-white px-6 py-2 rounded-lg text-sm font-semibold transition-colors flex items-center gap-2"
            >
              <User className="w-4 h-4" />
              Sign In
            </button>
            )}
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <button
              onClick={toggleMenu}
              className="inline-flex items-center justify-center p-2 rounded-lg text-gray-700 hover:text-blue-600 hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500 transition-colors"
              aria-expanded="false"
            >
              <span className="sr-only">Open main menu</span>
              {isMenuOpen ? (
                <X className="block h-6 w-6" aria-hidden="true" />
              ) : (
                <Menu className="block h-6 w-6" aria-hidden="true" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      {isMenuOpen && (
        <div className="md:hidden">
          <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3 bg-white border-t">
            <a
              href="/"
              className="text-gray-700 hover:text-blue-600 block px-3 py-2 text-base font-medium transition-colors"
              onClick={() => setIsMenuOpen(false)}
            >
              Home
            </a>
            <a
              href="/hotels"
              onClick={(e) => {
                e.preventDefault();
                navigate('/hotels');
                setIsMenuOpen(false);
              }}
              className="text-gray-700 hover:text-blue-600 block px-3 py-2 text-base font-medium transition-colors"
            >
              Hotels
            </a>
            <a
              href="#news"
              className="text-gray-700 hover:text-blue-600 block px-3 py-2 text-base font-medium transition-colors"
              onClick={() => setIsMenuOpen(false)}
            >
              News
            </a>
            <a
              href="#contacts"
              className="text-gray-700 hover:text-blue-600 block px-3 py-2 text-base font-medium transition-colors"
              onClick={() => setIsMenuOpen(false)}
            >
              Contacts
            </a>
            <div className="border-t border-gray-200 pt-4 mt-4">
              {isAuthenticated ? (
                <>
                  <div className="flex items-center space-x-3 px-3 py-2 mb-3">
                    <div className="w-8 h-8 bg-gray-800 rounded-full flex items-center justify-center text-white font-semibold text-sm">
                      {user?.first_name?.charAt(0) || user?.email?.charAt(0).toUpperCase()}
                    </div>
                    <span className="text-gray-700 text-sm font-medium">
                      {user?.first_name || user?.email?.split('@')[0]}
                    </span>
                  </div>
                  <button
                    onClick={() => {
                      handleLogout();
                      setIsMenuOpen(false);
                    }}
                    className="flex items-center space-x-2 text-gray-700 hover:text-blue-600 block px-3 py-2 text-base font-medium transition-colors w-full"
                  >
                    <LogOut className="w-4 h-4" />
                    <span>Logout</span>
                  </button>
                </>
              ) : (
                <>
                  <button
                    onClick={() => {
                      navigate('/login');
                      setIsMenuOpen(false);
                    }}
                    className="bg-gray-800 hover:bg-gray-900 text-white block w-full px-6 py-2 rounded-lg text-base font-semibold transition-colors mt-2 flex items-center justify-center gap-2"
                  >
                    <User className="w-4 h-4" />
                    Sign In
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navigation;
