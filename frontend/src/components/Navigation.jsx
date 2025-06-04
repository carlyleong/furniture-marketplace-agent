import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Zap, Upload, Edit, Home } from 'lucide-react'

const Navigation = () => {
  const location = useLocation()
  
  const isActive = (path) => location.pathname === path
  
  const navItems = [
    { path: '/', icon: Home, label: 'Home' },
    { path: '/auto-fill', icon: Zap, label: 'AI Auto-Fill', featured: true },
    { path: '/classify', icon: Upload, label: 'Bulk Classify' },
    { path: '/manual', icon: Edit, label: 'Manual Create' },
  ]

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white shadow-lg border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2 text-xl font-bold">
            <span className="text-2xl">🤖</span>
            <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              Furniture Agent
            </span>
          </Link>

          {/* Navigation Items */}
          <div className="flex items-center space-x-1">
            {navItems.map(({ path, icon: Icon, label, featured }) => (
              <Link
                key={path}
                to={path}
                className={`
                  flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200
                  ${featured 
                    ? isActive(path)
                      ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-white shadow-lg'
                      : 'bg-gradient-to-r from-yellow-400 to-orange-500 text-white hover:shadow-lg hover:scale-105'
                    : isActive(path)
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-600 hover:text-blue-600 hover:bg-gray-50'
                  }
                `}
              >
                <Icon className={`h-4 w-4 ${featured ? 'text-white' : ''}`} />
                <span>{label}</span>
                {featured && !isActive(path) && (
                  <span className="bg-red-500 text-white text-xs px-1.5 py-0.5 rounded-full">
                    NEW!
                  </span>
                )}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </nav>
  )
}

export default Navigation
