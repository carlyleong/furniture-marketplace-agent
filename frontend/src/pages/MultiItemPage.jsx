import React, { useState } from 'react'
import { CheckCircle, AlertCircle, Edit2, Save, X, Download, Split } from 'lucide-react'
import axios from 'axios'
import BulkProcessor from '../components/BulkProcessor'
import { getApiUrl } from '../config/api'

const MultiItemPage = () => {
  const [listings, setListings] = useState([])
  const [analysisComplete, setAnalysisComplete] = useState(false)
  const [warning, setWarning] = useState(null)
  const [error, setError] = useState(null)
  const [totalImages, setTotalImages] = useState(0)
  const [editingStates, setEditingStates] = useState({})
  const [isExporting, setIsExporting] = useState(false)

  const handleAnalysisComplete = (data) => {
    console.log('Analysis completed:', data)
    
    if (!data || data.status !== 'success') {
      setError('Analysis failed - please try again')
      return
    }

    // Check for warnings
    if (data.warning) {
      setWarning(data.warning)
    }

    // Set the multiple listings
    setListings(data.listings || [])
    setTotalImages(data.total_images || 0)
    setAnalysisComplete(true)

    // Initialize editing states
    const editStates = {}
    data.listings?.forEach((listing, index) => {
      editStates[index] = false
    })
    setEditingStates(editStates)
  }

  const handleFieldChange = (listingIndex, field, value) => {
    setListings(prev => prev.map((listing, index) => 
      index === listingIndex 
        ? { ...listing, [field]: value }
        : listing
    ))
  }

  const toggleEditing = (listingIndex) => {
    setEditingStates(prev => ({
      ...prev,
      [listingIndex]: !prev[listingIndex]
    }))
  }

  const handleSaveListing = async (listingIndex) => {
    const listing = listings[listingIndex]
    try {
      const response = await axios.post(getApiUrl('/api/listings'), {
        ...listing,
        price: parseFloat(listing.price) || 0,
        auto_enhance_description: false
      })
      console.log('Listing saved:', response.data)
      alert(`"${listing.title}" saved successfully!`)
    } catch (error) {
      console.error('Save error:', error)
      setError(`Failed to save "${listing.title}". Please try again.`)
    }
  }

  const handleSaveAll = async () => {
    try {
      const savePromises = listings.map(listing => 
        axios.post(getApiUrl('/api/listings'), {
          ...listing,
          price: parseFloat(listing.price) || 0,
          auto_enhance_description: false
        })
      )
      
      await Promise.all(savePromises)
      alert(`All ${listings.length} listings saved successfully!`)
    } catch (error) {
      console.error('Save all error:', error)
      setError('Failed to save some listings. Please try saving individually.')
    }
  }

  const handleExportAll = async () => {
    try {
      setIsExporting(true)
      
      // Prepare listings data for export
      const exportData = listings.map(listing => ({
        title: listing.title || '',
        description: listing.description || '',
        price: listing.price || '0',
        condition: listing.condition || '',
        category: listing.category || '',
        images: listing.images || []
      }))
      
      console.log('Exporting data:', exportData)
      
      // Call backend CSV export endpoint
      const response = await axios.post(getApiUrl('/api/export-csv'), exportData, {
        responseType: 'blob'
      })
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      
      // Use current date for filename
      const date = new Date().toISOString().split('T')[0]
      link.download = `facebook-marketplace-listings-${date}.csv`
      
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      
      alert(`✅ CSV exported successfully! Downloaded ${listings.length} listings.`)
      
    } catch (error) {
      console.error('Export error:', error)
      alert('Error exporting CSV: ' + (error.response?.data?.detail || error.message))
    } finally {
      setIsExporting(false)
    }
  }

  const handleExportWithPhotos = async () => {
    try {
      setIsExporting(true)
      
      // Prepare listings data for export
      const exportData = listings.map(listing => ({
        title: listing.title || '',
        description: listing.description || '',
        price: listing.price || '0',
        condition: listing.condition || '',
        category: listing.category || '',
        images: listing.images || []
      }))
      
      console.log('Exporting data with photos:', exportData)
      
      // Call backend CSV+Photos export endpoint
      const response = await axios.post(getApiUrl('/api/export-csv-with-photos'), exportData)
      
      // Check if we got a JSON response with download URL (production with GCS)
      if (response.data && typeof response.data === 'object' && response.data.download_url) {
        // Direct download from GCS URL
        const downloadUrl = response.data.download_url
        const filename = response.data.filename || 'export.zip'
        
        const link = document.createElement('a')
        link.href = downloadUrl
        link.download = filename
        link.target = '_blank' // Open in new tab as fallback
        
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        
        alert(`✅ ${response.data.message || 'Export complete!'}`)
      } else {
        // Handle as blob (local development or fallback)
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        
        // Use current date for filename
        const date = new Date().toISOString().split('T')[0]
        link.download = `facebook-marketplace-export-${date}.zip`
        
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
        
        alert(`✅ Export complete! Downloaded ZIP with ${listings.length} listings and their photos.`)
      }
      
    } catch (error) {
      console.error('Export error:', error)
      alert('Error exporting ZIP: ' + (error.response?.data?.detail || error.message))
    } finally {
      setIsExporting(false)
    }
  }

  const resetForm = () => {
    setListings([])
    setAnalysisComplete(false)
    setWarning(null)
    setError(null)
    setTotalImages(0)
    setEditingStates({})
  }

  return (
    <div className="max-w-7xl mx-auto p-4 space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          LangGraph Furniture Classifier
        </h1>
        <p className="text-gray-600">
          Upload multiple furniture images for AI-powered analysis and automatic Facebook Marketplace listing generation.
        </p>
      </div>

      {/* Bulk Processor Component */}
      {!analysisComplete && (
        <BulkProcessor 
          onComplete={handleAnalysisComplete}
          onProgress={(progress) => {
            // Handle progress updates if needed
            console.log('Progress:', progress)
          }}
        />
      )}

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <AlertCircle className="w-5 h-5 text-red-600 mr-2" />
            <span className="text-red-800">{error}</span>
          </div>
        </div>
      )}

      {/* Warning Display */}
      {warning && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-center">
            <AlertCircle className="w-5 h-5 text-yellow-600 mr-2" />
            <span className="text-yellow-800">{warning}</span>
          </div>
        </div>
      )}

      {/* Results */}
      {analysisComplete && listings.length > 0 && (
        <div className="space-y-8">
          {/* Success Header */}
          <div className="bg-green-50 border border-green-200 rounded-lg p-6">
            <div className="flex items-center">
              <CheckCircle className="w-6 h-6 text-green-600 mr-3" />
              <div>
                <h2 className="text-xl font-semibold text-green-900">
                  Analysis Complete! 🎉
                </h2>
                <p className="text-green-700">
                  Created {listings.length} listing{listings.length !== 1 ? 's' : ''} from {totalImages} images
                </p>
              </div>
            </div>
          </div>

          {/* Export Actions */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Export Options</h3>
            <div className="flex flex-wrap gap-3">
              <button
                onClick={handleSaveAll}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center"
              >
                <Save className="w-4 h-4 mr-2" />
                Save All Listings
              </button>
              <button
                onClick={handleExportWithPhotos}
                disabled={isExporting}
                className={`px-4 py-2 rounded-lg transition-colors flex items-center ${
                  isExporting 
                    ? 'bg-gray-400 cursor-not-allowed' 
                    : 'bg-purple-600 hover:bg-purple-700'
                } text-white`}
              >
                {isExporting ? (
                  <>
                    <div className="w-4 h-4 mr-2 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Exporting...
                  </>
                ) : (
                  <>
                    <Download className="w-4 h-4 mr-2" />
                    Export ZIP with Photos
                  </>
                )}
              </button>
              <button
                onClick={handleExportAll}
                disabled={isExporting}
                className={`px-4 py-2 rounded-lg transition-colors flex items-center ${
                  isExporting 
                    ? 'bg-gray-400 cursor-not-allowed' 
                    : 'bg-green-600 hover:bg-green-700'
                } text-white`}
              >
                {isExporting ? (
                  <>
                    <div className="w-4 h-4 mr-2 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Exporting...
                  </>
                ) : (
                  <>
                    <Download className="w-4 h-4 mr-2" />
                    Export CSV Only
                  </>
                )}
              </button>
              <button
                onClick={resetForm}
                className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors flex items-center"
              >
                <X className="w-4 h-4 mr-2" />
                Start Over
              </button>
            </div>
            
            <div className="mt-4 text-sm text-gray-600">
              <p><strong>Save All:</strong> Saves listings to your local database</p>
              <p><strong>Export ZIP with Photos:</strong> Downloads a ZIP file containing the CSV and organized photo folders</p>
              <p><strong>Export CSV Only:</strong> Downloads just the CSV file for Facebook Marketplace</p>
            </div>
          </div>

          {/* Listings */}
          <div className="space-y-6">
            {listings.map((listing, index) => (
              <div key={index} className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                {/* Listing Header */}
                <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-gray-900">
                      Listing {index + 1}: {listing.title || 'Untitled'}
                    </h3>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => toggleEditing(index)}
                        className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 transition-colors flex items-center"
                      >
                        <Edit2 className="w-3 h-3 mr-1" />
                        {editingStates[index] ? 'View' : 'Edit'}
                      </button>
                      <button
                        onClick={() => handleSaveListing(index)}
                        className="px-3 py-1 text-sm bg-green-100 text-green-700 rounded-md hover:bg-green-200 transition-colors flex items-center"
                      >
                        <Save className="w-3 h-3 mr-1" />
                        Save
                      </button>
                    </div>
                  </div>
                </div>

                <div className="p-6">
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Images */}
                    <div>
                      <h4 className="font-medium text-gray-900 mb-3">Images ({listing.images?.length || 0})</h4>
                      {listing.images && listing.images.length > 0 ? (
                        <div className="grid grid-cols-2 gap-2">
                          {listing.images.slice(0, 4).map((image, imgIndex) => {
                            // Enhanced debugging for image loading issues
                            console.log(`=== IMAGE DEBUG ${imgIndex + 1} ===`);
                            console.log('Raw image data:', JSON.stringify(image, null, 2));
                            
                            let imageUrl = '';
                            
                            if (typeof image === 'string') {
                              // Simple string URL
                              imageUrl = image.startsWith('/') ? image : `/static/${image}`;
                              console.log('String image URL:', imageUrl);
                            } else if (image && typeof image === 'object') {
                              // Use url first (static, known working), then processed_url, then construct from filename
                              console.log('Available URLs:', {
                                processed_url: image.processed_url,
                                url: image.url,
                                filename: image.filename
                              });
                              
                              // Try different URL patterns for production vs development
                              if (image.processed_url && image.processed_url.startsWith('/api/image/')) {
                                imageUrl = image.processed_url; // New API endpoint
                              } else if (image.url) {
                                imageUrl = image.url; // Static URL
                              } else if (image.processed_url) {
                                imageUrl = image.processed_url; // Legacy processed URL
                              } else if (image.filename) {
                                imageUrl = `/static/${image.filename}`; // Fallback
                              }
                              console.log('Selected image URL:', imageUrl);
                            } else {
                              console.error('Invalid image data:', image);
                              imageUrl = '/static/placeholder.jpg';
                            }
                            
                            console.log(`Final URL for image ${imgIndex + 1}: ${imageUrl}`);
                            
                            return (
                              <div key={imgIndex} className="aspect-square bg-gray-100 rounded-lg overflow-hidden">
                                <img
                                  src={imageUrl}
                                  alt={`${listing.title} ${imgIndex + 1}`}
                                  className="w-full h-full object-cover"
                                  onLoad={() => {
                                    console.log(`✅ SUCCESS: Image ${imgIndex + 1} loaded successfully from: ${imageUrl}`);
                                  }}
                                  onError={(e) => {
                                    console.error(`❌ FAILED: Image ${imgIndex + 1} failed to load from: ${imageUrl}`);
                                    console.error('Error event:', e);
                                    console.error('Image element:', e.target);
                                    
                                    // Try backup URLs in sequence
                                    if (image && typeof image === 'object') {
                                      if (image.filename && !imageUrl.includes('/api/image/')) {
                                        const apiUrl = `/api/image/${image.filename}`;
                                        console.log(`🔄 RETRY: Trying API endpoint: ${apiUrl}`);
                                        e.target.src = apiUrl;
                                        return;
                                      } else if (image.processed_url && imageUrl !== image.processed_url) {
                                        console.log(`🔄 RETRY: Trying processed URL: ${image.processed_url}`);
                                        e.target.src = image.processed_url;
                                        return;
                                      } else if (image.url && imageUrl !== image.url) {
                                        console.log(`🔄 RETRY: Trying original URL: ${image.url}`);
                                        e.target.src = image.url;
                                        return;
                                      } else if (image.filename && !imageUrl.includes(image.filename)) {
                                        const staticUrl = `/static/${image.filename}`;
                                        console.log(`🔄 RETRY: Trying static URL: ${staticUrl}`);
                                        e.target.src = staticUrl;
                                        return;
                                      }
                                    }
                                    
                                    // Show placeholder as last resort
                                    console.log('🔄 FALLBACK: Showing placeholder');
                                    e.target.style.display = 'none';
                                    e.target.parentElement.innerHTML = `
                                      <div class="w-full h-full bg-gray-200 flex items-center justify-center text-gray-500">
                                        <div class="text-center">
                                          <svg class="w-8 h-8 mx-auto mb-2" fill="currentColor" viewBox="0 0 20 20">
                                            <path fill-rule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clip-rule="evenodd"></path>
                                          </svg>
                                          <p class="text-xs">Image ${imgIndex + 1}</p>
                                          <p class="text-xs text-red-500">Failed: ${imageUrl}</p>
                                        </div>
                                      </div>
                                    `;
                                  }}
                                />
                              </div>
                            );
                          })}
                          {listing.images.length > 4 && (
                            <div className="aspect-square bg-gray-100 rounded-lg flex items-center justify-center text-gray-500">
                              +{listing.images.length - 4} more
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="aspect-square bg-gray-100 rounded-lg flex items-center justify-center text-gray-500">
                          No images
                        </div>
                      )}
                    </div>

                    {/* Listing Details */}
                    <div className="space-y-4">
                      {/* Title */}
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
                        {editingStates[index] ? (
                          <input
                            type="text"
                            value={listing.title || ''}
                            onChange={(e) => handleFieldChange(index, 'title', e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />
                        ) : (
                          <p className="text-gray-900">{listing.title || 'No title'}</p>
                        )}
                      </div>

                      {/* Price */}
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Price</label>
                        {editingStates[index] ? (
                          <input
                            type="number"
                            value={listing.price || ''}
                            onChange={(e) => handleFieldChange(index, 'price', e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />
                        ) : (
                          <p className="text-gray-900 font-semibold">${listing.price || '0'}</p>
                        )}
                      </div>

                      {/* Category */}
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                        {editingStates[index] ? (
                          <input
                            type="text"
                            value={listing.category || ''}
                            onChange={(e) => handleFieldChange(index, 'category', e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />
                        ) : (
                          <p className="text-gray-900">{listing.category || 'No category'}</p>
                        )}
                      </div>

                      {/* Condition */}
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Condition</label>
                        {editingStates[index] ? (
                          <select
                            value={listing.condition || ''}
                            onChange={(e) => handleFieldChange(index, 'condition', e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          >
                            <option value="">Select condition</option>
                            <option value="New">New</option>
                            <option value="Like New">Like New</option>
                            <option value="Good">Good</option>
                            <option value="Fair">Fair</option>
                            <option value="Poor">Poor</option>
                          </select>
                        ) : (
                          <p className="text-gray-900">{listing.condition || 'No condition'}</p>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Description */}
                  <div className="mt-6">
                    <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                    {editingStates[index] ? (
                      <textarea
                        value={listing.description || ''}
                        onChange={(e) => handleFieldChange(index, 'description', e.target.value)}
                        rows={4}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    ) : (
                      <p className="text-gray-900 whitespace-pre-wrap">{listing.description || 'No description'}</p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* No Results */}
      {analysisComplete && listings.length === 0 && (
        <div className="text-center py-12">
          <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No furniture items detected</h3>
          <p className="text-gray-600 mb-4">The AI couldn't identify any furniture in the uploaded images.</p>
          <button
            onClick={resetForm}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Try Different Photos
          </button>
        </div>
      )}
    </div>
  )
}

export default MultiItemPage
