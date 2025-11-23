import { useState } from 'react';
import { Calendar, DollarSign, Bell } from 'lucide-react';
import { apiClient } from '../../lib/api-client';

export default function PriceAlertForm({ hotel, onSuccess, onClose }) {
  const [formData, setFormData] = useState({
    target_price: '',
    currency: 'USD',
    check_in: '',
    check_out: '',
    guests: 1,
    rooms: 1,
    notify_email: true,
    notify_sms: false,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!formData.target_price || parseFloat(formData.target_price) <= 0) {
      setError('Please enter a valid target price');
      return;
    }

    setLoading(true);
    try {
      await apiClient.post('/v1/user/price-alerts', {
        hotel_id: hotel.id,
        target_price: parseFloat(formData.target_price),
        currency: formData.currency,
        check_in: formData.check_in || null,
        check_out: formData.check_out || null,
        guests: formData.guests,
        rooms: formData.rooms,
        notify_email: formData.notify_email,
        notify_sms: formData.notify_sms,
      });

      if (onSuccess) onSuccess();
      if (onClose) onClose();
    } catch (err) {
      console.error('Error creating price alert:', err);
      setError(err.response?.data?.detail || 'Failed to create price alert');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded text-sm">
          {error}
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Target Price <span className="text-red-500">*</span>
        </label>
        <div className="relative">
          <DollarSign className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="number"
            step="0.01"
            min="0"
            required
            value={formData.target_price}
            onChange={(e) => setFormData({ ...formData, target_price: e.target.value })}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Enter target price"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            <Calendar className="w-4 h-4 inline mr-1" />
            Check-in (Optional)
          </label>
          <input
            type="date"
            value={formData.check_in}
            onChange={(e) => setFormData({ ...formData, check_in: e.target.value })}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            <Calendar className="w-4 h-4 inline mr-1" />
            Check-out (Optional)
          </label>
          <input
            type="date"
            value={formData.check_out}
            onChange={(e) => setFormData({ ...formData, check_out: e.target.value })}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Guests</label>
          <input
            type="number"
            min="1"
            max="10"
            value={formData.guests}
            onChange={(e) => setFormData({ ...formData, guests: parseInt(e.target.value) || 1 })}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Rooms</label>
          <input
            type="number"
            min="1"
            max="5"
            value={formData.rooms}
            onChange={(e) => setFormData({ ...formData, rooms: parseInt(e.target.value) || 1 })}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          <Bell className="w-4 h-4 inline mr-1" />
          Notifications
        </label>
        <div className="space-y-2">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={formData.notify_email}
              onChange={(e) => setFormData({ ...formData, notify_email: e.target.checked })}
              className="mr-2"
            />
            <span className="text-sm text-gray-700">Email notifications</span>
          </label>
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={formData.notify_sms}
              onChange={(e) => setFormData({ ...formData, notify_sms: e.target.checked })}
              className="mr-2"
            />
            <span className="text-sm text-gray-700">SMS notifications</span>
          </label>
        </div>
      </div>

      <div className="flex gap-3 pt-4">
        <button
          type="submit"
          disabled={loading}
          className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
        >
          {loading ? 'Creating...' : 'Create Alert'}
        </button>
        {onClose && (
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
          >
            Cancel
          </button>
        )}
      </div>
    </form>
  );
}

