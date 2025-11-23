import { useState, useEffect } from 'react';
import { Heart } from 'lucide-react';
import { apiClient } from '../../lib/api-client';
import { useAuth } from '../../contexts/auth-context';

export default function FavoriteButton({ hotelId }) {
  const { user } = useAuth();
  const [isFavorite, setIsFavorite] = useState(false);
  const [loading, setLoading] = useState(false);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    if (user && hotelId) {
      checkFavorite();
    } else {
      setChecking(false);
    }
  }, [user, hotelId]);

  const checkFavorite = async () => {
    if (!user || !hotelId) return;
    
    try {
      const response = await apiClient.get(`/v1/user/favorites/${hotelId}/check`);
      setIsFavorite(response.data.is_favorite);
    } catch (err) {
      console.error('Error checking favorite:', err);
    } finally {
      setChecking(false);
    }
  };

  const toggleFavorite = async () => {
    if (!user) {
      // Redirect to login
      window.location.href = '/login?redirect=' + encodeURIComponent(window.location.pathname);
      return;
    }

    if (loading) return;
    setLoading(true);

    try {
      if (isFavorite) {
        await apiClient.delete(`/v1/user/favorites/${hotelId}`);
        setIsFavorite(false);
      } else {
        await apiClient.post('/v1/user/favorites', { hotel_id: hotelId });
        setIsFavorite(true);
      }
    } catch (err) {
      console.error('Error toggling favorite:', err);
      alert('Failed to update favorite. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (checking) {
    return (
      <button
        className="p-2 rounded-full bg-white/90 hover:bg-white transition-all"
        disabled
      >
        <Heart className="w-5 h-5 text-gray-400" />
      </button>
    );
  }

  return (
    <button
      onClick={toggleFavorite}
      disabled={loading}
      className={`p-2 rounded-full transition-all ${
        isFavorite
          ? 'bg-red-500 hover:bg-red-600 text-white'
          : 'bg-white/90 hover:bg-white text-gray-700'
      }`}
      title={isFavorite ? 'Remove from favorites' : 'Add to favorites'}
    >
      <Heart
        className={`w-5 h-5 ${isFavorite ? 'fill-current' : ''}`}
      />
    </button>
  );
}

