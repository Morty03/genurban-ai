// src/components/Layout.jsx
import { useState } from 'react'
import MapView from './MapView'
import GeneratePanel from './GeneratePanel'
import PlaceSearch from './PlaceSearch'
import ScenarioList from './ScenarioList'
import ScenarioUpload from './ScenarioUpload'

const Layout = () => {
  const [selectedLocation, setSelectedLocation] = useState(null)
  const [scenarios, setScenarios] = useState([])
  const [selectedScenario, setSelectedScenario] = useState(null)
  const [activeTab, setActiveTab] = useState('analysis')

  const handleGenerate = (parameters) => {
    // Generate mock scenarios based on parameters
    const newScenarios = [
      {
        id: 1,
        name: `Sustainable ${selectedLocation?.name || 'Location'} 2030`,
        description: 'Balanced urban development with green infrastructure',
        urbanGrowth: '12.5',
        vegetationChange: '8.2',
        climateRisk: '-15.3',
        features: ['Green corridors', 'Mixed-use zones', 'Public transit']
      },
      {
        id: 2,
        name: `Compact ${selectedLocation?.name || 'Location'} Development`,
        description: 'High-density urban expansion',
        urbanGrowth: '24.7',
        vegetationChange: '-12.1',
        climateRisk: '18.5',
        features: ['Vertical development', 'Transit-oriented', 'Smart infrastructure']
      }
    ]
    setScenarios(newScenarios)
    setSelectedScenario(newScenarios[0])
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Main Content Grid */}
      <div className="max-w-7xl mx-auto p-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Sidebar - Controls */}
          <div className="lg:col-span-1 space-y-6">
            {/* Location Search */}
            <div className="bg-white rounded-2xl border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Location Search</h2>
              <PlaceSearch onLocationSelect={setSelectedLocation} />
            </div>

            {/* Analysis Tabs */}
            <div className="bg-white rounded-2xl border border-gray-200 p-6">
              <div className="flex border-b border-gray-200 mb-4">
                {['analysis', 'scenarios', 'upload'].map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`flex-1 py-2 text-sm font-medium transition-colors ${
                      activeTab === tab
                        ? 'text-blue-600 border-b-2 border-blue-600'
                        : 'text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    {tab.charAt(0).toUpperCase() + tab.slice(1)}
                  </button>
                ))}
              </div>

              {activeTab === 'analysis' && (
                <GeneratePanel onGenerate={handleGenerate} />
              )}

              {activeTab === 'scenarios' && (
                <ScenarioList
                  scenarios={scenarios}
                  selectedScenario={selectedScenario}
                  onScenarioSelect={setSelectedScenario}
                />
              )}

              {activeTab === 'upload' && (
                <ScenarioUpload onUpload={(file) => console.log('File uploaded:', file)} />
              )}
            </div>
          </div>

          {/* Main Map Area */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-2xl border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900">
                  {selectedLocation ? `Map View - ${selectedLocation.name}` : 'Map View'}
                </h2>
                {selectedLocation && (
                  <div className="text-sm text-green-600 bg-green-50 px-3 py-1 rounded-full">
                    Location Selected
                  </div>
                )}
              </div>
              
              <div className="h-96 rounded-xl overflow-hidden">
                <MapView selected={selectedLocation} />
              </div>
            </div>

            {/* Selected Scenario Details */}
            {selectedScenario && (
              <div className="mt-6 bg-white rounded-2xl border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Scenario Analysis: {selectedScenario.name}
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-medium text-gray-700 mb-3">Key Features</h4>
                    <ul className="space-y-2">
                      {selectedScenario.features.map((feature, index) => (
                        <li key={index} className="flex items-center gap-3 text-sm text-gray-600">
                          <div className="w-2 h-2 bg-blue-500 rounded-full" />
                          {feature}
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-700 mb-3">Impact Metrics</h4>
                    <div className="space-y-4">
                      <div>
                        <div className="flex justify-between text-sm mb-2">
                          <span className="text-gray-600">Urban Density Change</span>
                          <span className="font-semibold text-gray-900">+{selectedScenario.urbanGrowth}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-blue-500 h-2 rounded-full" 
                            style={{ width: `${Math.min(selectedScenario.urbanGrowth, 100)}%` }} 
                          />
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between text-sm mb-2">
                          <span className="text-gray-600">Climate Resilience</span>
                          <span className={`font-semibold ${
                            selectedScenario.climateRisk < 0 ? 'text-green-600' : 'text-red-600'
                          }`}>
                            {selectedScenario.climateRisk < 0 ? '+' : ''}{-selectedScenario.climateRisk}%
                          </span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className={`h-2 rounded-full ${
                              selectedScenario.climateRisk < 0 ? 'bg-green-500' : 'bg-red-500'
                            }`} 
                            style={{ width: `${Math.min(Math.abs(selectedScenario.climateRisk), 100)}%` }} 
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default Layout