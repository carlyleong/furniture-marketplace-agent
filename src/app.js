import React, { useState, useRef, useEffect } from 'react';
import { Upload, Download, Plus, Trash2, Camera, FileText, CheckCircle, AlertCircle, Wand2, Loader } from 'lucide-react';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const FurnitureMarketplaceAgent = () => {
  const [listings, setListings] = useState([]);
  const [currentListing, setCurrentListing] = useState({
    title: '',
    price: '',
    condition: 'Used - Good',
    description: '',
    category: 'Home & Garden//Furniture//Living Room Furniture',
    images: [],
    auto_enhance_description: false
  });
  const [dragActive, setDragActive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [categories, setCategories] = useState([]);
  const fileInputRef = useRef(null);

  const conditions = ['New', 'Used - Like New', 'Used - Good', 'Used - Fair'];

  // Load categories and listings on component mount
  useEffect(() => {
    loadCategories();
    loadListings();
  }, []);

  const loadCategories = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/categories`);
      const data = await response.json();
      setCategories(data.categories);
    } catch (error) {
      console.error('Error loading categories:', error);
    }
  };

  const loadListings = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/listings`);
      const data = await response.json();
      setListings(data);
    } catch (error) {
      console.error('Error loading listings:', error);
    }
  };

  const handleImageUpload = async (files) => {
    if (files.length === 0) return;
    
    setUploading(true);
    const formData = new FormData();
    
    Array.from(files).forEach(file => {
      formData.append('files', file);
    });
    
    try {
      const response = await fetch(`${API_BASE}/api/upload-images`, {
        method: 'POST',
        body: formData,
      });
      
      if (response.ok) {
        const data = await response.json();
        setCurrentListing(prev => ({
          ...prev,
          images: [...prev.images, ...data.images]
        }));
        
        // If this is the first image, try to auto-analyze
        if (currentListing.images.length === 0 && data.images.length > 0) {
          await autoAnalyzeImage(files[0]);
        }
      } else {
        alert('Error uploading images');
      }
    } catch (error) {
      console.error('Upload error:', error);
      alert('Error uploading images');
    } finally {
      setUploading(false);
    }
  };

  const autoAnalyzeImage = async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await fetch(`${API_BASE}/api/analyze-image`, {
        method: 'POST',
        body: formData,
      });
      
      if (response.ok) {
        const data = await response.json();
        
        // Apply suggestions if available
        if (data.suggestions) {
          setCurrentListing(prev => ({
            ...prev,
            title: data.suggestions.suggested_title || prev.title,
            category: data.suggestions.suggested_category || prev.category
          }));
        }
      }
    } catch (error) {
      console.error('Analysis error:', error);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragActive(false);
    const files = Array.from(e.dataTransfer.files).filter(file => file.type.startsWith('image/'));
    if (files.length > 0) {
      handleImageUpload(files);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragActive(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setDragActive(false);
  };

  const removeImage = (imageId) => {
    setCurrentListing(prev => ({
      ...prev,
      images: prev.images.filter(img => img.id !== imageId)
    }));
  };

  const enhanceDescription = async () => {
    if (!currentListing.title) {
      alert('Please enter a title first');
      return;
    }
    
    setLoading(true);
    const formData = new FormData();
    formData.append('title', currentListing.title);
    formData.append('condition', currentListing.condition);
    formData.append('category', currentListing.category);
    formData.append('current_description', currentListing.description);
    
    try {
      const response = await fetch(`${API_BASE}/api/enhance-description`, {
        method: 'POST',
        body: formData,
      });
      
      if (response.ok) {
        const data = await response.json();
        setCurrentListing(prev => ({
          ...prev,
          description: data.enhanced_description
        }));
      } else {
        alert('Error enhancing description');
      }
    } catch (error) {
      console.error('Enhancement error:', error);
      alert('Error enhancing description');
    } finally {
      setLoading(false);
    }
  };

  const addListing = async () => {
    if (!currentListing.title || !currentListing.price) {
      alert('Please fill in the title and price at minimum');
      return;
    }
    
    setLoading(true);
    
    try {
      const response = await fetch(`${API_BASE}/api/listings`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: currentListing.title,
          price: parseFloat(currentListing.price),
          condition: currentListing.condition,
          description: currentListing.description,
          category: currentListing.category,
          images: currentListing.images,
          auto_enhance_description: currentListing.auto_enhance_description
        }),
      });
      
      if (response.ok) {
        const newListing = await response.json();
        setListings(prev => [...prev, newListing]);
        
        // Reset form
        setCurrentListing({
          title: '',
          price: '',
          condition: 'Used - Good',
          description: '',
          category: 'Home & Garden//Furniture//Living Room Furniture',
          images: [],
          auto_enhance_description: false
        });
      } else {
        alert('Error creating listing');
      }
    } catch (error) {
      console.error('Create listing error:', error);
      alert('Error creating listing');
    } finally {
      setLoading(false);
    }
  };

  const removeListing = async (id) => {
    try {
      const response = await fetch(`${API_BASE}/api/listings/${id}`, {
        method: 'DELETE',
      });
      
      if (response.ok) {
        setListings(prev => prev.filter(listing => listing.id !== id));
      } else {
        alert('Error deleting listing');
      }
    } catch (error) {
      console.error('Delete error:', error);
      alert('Error deleting listing');
    }
  };

  const generateCSV = async () => {
    if (listings.length === 0) {
      alert('Please add at least one listing first');
      return;
    }

    setLoading(true);
    
    try {
      const listingIds = listings.map(listing => listing.id);
      const response = await fetch(`${API_BASE}/api/export-csv`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(listingIds),
      });
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `facebook_marketplace_listings_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      } else {
        alert('Error generating CSV');
      }
    } catch (error) {
      console.error('CSV export error:', error);
      alert('Error generating CSV');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6 bg-gradient-to-br from-blue-50 to-indigo-100 min-h-screen">
      <div className="bg-white rounded-2xl shadow-2xl overflow-hidden">
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-8">
          <h1 className="text-4xl font-bold mb-2 flex items-center gap-3">
            <Camera className="w-10 h-10" />
            Facebook Marketplace Furniture Agent
          </h1>
          <p className="text-blue-100 text-lg">Upload furniture photos and generate marketplace-ready listings with AI assistance</p>
        </div>

        <div className="p-8">
          <div className="grid lg:grid-cols-2 gap-8">
            {/* Left Column - Create Listing */}
            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                <Plus className="w-6 h-6 text-blue-600" />
                Create New Listing
              </h2>

              {/* Image Upload */}
              <div className="space-y-4">
                <label className="block text-sm font-semibold text-gray-700">Furniture Photos</label>
                <div
                  className={`border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200 cursor-pointer ${
                    dragActive 
                      ? 'border-blue-500 bg-blue-50' 
                      : 'border-gray-300 hover:border-blue-400'
                  } ${uploading ? 'opacity-50 pointer-events-none' : ''}`}
                  onDrop={handleDrop}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onClick={() => !uploading && fileInputRef.current?.click()}
                >
                  {uploading ? (
                    <Loader className="w-12 h-12 text-blue-500 mx-auto mb-4 animate-spin" />
                  ) : (
                    <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  )}
                  <p className="text-gray-600 font-medium">
                    {uploading ? 'Processing images...' : 'Click to upload or drag & drop furniture photos'}
                  </p>
                  <p className="text-sm text-gray-500 mt-2">PNG, JPG, WEBP up to 10MB each • AI analysis included</p>
                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    accept="image/*"
                    onChange={(e) => handleImageUpload(e.target.files)}
                    className="hidden"
                    disabled={uploading}
                  />
                </div>

                {currentListing.images.length > 0 && (
                  <div className="grid grid-cols-3 gap-3">
                    {currentListing.images.map((image) => (
                      <div key={image.id} className="relative group">
                        <img
                          src={`${API_BASE}${image.url}`}
                          alt={image.original_name}
                          className="w-full h-24 object-cover rounded-lg shadow-md"
                        />
                        <button
                          onClick={() => removeImage(image.id)}
                          className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                        {image.analysis && (
                          <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-70 text-white text-xs p-1 rounded-b-lg">
                            AI: {image.analysis.estimated_type}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Form Fields */}
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Title *</label>
                  <input
                    type="text"
                    value={currentListing.title}
                    onChange={(e) => setCurrentListing(prev => ({ ...prev, title: e.target.value }))}
                    placeholder="e.g., Vintage Oak Dining Table"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    maxLength={150}
                  />
                  <p className="text-xs text-gray-500 mt-1">{currentListing.title.length}/150 characters</p>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Price ($) *</label>
                  <input
                    type="number"
                    value={currentListing.price}
                    onChange={(e) => setCurrentListing(prev => ({ ...prev, price: e.target.value }))}
                    placeholder="299"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    min="1"
                  />
                </div>
              </div>

              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Condition</label>
                  <select
                    value={currentListing.condition}
                    onChange={(e) => setCurrentListing(prev => ({ ...prev, condition: e.target.value }))}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    {conditions.map(condition => (
                      <option key={condition} value={condition}>{condition}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Category</label>
                  <select
                    value={currentListing.category}
                    onChange={(e) => setCurrentListing(prev => ({ ...prev, category: e.target.value }))}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    {categories.map(category => (
                      <option key={category} value={category}>
                        {category.split('//').pop()}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-sm font-semibold text-gray-700">Description</label>
                  <button
                    onClick={enhanceDescription}
                    disabled={loading || !currentListing.title}
                    className="text-sm text-blue-600 hover:text-blue-800 font-medium flex items-center gap-1 disabled:text-gray-400 disabled:cursor-not-allowed"
                  >
                    {loading ? (
                      <Loader className="w-4 h-4 animate-spin" />
                    ) : (
                      <Wand2 className="w-4 h-4" />
                    )}
                    AI Enhance
                  </button>
                </div>
                <textarea
                  value={currentListing.description}
                  onChange={(e) => setCurrentListing(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Describe your furniture item..."
                  rows={4}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  maxLength={5000}
                />
                <p className="text-xs text-gray-500 mt-1">{currentListing.description.length}/5000 characters</p>
              </div>

              <div className="flex items-center gap-3 p-4 bg-blue-50 rounded-lg">
                <input
                  type="checkbox"
                  id="auto-enhance"
                  checked={currentListing.auto_enhance_description}
                  onChange={(e) => setCurrentListing(prev => ({ ...prev, auto_enhance_description: e.target.checked }))}
                  className="rounded text-blue-600 focus:ring-blue-500"
                />
                <label htmlFor="auto-enhance" className="text-sm text-gray-700 flex items-center gap-2">
                  <Wand2 className="w-4 h-4 text-blue-600" />
                  Auto-enhance description when saving
                </label>
              </div>

              <button
                onClick={addListing}
                disabled={loading || !currentListing.title || !currentListing.price}
                className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-3 px-6 rounded-lg font-semibold hover:from-blue-700 hover:to-indigo-700 transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <Loader className="w-5 h-5 animate-spin" />
                ) : (
                  <Plus className="w-5 h-5" />
                )}
                {loading ? 'Creating...' : 'Add to Listings'}
              </button>
            </div>

            {/* Right Column - Current Listings */}
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                  <FileText className="w-6 h-6 text-green-600" />
                  Your Listings ({listings.length})
                </h2>
                {listings.length > 0 && (
                  <button
                    onClick={generateCSV}
                    disabled={loading}
                    className="bg-gradient-to-r from-green-600 to-emerald-600 text-white py-2 px-4 rounded-lg font-semibold hover:from-green-700 hover:to-emerald-700 transition-all duration-200 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? (
                      <Loader className="w-4 h-4 animate-spin" />
                    ) : (
                      <Download className="w-4 h-4" />
                    )}
                    Export CSV
                  </button>
                )}
              </div>

              <div className="space-y-4 max-h-96 overflow-y-auto">
                {listings.length === 0 ? (
                  <div className="text-center py-12 text-gray-500">
                    <FileText className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                    <p className="text-lg font-medium">No listings yet</p>
                    <p className="text-sm">Add your first furniture listing to get started</p>
                  </div>
                ) : (
                  listings.map((listing) => (
                    <div key={listing.id} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                          <h3 className="font-semibold text-gray-800 text-lg">{listing.title}</h3>
                          <p className="text-2xl font-bold text-green-600">${listing.price}</p>
                        </div>
                        <button
                          onClick={() => removeListing(listing.id)}
                          className="text-red-500 hover:text-red-700 p-1"
                        >
                          <Trash2 className="w-5 h-5" />
                        </button>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-2 text-sm text-gray-600 mb-3">
                        <div className="flex items-center gap-1">
                          <CheckCircle className="w-4 h-4 text-green-500" />
                          {listing.condition}
                        </div>
                        <div className="flex items-center gap-1">
                          <AlertCircle className="w-4 h-4 text-blue-500" />
                          {listing.category.split('//').pop()}
                        </div>
                      </div>
                      
                      {listing.images && listing.images.length > 0 && (
                        <div className="flex gap-2 mb-3">
                          {listing.images.slice(0, 3).map((image, index) => (
                            <img
                              key={index}
                              src={`${API_BASE}${image.url}`}
                              alt=""
                              className="w-12 h-12 object-cover rounded"
                            />
                          ))}
                          {listing.images.length > 3 && (
                            <div className="w-12 h-12 bg-gray-200 rounded flex items-center justify-center text-xs text-gray-600">
                              +{listing.images.length - 3}
                            </div>
                          )}
                        </div>
                      )}
                      
                      {listing.description && (
                        <p className="text-sm text-gray-600 line-clamp-2">{listing.description}</p>
                      )}
                      
                      <div className="text-xs text-gray-400 mt-2">
                        Created: {new Date(listing.created_at).toLocaleDateString()}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FurnitureMarketplaceAgent;