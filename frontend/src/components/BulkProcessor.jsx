import React, { useState, useCallback } from 'react';
import { 
  Upload, 
  Play, 
  Pause, 
  Square, 
  CheckCircle, 
  AlertCircle, 
  Clock,
  Loader,
  FileImage,
  Star,
  Zap
} from 'lucide-react';
import ImageUploader from './ImageUploader';

const BulkProcessor = ({ onComplete, onProgress }) => {
  const [selectedImages, setSelectedImages] = useState([]);
  const [processing, setProcessing] = useState(false);
  const [results, setResults] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [startTime, setStartTime] = useState(null);
  const [useRealAI, setUseRealAI] = useState(true);

  const handleImagesSelected = useCallback((newImages) => {
    setSelectedImages(newImages);
    setResults([]);
    setCurrentIndex(0);
  }, []);

  const processImages = async () => {
    if (selectedImages.length === 0) return;

    setProcessing(true);
    setStartTime(Date.now());
    setResults([]);
    
    const formData = new FormData();
    selectedImages.forEach((file) => {
      formData.append('files', file);
    });

    // Add processing options
    formData.append('use_real_ai', useRealAI.toString());
    formData.append('force_langgraph', 'true');

    try {
      const response = await fetch('http://localhost:8000/api/auto-analyze-multiple', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      setResults(data.results || []);
      setProcessing(false);
      
      onComplete?.(data);
      
    } catch (error) {
      console.error('Bulk processing error:', error);
      setProcessing(false);
      alert(`Processing failed: ${error.message}`);
    }
  };

  const resetProcessor = () => {
    setSelectedImages([]);
    setResults([]);
    setCurrentIndex(0);
    setProcessing(false);
    setStartTime(null);
  };

  const getProcessingStats = () => {
    if (!startTime || !processing) return null;
    
    const elapsed = (Date.now() - startTime) / 1000;
    const avgTime = currentIndex > 0 ? elapsed / currentIndex : 0;
    const remaining = (selectedImages.length - currentIndex) * avgTime;
    
    return {
      elapsed: elapsed.toFixed(1),
      remaining: remaining.toFixed(1),
      avgTime: avgTime.toFixed(1)
    };
  };

  const stats = getProcessingStats();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold flex items-center">
              <Zap className="w-6 h-6 mr-2" />
              LangGraph Bulk Processor
            </h2>
            <p className="mt-1 text-blue-100">
              AI-powered furniture analysis for multiple images
            </p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold">{selectedImages.length}</div>
            <div className="text-blue-100">Images Selected</div>
          </div>
        </div>
      </div>

      {/* Processing Options */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Processing Options</h3>
        <div className="space-y-3">
          <label className="flex items-center space-x-3">
            <input
              type="checkbox"
              checked={useRealAI}
              onChange={(e) => setUseRealAI(e.target.checked)}
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              disabled={processing}
            />
            <span className="text-sm text-gray-700">
              Use Real AI Analysis (OpenAI + Gemini)
            </span>
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
              <Star className="w-3 h-3 mr-1" />
              Recommended
            </span>
          </label>
          <p className="text-xs text-gray-500 ml-7">
            When enabled, uses LangGraph workflow with OpenAI GPT-4 and Gemini for enhanced accuracy.
          </p>
        </div>
      </div>

      {/* Image Uploader */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <ImageUploader
          onImagesSelected={handleImagesSelected}
          selectedImages={selectedImages}
          maxImages={15}
        />
      </div>

      {/* Processing Controls */}
      {selectedImages.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              {!processing ? (
                <button
                  onClick={processImages}
                  disabled={selectedImages.length === 0}
                  className="flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
                >
                  <Play className="w-5 h-5 mr-2" />
                  Start AI Analysis
                </button>
              ) : (
                <div className="flex items-center space-x-3">
                  <div className="flex items-center px-4 py-2 bg-yellow-100 text-yellow-800 rounded-lg">
                    <Loader className="w-4 h-4 mr-2 animate-spin" />
                    Processing...
                  </div>
                  <button
                    onClick={() => setProcessing(false)}
                    className="px-4 py-2 bg-red-100 text-red-800 rounded-lg hover:bg-red-200"
                  >
                    <Square className="w-4 h-4 mr-1 inline" />
                    Stop
                  </button>
                </div>
              )}
              
              {(results.length > 0 || processing) && (
                <button
                  onClick={resetProcessor}
                  disabled={processing}
                  className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50"
                >
                  Reset
                </button>
              )}
            </div>

            {/* Processing Stats */}
            {processing && stats && (
              <div className="text-sm text-gray-600 space-y-1">
                <div>Processing: {currentIndex} / {selectedImages.length}</div>
                <div>Elapsed: {stats.elapsed}s | Remaining: ~{stats.remaining}s</div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Progress Bar */}
      {processing && (
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Processing Progress</span>
            <span>{Math.round((currentIndex / selectedImages.length) * 100)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${(currentIndex / selectedImages.length) * 100}%` }}
            />
          </div>
          <div className="mt-2 text-xs text-gray-500">
            Using LangGraph AI workflow with real-time analysis
          </div>
        </div>
      )}

      {/* Results Summary */}
      {results.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Processing Results ({results.length} listings created)
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-green-50 rounded-lg p-4">
              <div className="flex items-center">
                <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
                <span className="text-sm font-medium text-green-800">Successful</span>
              </div>
              <div className="text-2xl font-bold text-green-900 mt-1">
                {results.filter(r => r.success).length}
              </div>
            </div>
            
            <div className="bg-red-50 rounded-lg p-4">
              <div className="flex items-center">
                <AlertCircle className="w-5 h-5 text-red-600 mr-2" />
                <span className="text-sm font-medium text-red-800">Failed</span>
              </div>
              <div className="text-2xl font-bold text-red-900 mt-1">
                {results.filter(r => !r.success).length}
              </div>
            </div>
            
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="flex items-center">
                <Clock className="w-5 h-5 text-blue-600 mr-2" />
                <span className="text-sm font-medium text-blue-800">Avg Time</span>
              </div>
              <div className="text-2xl font-bold text-blue-900 mt-1">
                {results.length > 0 ? 
                  (results.reduce((sum, r) => sum + (r.processing_time || 0), 0) / results.length).toFixed(1) : 0}s
              </div>
            </div>
          </div>

          {/* Results List */}
          <div className="space-y-3">
            <h4 className="font-medium text-gray-900">Detailed Results:</h4>
            {results.map((result, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  {result.success ? (
                    <CheckCircle className="w-5 h-5 text-green-600" />
                  ) : (
                    <AlertCircle className="w-5 h-5 text-red-600" />
                  )}
                  <div>
                    <div className="font-medium text-gray-900">
                      {result.title || `Image ${index + 1}`}
                    </div>
                    <div className="text-sm text-gray-600">
                      {result.success ? `$${result.price} • ${result.processing_time}s` : result.error}
                    </div>
                  </div>
                </div>
                {result.workflow_type && (
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    {result.workflow_type}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default BulkProcessor; 