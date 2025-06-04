import React, { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, Loader2, CheckCircle, AlertCircle, Edit2, Save, X, Zap, Star, Download, Split } from 'lucide-react'
import axios from 'axios'

const MultiItemPage = () => {
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [error, setError] = useState(null)
  const [listings, setListings] = useState([])
  const [analysisComplete, setAnalysisComplete] = useState(false)
  const [warning, setWarning] = useState(null)
  const [totalImages, setTotalImages] = useState(0)
  const [editingStates, setEditingStates] = useState({})
  const [isExporting, setIsExporting] = useState(false)

  const onDrop = useCallback(async (acceptedFiles) => {
    if (acceptedFiles.length === 0) return
    if (acceptedFiles.length > 15) {
      setError('Maximum 15 images allowed for multi-item analysis')
      return
    }

    setIsAnalyzing(true)
    setError(null)
    setWarning(null)
    setListings([])

    const formDataToSend = new FormData()
    acceptedFiles.forEach(file => {
      formDataToSend.append('files', file)
    })

    try {
      console.log('Starting multi-item auto-analysis...')
      const response = await axios.post('/api/auto-analyze-multiple', formDataToSend, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      const result = response.data
      console.log('Multi-item analysis response:', result)

      if (!result.success) {
        throw new Error(result.error || 'Analysis failed - please try again')
      }

      // Check for warnings
      if (result.warning) {
        setWarning(result.warning)
      }

      // Set the multiple listings
      setListings(result.listings || [])
      setTotalImages(result.total_images || 0)
      setAnalysisComplete(true)

      // Initialize editing states
      const editStates = {}
      result.listings?.forEach((listing, index) => {
        editStates[index] = false
      })
      setEditingStates(editStates)

    } catch (error) {
      console.error('Multi-item analysis error:', error)
      setError(error.response?.data?.detail || error.message || 'Failed to analyze images. Please try again.')
    } finally {
      setIsAnalyzing(false)
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.webp']
    },
    maxFiles: 15,
    disabled: isAnalyzing || analysisComplete
  })

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
      const response = await axios.post('/api/listings', {
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
        axios.post('/api/listings', {
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
      
      // Call backend CSV export endpoint (old method - with photo URLs)
      const response = await axios.post('/api/export-csv', exportData, {
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
      
      console.log('Exporting with organized photos:', exportData)
      
      // Call new endpoint that organizes photos into folders
      const response = await axios.post('/api/export-csv-with-photos', exportData, {
        responseType: 'blob'
      })
      
      // Create download link for zip file
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      
      // Get filename from response headers or use default
      const contentDisposition = response.headers['content-disposition']
      let filename = 'facebook-marketplace-export.zip'
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/)
        if (filenameMatch) {
          filename = filenameMatch[1]
        }
      }
      
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      
      alert(`🎉 Export complete! Downloaded:\n• CSV file (no photo columns)\n• ${listings.length} photo folders\n• README with instructions`)
      
    } catch (error) {
      console.error('Export with photos error:', error)
      alert('Error exporting with photos: ' + (error.response?.data?.detail || error.message))
    } finally {
      setIsExporting(false)
    }
  }

  const resetForm = () => {
    setListings([])
    setAnalysisComplete(false)
    setError(null)
    setWarning(null)
    setEditingStates({})
    setTotalImages(0)
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-4 flex items-center justify-center">
          <Split className="h-10 w-10 mr-3 text-blue-500" />
          🛋️ Multi-Item Furniture Classifier
        </h1>
        <p className="text-xl text-gray-600">
          Upload photos of different furniture → Get separate listings automatically!
        </p>
      </div>

      {/* Description */}
      {!analysisComplete && (
        <div className="mb-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-blue-900 mb-3 flex items-center">
            <Zap className="h-5 w-5 mr-2" />
            🤖 Multi-AI Agent System:
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-blue-800 text-sm">
            <div className="flex items-center">
              🎯 <span className="ml-2"><strong>Category Agent:</strong> Chair, Table, Sofa...</span>
            </div>
            <div className="flex items-center">
              🎨 <span className="ml-2"><strong>Color Agent:</strong> Colors, finishes, wood tones</span>
            </div>
            <div className="flex items-center">
              🏷️ <span className="ml-2"><strong>Brand Agent:</strong> IKEA, Herman Miller...</span>
            </div>
            <div className="flex items-center">
              📏 <span className="ml-2"><strong>Dimensions Agent:</strong> Size estimation</span>
            </div>
            <div className="flex items-center">
              🎨 <span className="ml-2"><strong>Style Agent:</strong> Modern, Traditional...</span>
            </div>
            <div className="flex items-center">
              💰 <span className="ml-2"><strong>Pricing Agent:</strong> Market research</span>
            </div>
          </div>
          <div className="mt-4 text-blue-700">
            <p>• Upload photos of <strong>different furniture items</strong></p>
            <p>• AI agents work in parallel to analyze each piece</p>
            <p>• Get detailed listings with brand, dimensions, and market pricing</p>
          </div>
        </div>
      )}

      {/* Upload Section */}
      {!analysisComplete && (
        <div className="mb-8">
          <div
            {...getRootProps()}
            className={`
              border-2 border-dashed rounded-xl p-12 text-center transition-all cursor-pointer
              ${isDragActive 
                ? 'border-blue-500 bg-blue-50' 
                : isAnalyzing 
                  ? 'border-gray-300 bg-gray-50 cursor-not-allowed' 
                  : 'border-blue-400 bg-blue-50 hover:border-blue-500 hover:bg-blue-100'
              }
            `}
          >
            <input {...getInputProps()} />
            
            {isAnalyzing ? (
              <div className="space-y-4">
                <Loader2 className="h-12 w-12 text-blue-500 animate-spin mx-auto" />
                <div>
                  <p className="text-lg font-medium text-gray-700">🤖 6 AI Agents analyzing your furniture...</p>
                  <p className="text-sm text-gray-500">Category • Color • Brand • Dimensions • Style • Pricing</p>
                </div>
                <div className="bg-white rounded-lg p-4 max-w-md mx-auto">
                  <div className="grid grid-cols-6 gap-2">
                    <div className="w-3 h-3 bg-blue-500 rounded-full animate-pulse" title="Category Agent"></div>
                    <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }} title="Color Agent"></div>
                    <div className="w-3 h-3 bg-purple-500 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }} title="Brand Agent"></div>
                    <div className="w-3 h-3 bg-orange-500 rounded-full animate-pulse" style={{ animationDelay: '0.6s' }} title="Dimensions Agent"></div>
                    <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" style={{ animationDelay: '0.8s' }} title="Style Agent"></div>
                    <div className="w-3 h-3 bg-yellow-500 rounded-full animate-pulse" style={{ animationDelay: '1.0s' }} title="Pricing Agent"></div>
                  </div>
                  <p className="text-xs text-gray-500 text-center mt-2">Parallel processing for speed</p>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <Upload className="h-16 w-16 text-blue-500 mx-auto" />
                <div>
                  <p className="text-xl font-medium text-gray-700">
                    {isDragActive ? 'Drop the files here!' : 'Upload photos of DIFFERENT furniture items'}
                  </p>
                  <p className="text-sm text-gray-500 mt-2">
                    Or click to select files • Maximum 15 images • AI will create separate listings!
                  </p>
                </div>
                <div className="flex items-center justify-center space-x-4 text-sm text-gray-600">
                  <span className="flex items-center">
                    <CheckCircle className="h-4 w-4 mr-1 text-green-500" />
                    JPEG, PNG, WebP
                  </span>
                  <span className="flex items-center">
                    <Split className="h-4 w-4 mr-1 text-blue-500" />
                    Auto-groups items
                  </span>
                  <span className="flex items-center">
                    <Zap className="h-4 w-4 mr-1 text-yellow-500" />
                    5-10 second analysis
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 rounded-lg flex items-start">
          <AlertCircle className="h-5 w-5 text-red-500 mr-3 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-red-800">Error</p>
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      )}

      {/* Warning Display */}
      {warning && (
        <div className="mb-6 p-4 bg-yellow-50 rounded-lg flex items-start">
          <AlertCircle className="h-5 w-5 text-yellow-500 mr-3 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-yellow-800">Warning</p>
            <p className="text-sm text-yellow-700">{warning}</p>
          </div>
        </div>
      )}

      {/* Results Section */}
      {analysisComplete && listings.length > 0 && (
        <div className="space-y-8">
          {/* Summary */}
          <div className="bg-green-50 border border-green-200 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <CheckCircle className="h-6 w-6 text-green-500 mr-3" />
                <div>
                  <h2 className="text-lg font-semibold text-green-900">
                    Analysis Complete! Found {listings.length} furniture item{listings.length > 1 ? 's' : ''}
                  </h2>
                  <p className="text-sm text-green-700">
                    From {totalImages} uploaded image{totalImages > 1 ? 's' : ''} • Ready to save or export
                  </p>
                </div>
              </div>
              <div className="flex space-x-3">
                <button
                  onClick={handleExportWithPhotos}
                  disabled={isExporting}
                  className={`px-4 py-2 rounded-lg transition-colors flex items-center ${
                    isExporting 
                      ? 'bg-gray-400 cursor-not-allowed' 
                      : 'bg-green-600 hover:bg-green-700'
                  } text-white`}
                >
                  {isExporting ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Exporting...
                    </>
                  ) : (
                    <>
                      <Download className="h-4 w-4 mr-2" />
                      📋 Export + Photos
                    </>
                  )}
                </button>
                <button
                  onClick={handleExportAll}
                  disabled={isExporting}
                  className={`px-4 py-2 rounded-lg transition-colors flex items-center ${
                    isExporting 
                      ? 'bg-gray-400 cursor-not-allowed' 
                      : 'bg-gray-600 hover:bg-gray-700'
                  } text-white text-sm`}
                >
                  {isExporting ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Exporting...
                    </>
                  ) : (
                    <>
                      CSV Only
                    </>
                  )}
                </button>
                <button
                  onClick={handleSaveAll}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center"
                >
                  <Save className="h-4 w-4 mr-2" />
                  Save All ({listings.length})
                </button>
              </div>
            </div>
            
            <div className="mt-4 text-sm text-green-700">
              <p><strong>📋 Export + Photos:</strong> Downloads CSV (no photo columns) + organized photo folders ready for Facebook upload</p>
              <p><strong>CSV Only:</strong> Downloads CSV with photo URLs (for advanced users)</p>
              <p><strong>Save All:</strong> Saves listings to your local database</p>
            </div>
          </div>

          {/* Individual Listings */}
          {listings.map((listing, index) => (
            <div key={index} className="bg-white rounded-xl shadow-lg p-6 border">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-semibold text-gray-900 flex items-center">
                  🛋️ Listing {index + 1}: {listing.title}
                  <span className="ml-3 bg-blue-100 text-blue-800 text-sm px-2 py-1 rounded-full">
                    {listing.photo_count || listing.images?.length || 0} photo{(listing.photo_count || listing.images?.length || 0) > 1 ? 's' : ''}
                  </span>
                </h3>
                <div className="flex items-center space-x-3">
                  {listing.confidence && (
                    <span className="text-sm text-gray-600">
                      <Star className="h-4 w-4 inline mr-1" />
                      {(listing.confidence * 100).toFixed(0)}% confidence
                    </span>
                  )}
                  <button
                    onClick={() => toggleEditing(index)}
                    className="text-blue-600 hover:text-blue-700 flex items-center transition-colors"
                  >
                    <Edit2 className="h-4 w-4 mr-1" />
                    {editingStates[index] ? 'Done' : 'Edit'}
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Title */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Title</label>
                  <input
                    type="text"
                    value={listing.title || ''}
                    onChange={(e) => handleFieldChange(index, 'title', e.target.value)}
                    disabled={!editingStates[index]}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50 disabled:text-gray-700"
                  />
                </div>

                {/* Price */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Price ($)</label>
                  <input
                    type="number"
                    value={listing.price || ''}
                    onChange={(e) => handleFieldChange(index, 'price', e.target.value)}
                    disabled={!editingStates[index]}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50 disabled:text-gray-700"
                  />
                </div>

                {/* Condition */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Condition</label>
                  <select
                    value={listing.condition || ''}
                    onChange={(e) => handleFieldChange(index, 'condition', e.target.value)}
                    disabled={!editingStates[index]}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50 disabled:text-gray-700"
                  >
                    <option value="">Select condition</option>
                    <option value="New">New</option>
                    <option value="Like New">Like New</option>
                    <option value="Good">Good</option>
                    <option value="Fair">Fair</option>
                    <option value="Poor">Poor</option>
                  </select>
                </div>

                {/* Category */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Category</label>
                  <select
                    value={listing.category || ''}
                    onChange={(e) => handleFieldChange(index, 'category', e.target.value)}
                    disabled={!editingStates[index]}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50 disabled:text-gray-700"
                  >
                    <option value="">Select category</option>
                    <option value="Chair">Chair</option>
                    <option value="Table">Table</option>
                    <option value="Sofa">Sofa</option>
                    <option value="Bed">Bed</option>
                    <option value="Desk">Desk</option>
                    <option value="Cabinet">Cabinet</option>
                    <option value="Bookshelf">Bookshelf</option>
                    <option value="Dresser">Dresser</option>
                  </select>
                </div>
              </div>

              {/* Description */}
              <div className="mt-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
                <textarea
                  value={listing.description || ''}
                  onChange={(e) => handleFieldChange(index, 'description', e.target.value)}
                  disabled={!editingStates[index]}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50 disabled:text-gray-700"
                />
              </div>

              {/* Images */}
              {listing.images && listing.images.length > 0 && (
                <div className="mt-6">
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Images ({listing.images.length})
                  </label>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {listing.images.map((image, imgIndex) => (
                      <div key={imgIndex} className="relative aspect-square group">
                        <img
                          src={image.processed_url || image.url}
                          alt={`${listing.title} ${imgIndex + 1}`}
                          className="w-full h-full object-cover rounded-lg border"
                          onError={(e) => {
                            e.target.src = image.url // Fallback to original URL
                          }}
                        />
                        <div className="absolute inset-0 bg-black bg-opacity-50 opacity-0 group-hover:opacity-100 transition-opacity rounded-lg flex items-center justify-center">
                          <span className="text-white text-sm">Photo {imgIndex + 1}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Individual Save Button */}
              <div className="mt-6 flex justify-end">
                <button
                  onClick={() => handleSaveListing(index)}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center"
                >
                  <Save className="h-4 w-4 mr-2" />
                  Save This Listing
                </button>
              </div>
            </div>
          ))}

          {/* Reset Button */}
          <div className="text-center">
            <button
              onClick={resetForm}
              className="text-gray-600 hover:text-gray-800 transition-colors"
            >
              Start Over with New Photos
            </button>
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
