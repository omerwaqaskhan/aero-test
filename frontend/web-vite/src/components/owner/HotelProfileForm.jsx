import { useState, useEffect } from 'react';
import { Upload, X, Save, Building2, MapPin, Phone, Mail, Globe } from 'lucide-react';
import { apiClient } from '../../lib/api-client';
import { useToast } from '../../hooks/use-toast-context';

export default function HotelProfileForm({ listing, hotel, onUpdate }) {
  const { success, error: showError } = useToast();
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [formData, setFormData] = useState({
    owner_name: listing?.owner_name || '',
    owner_email: listing?.owner_email || '',
    owner_phone: listing?.owner_phone || '',
    website: listing?.website || '',
    description: hotel?.description || '',
    amenities: hotel?.amenities || [],
  });
  const [previewImages, setPreviewImages] = useState([]);
  const [newImages, setNewImages] = useState([]);

  useEffect(() => {
    if (hotel?.images) {
      setPreviewImages(hotel.images);
    }
  }, [hotel]);

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleImageUpload = async (e) => {
    const files = Array.from(e.target.files);
    if (files.length === 0) return;

    setUploading(true);
    try {
      // In a real app, upload to cloud storage (S3, Cloudinary, etc.)
      // For now, we'll just create preview URLs
      const imageUrls = files.map(file => URL.createObjectURL(file));
      setPreviewImages(prev => [...prev, ...imageUrls]);
      setNewImages(prev => [...prev, ...files]);
      success('Success', `${files.length} image(s) selected`);
    } catch (err) {
      showError('Error', 'Failed to upload images');
    } finally {
      setUploading(false);
    }
  };

  const removeImage = (index) => {
    setPreviewImages(prev => prev.filter((_, i) => i !== index));
    setNewImages(prev => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Upload new images first (in real app)
      // Then update listing and hotel
      
      // Update listing
      await apiClient.patch(`/v1/revenue/listings/${listing.id}`, {
        owner_name: formData.owner_name,
        owner_phone: formData.owner_phone,
        website: formData.website,
      });

      // Update hotel (if endpoint exists)
      // await apiClient.patch(`/v1/search-booking/hotels/${hotel.id}`, {
      //   description: formData.description,
      //   amenities: formData.amenities,
      //   images: previewImages,
      // });

      success('Success', 'Profile updated successfully');
      if (onUpdate) onUpdate();
    } catch (err) {
      console.error('Error updating profile:', err);
      showError('Error', 'Failed to update profile. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Owner Information */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Building2 className="w-5 h-5" />
          Owner Information
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Owner Name
            </label>
            <input
              type="text"
              value={formData.owner_name}
              onChange={(e) => handleInputChange('owner_name', e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Your name"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              <Mail className="w-4 h-4 inline mr-1" />
              Email
            </label>
            <input
              type="email"
              value={formData.owner_email}
              disabled
              className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              <Phone className="w-4 h-4 inline mr-1" />
              Phone
            </label>
            <input
              type="tel"
              value={formData.owner_phone}
              onChange={(e) => handleInputChange('owner_phone', e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="+1 (555) 123-4567"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              <Globe className="w-4 h-4 inline mr-1" />
              Website
            </label>
            <input
              type="url"
              value={formData.website}
              onChange={(e) => handleInputChange('website', e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="https://yourhotel.com"
            />
          </div>
        </div>
      </div>

      {/* Hotel Images */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Hotel Images</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          {previewImages.map((img, index) => (
            <div key={index} className="relative group">
              <img
                src={img}
                alt={`Hotel ${index + 1}`}
                className="w-full h-32 object-cover rounded-lg"
              />
              <button
                type="button"
                onClick={() => removeImage(index)}
                className="absolute top-2 right-2 p-1 bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
        <label className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg cursor-pointer hover:bg-blue-700 transition-colors">
          <Upload className="w-4 h-4 mr-2" />
          {uploading ? 'Uploading...' : 'Upload Images'}
          <input
            type="file"
            multiple
            accept="image/*"
            onChange={handleImageUpload}
            className="hidden"
            disabled={uploading}
          />
        </label>
      </div>

      {/* Hotel Description */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Hotel Description</h3>
        <textarea
          value={formData.description}
          onChange={(e) => handleInputChange('description', e.target.value)}
          rows={6}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          placeholder="Describe your hotel..."
        />
      </div>

      {/* Submit Button */}
      <div className="flex justify-end">
        <button
          type="submit"
          disabled={loading}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2"
        >
          <Save className="w-4 h-4" />
          {loading ? 'Saving...' : 'Save Changes'}
        </button>
      </div>
    </form>
  );
}

