import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  TrendingUp, 
  Clock, 
  CheckCircle, 
  AlertTriangle,
  Star,
  DollarSign,
  Image,
  BarChart3,
  Zap
} from 'lucide-react';

const Dashboard = ({ listings = [], isLoading = false }) => {
  const [stats, setStats] = useState({
    total: 0,
    langGraph: 0,
    legacy: 0,
    successful: 0,
    failed: 0,
    avgConfidence: 0,
    avgPrice: 0,
    avgProcessingTime: 0,
    recentActivity: []
  });

  useEffect(() => {
    if (listings.length === 0) {
      setStats({
        total: 0,
        langGraph: 0,
        legacy: 0,
        successful: 0,
        failed: 0,
        avgConfidence: 0,
        avgPrice: 0,
        avgProcessingTime: 0,
        recentActivity: []
      });
      return;
    }

    const total = listings.length;
    const langGraphCount = listings.filter(l => 
      l.analysis_source?.includes('LANGGRAPH') || 
      l.workflow_type?.includes('LANGGRAPH')
    ).length;
    const successful = listings.filter(l => l.confidence && l.confidence > 0.5).length;
    const failed = total - successful;
    
    const avgConfidence = listings.reduce((sum, l) => sum + (l.confidence || 0), 0) / total;
    const avgPrice = listings.reduce((sum, l) => sum + (parseFloat(l.price) || 0), 0) / total;
    const avgProcessingTime = listings.reduce((sum, l) => sum + (l.processing_time || 0), 0) / total;
    
    // Get recent activity (last 10 items, sorted by creation time)
    const recentActivity = [...listings]
      .sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0))
      .slice(0, 10)
      .map(item => ({
        id: item.id,
        title: item.title || 'Untitled',
        timestamp: item.created_at,
        type: item.analysis_source?.includes('LANGGRAPH') ? 'langgraph' : 'legacy',
        success: (item.confidence || 0) > 0.5,
        confidence: item.confidence,
        price: item.price,
        processing_time: item.processing_time
      }));

    setStats({
      total,
      langGraph: langGraphCount,
      legacy: total - langGraphCount,
      successful,
      failed,
      avgConfidence,
      avgPrice,
      avgProcessingTime,
      recentActivity
    });
  }, [listings]);

  const formatTime = (timestamp) => {
    if (!timestamp) return 'Unknown';
    const date = new Date(timestamp);
    const now = new Date();
    const diff = Math.floor((now - date) / 1000);
    
    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600">Loading dashboard...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold flex items-center">
              <Activity className="w-6 h-6 mr-2" />
              LangGraph Analytics Dashboard
            </h1>
            <p className="mt-1 text-blue-100">
              AI-powered furniture analysis insights and performance metrics
            </p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold">{stats.total}</div>
            <div className="text-blue-100">Total Listings</div>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* LangGraph Listings */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">LangGraph AI</p>
              <p className="text-2xl font-bold text-blue-600">{stats.langGraph}</p>
            </div>
            <div className="h-12 w-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <Star className="h-6 w-6 text-blue-600" />
            </div>
          </div>
          <div className="mt-4">
            <div className="flex items-center text-sm">
              <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
              <span className="text-green-600 font-medium">
                {stats.total > 0 ? Math.round((stats.langGraph / stats.total) * 100) : 0}%
              </span>
              <span className="text-gray-600 ml-1">of total</span>
            </div>
          </div>
        </div>

        {/* Success Rate */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Success Rate</p>
              <p className="text-2xl font-bold text-green-600">
                {stats.total > 0 ? Math.round((stats.successful / stats.total) * 100) : 0}%
              </p>
            </div>
            <div className="h-12 w-12 bg-green-100 rounded-lg flex items-center justify-center">
              <CheckCircle className="h-6 w-6 text-green-600" />
            </div>
          </div>
          <div className="mt-4">
            <div className="flex items-center text-sm">
              <span className="text-gray-600">
                {stats.successful} successful, {stats.failed} failed
              </span>
            </div>
          </div>
        </div>

        {/* Average Confidence */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Avg Confidence</p>
              <p className="text-2xl font-bold text-purple-600">
                {Math.round(stats.avgConfidence * 100)}%
              </p>
            </div>
            <div className="h-12 w-12 bg-purple-100 rounded-lg flex items-center justify-center">
              <BarChart3 className="h-6 w-6 text-purple-600" />
            </div>
          </div>
          <div className="mt-4">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-purple-600 h-2 rounded-full"
                style={{ width: `${stats.avgConfidence * 100}%` }}
              />
            </div>
          </div>
        </div>

        {/* Average Price */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Avg Price</p>
              <p className="text-2xl font-bold text-orange-600">
                ${Math.round(stats.avgPrice)}
              </p>
            </div>
            <div className="h-12 w-12 bg-orange-100 rounded-lg flex items-center justify-center">
              <DollarSign className="h-6 w-6 text-orange-600" />
            </div>
          </div>
          <div className="mt-4">
            <div className="flex items-center text-sm">
              <Clock className="h-4 w-4 text-gray-500 mr-1" />
              <span className="text-gray-600">
                ~{stats.avgProcessingTime.toFixed(1)}s avg processing
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* System Performance */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Zap className="w-5 h-5 mr-2 text-yellow-600" />
            System Performance
          </h3>
          
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">LangGraph Usage</span>
              <div className="flex items-center">
                <div className="w-32 bg-gray-200 rounded-full h-2 mr-3">
                  <div
                    className="bg-blue-600 h-2 rounded-full"
                    style={{ width: `${stats.total > 0 ? (stats.langGraph / stats.total) * 100 : 0}%` }}
                  />
                </div>
                <span className="text-sm font-medium text-gray-900">
                  {stats.total > 0 ? Math.round((stats.langGraph / stats.total) * 100) : 0}%
                </span>
              </div>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">High Confidence</span>
              <div className="flex items-center">
                <div className="w-32 bg-gray-200 rounded-full h-2 mr-3">
                  <div
                    className="bg-green-600 h-2 rounded-full"
                    style={{ 
                      width: `${stats.total > 0 ? (listings.filter(l => (l.confidence || 0) >= 0.8).length / stats.total) * 100 : 0}%` 
                    }}
                  />
                </div>
                <span className="text-sm font-medium text-gray-900">
                  {stats.total > 0 ? Math.round((listings.filter(l => (l.confidence || 0) >= 0.8).length / stats.total) * 100) : 0}%
                </span>
              </div>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Processing Speed</span>
              <div className="flex items-center">
                <div className="w-32 bg-gray-200 rounded-full h-2 mr-3">
                  <div
                    className="bg-purple-600 h-2 rounded-full"
                    style={{ width: `${Math.min(100, Math.max(0, 100 - (stats.avgProcessingTime / 30) * 100))}%` }}
                  />
                </div>
                <span className="text-sm font-medium text-gray-900">
                  {stats.avgProcessingTime.toFixed(1)}s
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Clock className="w-5 h-5 mr-2 text-blue-600" />
            Recent Activity
          </h3>
          
          {stats.recentActivity.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Image className="w-8 h-8 mx-auto mb-2 text-gray-400" />
              <p className="text-sm">No recent activity</p>
            </div>
          ) : (
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {stats.recentActivity.map((activity, index) => (
                <div key={activity.id || index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    {activity.success ? (
                      <CheckCircle className="w-5 h-5 text-green-600" />
                    ) : (
                      <AlertTriangle className="w-5 h-5 text-red-600" />
                    )}
                    <div>
                      <div className="font-medium text-gray-900 text-sm truncate max-w-40">
                        {activity.title}
                      </div>
                      <div className="text-xs text-gray-600">
                        {formatTime(activity.timestamp)} • ${activity.price}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {activity.type === 'langgraph' && (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        <Star className="w-3 h-3 mr-1" />
                        LG
                      </span>
                    )}
                    {activity.confidence && (
                      <span className={`text-xs font-medium px-2 py-1 rounded-full ${
                        activity.confidence >= 0.8 
                          ? 'bg-green-100 text-green-800' 
                          : activity.confidence >= 0.6 
                          ? 'bg-yellow-100 text-yellow-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {Math.round(activity.confidence * 100)}%
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* System Status */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">System Status</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex items-center space-x-3">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span className="text-sm text-gray-700">LangGraph API Connected</span>
          </div>
          <div className="flex items-center space-x-3">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span className="text-sm text-gray-700">OpenAI Integration Active</span>
          </div>
          <div className="flex items-center space-x-3">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span className="text-sm text-gray-700">Gemini Pricing Available</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard; 