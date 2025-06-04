import React from 'react'
import { Link } from 'react-router-dom'
import { Zap, Upload, Edit, ArrowRight, Star, Clock, CheckCircle, Split } from 'lucide-react'

const HomePage = () => {
  const features = [
    {
      icon: Zap,
      title: 'AI Auto-Fill',
      description: 'Upload photos → AI fills ALL fields automatically (single item)',
      path: '/auto-fill',
      featured: true,
      time: '3-5 seconds',
      benefits: ['Title, Price, Condition', 'Category & Description', 'Ready to post instantly']
    },
    {
      icon: Split,
      title: 'Multi-Item Classifier',
      description: 'Upload photos of DIFFERENT furniture → Get separate listings',
      path: '/multi-item',
      featured: true,
      time: '5-10 seconds',
      benefits: ['Auto-groups similar items', 'Multiple separate listings', 'Bulk save/export']
    },
    {
      icon: Upload,
      title: 'Bulk Classification',
      description: 'Upload multiple photos and group similar furniture',
      path: '/classify',
      time: '5-10 seconds',
      benefits: ['Group similar items', 'Generate multiple listings', 'Export to CSV']
    },
    {
      icon: Edit,
      title: 'Manual Create',
      description: 'Traditional form with AI assistance',
      path: '/manual',
      time: '2-3 minutes',
      benefits: ['Full control', 'AI description help', 'Image processing']
    }
  ]

  const steps = [
    { step: 1, title: 'Upload Photos', desc: 'Drag & drop furniture images' },
    { step: 2, title: 'AI Analysis', desc: 'AI detects condition, style & pricing' },
    { step: 3, title: 'Auto-Fill', desc: 'All fields populated automatically' },
    { step: 4, title: 'Ready!', desc: 'Edit if needed, then export or save' }
  ]

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <div className="hero-gradient text-white py-20">
        <div className="max-w-6xl mx-auto px-4 text-center">
          <div className="mb-8">
            <span className="text-6xl mb-4 block">🤖</span>
            <h1 className="text-5xl md:text-6xl font-bold mb-6">
              AI Furniture Listing Agent
            </h1>
            <p className="text-xl md:text-2xl mb-4 text-blue-100">
              Upload photos → AI fills ALL fields → Ready to post!
            </p>
            <p className="text-lg text-blue-200 mb-8">
              Zero manual typing required. AI handles title, price, condition, category & description.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Link
              to="/auto-fill"
              className="bg-yellow-400 hover:bg-yellow-500 text-black font-bold py-4 px-8 rounded-xl text-lg transition-all transform hover:scale-105 shadow-xl flex items-center"
            >
              <Zap className="h-5 w-5 mr-2" />
              Try AI Magic Now!
              <ArrowRight className="h-5 w-5 ml-2" />
            </Link>
            <div className="flex items-center text-blue-200">
              <Star className="h-4 w-4 mr-1" />
              <span className="text-sm">No signup required • Instant results</span>
            </div>
          </div>
        </div>
      </div>

      {/* Features Grid */}
      <div className="max-w-6xl mx-auto py-16 px-4">
        <h2 className="text-3xl font-bold text-center mb-12 text-gray-900">
          Choose Your Workflow
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {features.map(({ icon: Icon, title, description, path, featured, time, benefits }) => (
            <Link
              key={path}
              to={path}
              className={`
                group relative p-8 rounded-2xl transition-all duration-300 transform hover:scale-105
                ${featured 
                  ? 'bg-gradient-to-br from-blue-500 via-purple-600 to-blue-700 text-white shadow-2xl' 
                  : 'bg-white border border-gray-200 hover:shadow-xl'
                }
              `}
            >
              {featured && (
                <div className="absolute -top-3 -right-3 bg-yellow-400 text-black px-3 py-1 rounded-full text-sm font-bold">
                  🔥 HOT!
                </div>
              )}
              
              <div className={`text-4xl mb-4 ${featured ? 'text-white' : 'text-blue-500'}`}>
                <Icon className="h-12 w-12" />
              </div>
              
              <h3 className={`text-2xl font-bold mb-3 ${featured ? 'text-white' : 'text-gray-900'}`}>
                {title}
              </h3>
              
              <p className={`mb-4 ${featured ? 'text-blue-100' : 'text-gray-600'}`}>
                {description}
              </p>

              <div className={`flex items-center mb-4 text-sm ${featured ? 'text-blue-200' : 'text-gray-500'}`}>
                <Clock className="h-4 w-4 mr-1" />
                <span>{time}</span>
              </div>

              <div className={`space-y-2 ${featured ? 'text-blue-100' : 'text-gray-600'}`}>
                {benefits.map((benefit, idx) => (
                  <div key={idx} className="flex items-center text-sm">
                    <CheckCircle className={`h-4 w-4 mr-2 ${featured ? 'text-green-300' : 'text-green-500'}`} />
                    <span>{benefit}</span>
                  </div>
                ))}
              </div>

              {featured && (
                <div className="mt-6 bg-yellow-400 text-black px-4 py-2 rounded-lg font-bold text-center group-hover:bg-yellow-300 transition-colors">
                  Start Here! ⚡
                </div>
              )}
            </Link>
          ))}
        </div>
      </div>

      {/* How It Works */}
      <div className="bg-gradient-to-r from-gray-50 to-blue-50 py-16">
        <div className="max-w-6xl mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12 text-gray-900">
            How AI Auto-Fill Works
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            {steps.map(({ step, title, desc }) => (
              <div key={step} className="text-center">
                <div className={`
                  w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4 text-xl font-bold text-white
                  ${step === 4 ? 'bg-green-500' : 'bg-blue-500'}
                `}>
                  {step === 4 ? '✓' : step}
                </div>
                <h4 className="font-semibold mb-2 text-gray-900">{title}</h4>
                <p className="text-sm text-gray-600">{desc}</p>
              </div>
            ))}
          </div>

          <div className="text-center mt-12">
            <Link
              to="/auto-fill"
              className="inline-flex items-center bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg transition-colors"
            >
              <Zap className="h-5 w-5 mr-2" />
              Experience the Magic
            </Link>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="py-16 bg-white">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div>
              <div className="text-4xl font-bold text-blue-600 mb-2">3-5s</div>
              <div className="text-gray-600">Average AI processing time</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-green-600 mb-2">95%</div>
              <div className="text-gray-600">Accuracy for furniture detection</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-purple-600 mb-2">0</div>
              <div className="text-gray-600">Manual typing required</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default HomePage
