import React, { useState } from 'react';
import { 
  Camera, 
  Clock, 
  DollarSign, 
  Tag, 
  Eye, 
  EyeOff, 
  Edit3, 
  Copy,
  CheckCircle,
  Star,
  MapPin
} from 'lucide-react';

const ListingCard = ({ listing, onEdit, onToggleVisibility, onCopy }) => {
  const [imageError, setImageError] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  // Get the primary image URL
  const primaryImage = listing.images && listing.images.length > 0 
    ? listing.images[0].processed_url || listing.images[0].url 
    : null;

  // Format price for display
  const formatPrice = (price) => {
    if (typeof price === 'string') {
      return price.startsWith('$') ? price : `$${price}`;
    }
    return `$${price || 0}`;
  };

  // Get confidence color
  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return 'text-green-600 bg-green-100';
    if (confidence >= 0.6) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  // Get source badge
  const getSourceBadge = () => {
    const source = listing.analysis_source || listing.workflow_type;
    if (source?.includes('LANGGRAPH')) {
      return (
        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
          <Star className="w-3 h-3 mr-1" />
          LangGraph AI
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
        Legacy AI
      </span>
    );
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden hover:shadow-lg transition-shadow duration-200">
      {/* Image Section */}
      <div className="relative h-48 bg-gray-100">
        {primaryImage && !imageError ? (
          <img
            src={primaryImage}
            alt={listing.title}
            className="w-full h-full object-cover"
            onError={() => setImageError(true)}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gray-100">
            <Camera className="w-12 h-12 text-gray-400" />
          </div>
        )}
        
        {/* Image Count Badge */}
        {listing.images && listing.images.length > 1 && (
          <div className="absolute top-3 left-3 bg-black bg-opacity-75 text-white px-2 py-1 rounded-full text-xs font-medium">
            <Camera className="w-3 h-3 inline mr-1" />
            {listing.images.length}
          </div>
        )}

        {/* Visibility Toggle */}
        <div className="absolute top-3 right-3 flex space-x-2">
          {getSourceBadge()}
          <button
            onClick={() => onToggleVisibility?.(listing.id)}
            className="p-2 bg-white bg-opacity-90 rounded-full hover:bg-opacity-100 transition-all duration-200"
          >
            {listing.visible !== false ? (
              <Eye className="w-4 h-4 text-green-600" />
            ) : (
              <EyeOff className="w-4 h-4 text-gray-600" />
            )}
          </button>
        </div>
      </div>

      {/* Content Section */}
      <div className="p-4">
        {/* Title and Price */}
        <div className="flex justify-between items-start mb-3">
          <h3 className="text-lg font-semibold text-gray-900 flex-1 mr-3 line-clamp-2">
            {listing.title}
          </h3>
          <div className="text-right">
            <div className="text-xl font-bold text-green-600">
              {formatPrice(listing.price)}
            </div>
          </div>
        </div>

        {/* Description */}
        <p className="text-gray-600 text-sm mb-3 line-clamp-2">
          {listing.description}
        </p>

        {/* Metadata Row */}
        <div className="flex items-center justify-between text-xs text-gray-500 mb-3">
          <div className="flex items-center space-x-3">
            {listing.category && (
              <span className="flex items-center">
                <Tag className="w-3 h-3 mr-1" />
                {listing.category.split('//').pop()}
              </span>
            )}
            {listing.condition && (
              <span className="flex items-center">
                <CheckCircle className="w-3 h-3 mr-1" />
                {listing.condition}
              </span>
            )}
          </div>
          {listing.confidence && (
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getConfidenceColor(listing.confidence)}`}>
              {Math.round(listing.confidence * 100)}% confident
            </span>
          )}
        </div>

        {/* Analysis Details (Expandable) */}
        {(listing.processing_time || listing.agent_results) && (
          <div className="border-t pt-3 mt-3">
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="text-xs text-blue-600 hover:text-blue-800 font-medium"
            >
              {showDetails ? 'Hide' : 'Show'} Analysis Details
            </button>
            
            {showDetails && (
              <div className="mt-2 space-y-2">
                {listing.processing_time && (
                  <div className="flex items-center text-xs text-gray-600">
                    <Clock className="w-3 h-3 mr-1" />
                    Processed in {listing.processing_time}s
                  </div>
                )}
                
                {listing.agent_results && (
                  <div className="text-xs text-gray-600">
                    <div className="font-medium mb-1">AI Analysis:</div>
                    <div className="bg-gray-50 rounded p-2 space-y-1">
                      {Object.entries(listing.agent_results).map(([agent, result]) => (
                        <div key={agent} className="flex justify-between">
                          <span className="capitalize">{agent}:</span>
                          <span className={result?.success ? 'text-green-600' : 'text-red-600'}>
                            {result?.success ? '✓' : '✗'}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex space-x-2 mt-4">
          <button
            onClick={() => onEdit?.(listing)}
            className="flex-1 bg-blue-600 text-white py-2 px-3 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors duration-200 flex items-center justify-center"
          >
            <Edit3 className="w-4 h-4 mr-1" />
            Edit
          </button>
          <button
            onClick={() => onCopy?.(listing)}
            className="flex-1 bg-gray-100 text-gray-700 py-2 px-3 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors duration-200 flex items-center justify-center"
          >
            <Copy className="w-4 h-4 mr-1" />
            Copy
          </button>
        </div>
      </div>
    </div>
  );
};

export default ListingCard; 