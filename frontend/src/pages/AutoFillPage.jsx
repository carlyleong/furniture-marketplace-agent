import React, { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, Loader2, CheckCircle, AlertCircle, Edit2, Save, ArrowLeft, X, Zap, Star, Download } from 'lucide-react'
import { Link } from 'react-router-dom'
import axios from 'axios'

const AutoFillPage = () => {
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [error, setError] = useState(null)
  const [formData, setFormData] = useState({
    title: '',
    price: '',
    condition: '',
    category: '',
    description: '',
    images: []
  })
  const [aiConfidence, setAiConfidence] = useState(null)
  const [analysisComplete, setAnalysisComplete] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [warning, setWarning] = useState(null)

  const onDrop = useCallback(async (acceptedFiles) => {
    if (acceptedFiles.length === 0) return
    if (acceptedFiles.length > 10) {
      setError('Maximum 10 images allowed for auto-analysis')
      return
    }

    setIsAnalyzing(true)
    setError(null)
    setWarning(null)

    const formDataToSend = new FormData()
    acceptedFiles.forEach(file => {
      formDataToSend.append('files', file)
    })

    try {
      console.log('Starting auto-analysis...')
      const response = await axios.post('/api/auto-analyze', formDataToSend, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      const analysis = response.data
      console.log('Auto-analysis response:', analysis)

      if (analysis.error) {
        throw new Error(analysis.error)
      }

      if (!analysis.success) {
        throw new Error('Analysis failed - please try again')
      }

      // Check for warnings
      if (analysis.warning) {
        setWarning(analysis.warning)
      }

      // AUTO-FILL ALL FORM FIELDS
      setFormData({
        title: analysis.title || '',
        price: analysis.price || '',
        condition: analysis.condition || '',
        category: analysis.category || '',
        description: analysis.description || '',
        images: analysis.images || []
      })

      setAiConfidence(analysis.confidence || 0.5)
      setAnalysisComplete(true)

    } catch (error) {
      console.error('Auto-analysis error:', error)
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
    maxFiles: 10,
    disabled: isAnalyzing || analysisComplete
  })

  const handleFieldChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handleSaveListing = async () => {
    try {
      const response = await axios.post('/api/listings', {
        ...formData,
        auto_enhance_description: false
      })
      console.log('Listing saved:', response.data)
      alert('Listing saved successfully!')
    } catch (error) {
      console.error('Save error:', error)
      setError('Failed to save listing. Please try again.')
    }
  }

  const handleExport = () => {
    const csvData = [formData]
    // You can implement CSV export logic here
    console.log('Exporting:', csvData)
    alert('Export functionality would trigger here')
  }

  const resetForm = () => {
    setFormData({
      title: '',
      price: '',
      condition: '',
      category: '',
      description: '',
      images: []
    })
    setAnalysisComplete(false)
    setAiConfidence(null)
    setError(null)
    setWarning(null)
    setIsEditing(false)
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <Link
          to="/"
          className="inline-flex items-center text-gray-600 hover:text-gray-900 transition-colors"
        >
          <ArrowLeft className="h-5 w-5 mr-2" />
          Back to Home
        </Link>
        <h1 className="text-3xl font-bold text-gray-900 flex items-center">
          <Zap className="h-8 w-8 mr-3 text-yellow-500" />
          AI Auto-Fill Listing
        </h1>
        <div className="w-28"></div>
      </div>

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
                  <p className="text-lg font-medium text-gray-700">🤖 AI is analyzing your furniture...</p>
                  <p className="text-sm text-gray-500">Detecting condition, pricing, and writing description...</p>
                </div>
                <div className="bg-white rounded-lg p-4 max-w-md mx-auto">
                  <div className="flex items-center justify-center space-x-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <Upload className="h-16 w-16 text-blue-500 mx-auto" />
                <div>
                  <p className="text-xl font-medium text-gray-700">
                    {isDragActive ? 'Drop the files here!' : 'Drag & drop furniture photos here'}
                  </p>
                  <p className="text-sm text-gray-500 mt-2">
                    Or click to select files • Maximum 10 images • AI will auto-fill ALL fields!
                  </p>
                </div>
                <div className="flex items-center justify-center space-x-4 text-sm text-gray-600">
                  <span className="flex items-center">
                    <CheckCircle className="h-4 w-4 mr-1 text-green-500" />
                    JPEG, PNG, WebP
                  </span>
                  <span className="flex items-center">
                    <Zap className="h-4 w-4 mr-1 text-yellow-500" />
                    3-5 second analysis
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
      {analysisComplete && (
        <div className="space-y-6">
          {/* AI Confidence Score */}
          {aiConfidence && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <Star className="h-5 w-5 text-green-500 mr-2" />
                  <span className="text-sm font-medium text-green-800">
                    AI Confidence: {(aiConfidence * 100).toFixed(0)}%
                  </span>
                </div>
                <span className="text-xs text-green-600">
                  You can edit any field before posting
                </span>
              </div>
            </div>
          )}

          {/* Auto-filled Form */}
          <div className="bg-white rounded-xl shadow-lg p-6 border">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-semibold text-gray-900 flex items-center">
                🤖 Auto-Generated Listing
                <span className="ml-2 bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full">
                  Ready to post!
                </span>
              </h2>
              <button
                onClick={() => setIsEditing(!isEditing)}
                className="text-blue-600 hover:text-blue-700 flex items-center transition-colors"
              >
                <Edit2 className="h-4 w-4 mr-1" />
                {isEditing ? 'Done Editing' : 'Edit Fields'}
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Title */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Title</label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => handleFieldChange('title', e.target.value)}
                  disabled={!isEditing}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50 disabled:text-gray-700"
                  placeholder="Furniture title..."
                />
              </div>

              {/* Price */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Price ($)</label>
                <input
                  type="number"
                  value={formData.price}
                  onChange={(e) => handleFieldChange('price', e.target.value)}
                  disabled={!isEditing}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50 disabled:text-gray-700"
                  placeholder="0"
                />
              </div>

              {/* Condition */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Condition</label>
                <select
                  value={formData.condition}
                  onChange={(e) => handleFieldChange('condition', e.target.value)}
                  disabled={!isEditing}
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
                  value={formData.category}
                  onChange={(e) => handleFieldChange('category', e.target.value)}
                  disabled={!isEditing}
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
                value={formData.description}
                onChange={(e) => handleFieldChange('description', e.target.value)}
                disabled={!isEditing}
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50 disabled:text-gray-700"
                placeholder="Furniture description..."
              />
            </div>

            {/* Images */}
            {formData.images.length > 0 && (
              <div className="mt-6">
                <label className="block text-sm font-medium text-gray-700 mb-3">Images ({formData.images.length})</label>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {formData.images.map((image, index) => (
                    <div key={index} className="relative aspect-square group">
                      <img
                        src={image.processed_url || image.url}
                        alt={`Furniture ${index + 1}`}
                        className="w-full h-full object-cover rounded-lg border"
                        onError={(e) => {
                          e.target.src = image.url // Fallback to original URL
                        }}
                      />
                      <div className="absolute inset-0 bg-black bg-opacity-50 opacity-0 group-hover:opacity-100 transition-opacity rounded-lg flex items-center justify-center">
                        <span className="text-white text-sm">Image {index + 1}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="mt-8 flex flex-col sm:flex-row justify-between items-center gap-4">
              <button
                onClick={resetForm}
                className="text-gray-600 hover:text-gray-800 transition-colors"
              >
                Start Over
              </button>
              
              <div className="flex flex-col sm:flex-row gap-3">
                <button
                  onClick={handleExport}
                  className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center"
                >
                  <Download className="h-4 w-4 mr-2" />
                  Export CSV
                </button>
                <button
                  onClick={handleSaveListing}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center"
                >
                  <Save className="h-4 w-4 mr-2" />
                  Save Listing
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default AutoFillPage