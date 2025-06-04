import React, { useState, useMemo } from 'react';
import { 
  Grid, 
  List, 
  Filter, 
  Search, 
  SortAsc, 
  SortDesc,
  Star,
  DollarSign,
  Clock,
  Eye,
  EyeOff
} from 'lucide-react';
import ListingCard from './ListingCard';

const ListingGrid = ({ 
  listings = [], 
  onEdit, 
  onToggleVisibility, 
  onCopy, 
  loading = false 
}) => {
  const [viewMode, setViewMode] = useState('grid');
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('newest');
  const [filterBy, setFilterBy] = useState('all');
  const [showFilters, setShowFilters] = useState(false);

  // Filter and sort listings
  const filteredAndSortedListings = useMemo(() => {
    let filtered = listings;

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter(listing =>
        listing.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        listing.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        listing.category?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Apply category filter
    if (filterBy !== 'all') {
      switch (filterBy) {
        case 'langgraph':
          filtered = filtered.filter(listing => 
            listing.analysis_source?.includes('LANGGRAPH') || 
            listing.workflow_type?.includes('LANGGRAPH')
          );
          break;
        case 'legacy':
          filtered = filtered.filter(listing => 
            !listing.analysis_source?.includes('LANGGRAPH') && 
            !listing.workflow_type?.includes('LANGGRAPH')
          );
          break;
        case 'high-confidence':
          filtered = filtered.filter(listing => (listing.confidence || 0) >= 0.8);
          break;
        case 'visible':
          filtered = filtered.filter(listing => listing.visible !== false);
          break;
        case 'hidden':
          filtered = filtered.filter(listing => listing.visible === false);
          break;
        default:
          break;
      }
    }

    // Apply sorting
    return filtered.sort((a, b) => {
      switch (sortBy) {
        case 'newest':
          return new Date(b.created_at || 0) - new Date(a.created_at || 0);
        case 'oldest':
          return new Date(a.created_at || 0) - new Date(b.created_at || 0);
        case 'price-high':
          return (parseFloat(b.price) || 0) - (parseFloat(a.price) || 0);
        case 'price-low':
          return (parseFloat(a.price) || 0) - (parseFloat(b.price) || 0);
        case 'confidence':
          return (b.confidence || 0) - (a.confidence || 0);
        case 'title':
          return (a.title || '').localeCompare(b.title || '');
        default:
          return 0;
      }
    });
  }, [listings, searchTerm, sortBy, filterBy]);

  // Get statistics
  const stats = useMemo(() => {
    const total = listings.length;
    const langGraphCount = listings.filter(l => 
      l.analysis_source?.includes('LANGGRAPH') || 
      l.workflow_type?.includes('LANGGRAPH')
    ).length;
    const highConfidence = listings.filter(l => (l.confidence || 0) >= 0.8).length;
    const visible = listings.filter(l => l.visible !== false).length;

    return {
      total,
      langGraph: langGraphCount,
      legacy: total - langGraphCount,
      highConfidence,
      visible,
      hidden: total - visible
    };
  }, [listings]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600">Loading listings...</span>
      </div>
    );
  }

  if (listings.length === 0) {
    return (
      <div className="text-center py-12">
        <Grid className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-4 text-lg font-medium text-gray-900">No listings yet</h3>
        <p className="mt-2 text-gray-600">
          Upload some furniture images to get started with AI analysis.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Stats */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              Furniture Listings ({filteredAndSortedListings.length})
            </h2>
            <div className="mt-1 flex items-center space-x-4 text-sm text-gray-600">
              <span className="flex items-center">
                <Star className="w-4 h-4 mr-1 text-blue-600" />
                {stats.langGraph} LangGraph
              </span>
              <span className="flex items-center">
                <DollarSign className="w-4 h-4 mr-1 text-green-600" />
                {stats.highConfidence} High Confidence
              </span>
              <span className="flex items-center">
                <Eye className="w-4 h-4 mr-1 text-gray-600" />
                {stats.visible} Visible
              </span>
            </div>
          </div>
          
          {/* View Mode Toggle */}
          <div className="mt-4 sm:mt-0 flex items-center space-x-2">
            <div className="flex rounded-lg border border-gray-300">
              <button
                onClick={() => setViewMode('grid')}
                className={`p-2 rounded-l-lg ${
                  viewMode === 'grid' 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-white text-gray-600 hover:bg-gray-50'
                }`}
              >
                <Grid className="w-4 h-4" />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`p-2 rounded-r-lg ${
                  viewMode === 'list' 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-white text-gray-600 hover:bg-gray-50'
                }`}
              >
                <List className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="flex flex-col sm:flex-row sm:items-center space-y-3 sm:space-y-0 sm:space-x-4">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search listings..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Sort */}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="newest">Newest First</option>
            <option value="oldest">Oldest First</option>
            <option value="price-high">Price: High to Low</option>
            <option value="price-low">Price: Low to High</option>
            <option value="confidence">Confidence: High to Low</option>
            <option value="title">Title: A to Z</option>
          </select>

          {/* Filter */}
          <select
            value={filterBy}
            onChange={(e) => setFilterBy(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">All Listings</option>
            <option value="langgraph">LangGraph Only</option>
            <option value="legacy">Legacy Only</option>
            <option value="high-confidence">High Confidence</option>
            <option value="visible">Visible Only</option>
            <option value="hidden">Hidden Only</option>
          </select>
        </div>
      </div>

      {/* Listings Grid/List */}
      {filteredAndSortedListings.length === 0 ? (
        <div className="text-center py-8">
          <Filter className="mx-auto h-8 w-8 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No matching listings</h3>
          <p className="mt-1 text-sm text-gray-500">
            Try adjusting your search or filter criteria.
          </p>
        </div>
      ) : (
        <div className={
          viewMode === 'grid'
            ? 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6'
            : 'space-y-4'
        }>
          {filteredAndSortedListings.map((listing, index) => (
            <div key={listing.id || index} className={viewMode === 'list' ? 'w-full' : ''}>
              <ListingCard
                listing={listing}
                onEdit={onEdit}
                onToggleVisibility={onToggleVisibility}
                onCopy={onCopy}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ListingGrid; 