// src/components/Layout/Sidebar.jsx
import LocationSearch from '../Search/LocationSearch'
import AnalysisPanel from '../Analysis/AnalysisPanel'

const Sidebar = ({ 
  currentLocation, 
  setCurrentLocation, 
  setUrbanData, 
  setScenarios, 
  setSelectedScenario,
  activeView,
  setActiveView,
  loading,
  setLoading
}) => {
  return (
    <div className="h-full bg-white border-r border-gray-200 flex flex-col">
      {/* Navigation */}
      <div className="p-6 border-b border-gray-200">
        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
            Navigation
          </h3>
          {[ 
            { id: 'analysis', label: 'Scenario Analysis', icon: '📊' },
            { id: 'scenarios', label: 'My Scenarios', icon: '🗂️' },
            { id: 'data', label: 'Data Library', icon: '📁' },
            { id: 'models', label: 'AI Models', icon: '🤖' }
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveView(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors ${
                activeView === item.id 
                  ? 'bg-blue-50 text-blue-700 border border-blue-200' 
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <span className="text-lg">{item.icon}</span>
              <span className="font-medium">{item.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-6 space-y-6">
          {/* Location Search */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">
              Location
            </h3>
            <LocationSearch
              currentLocation={currentLocation}
              setCurrentLocation={setCurrentLocation}
              setUrbanData={setUrbanData}
              loading={loading}
              setLoading={setLoading}
            />
          </div>

          {/* Analysis Panel */}
          {currentLocation && (
            <AnalysisPanel
              currentLocation={currentLocation}
              setUrbanData={setUrbanData}           // <-- forwarded
              setScenarios={setScenarios}
              setSelectedScenario={setSelectedScenario}
              loading={loading}
              setLoading={setLoading}
            />
          )}
        </div>
      </div>
    </div>
  )
}

export default Sidebar
