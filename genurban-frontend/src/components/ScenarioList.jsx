// src/components/ScenarioList.jsx
const ScenarioList = ({ scenarios, selectedScenario, onScenarioSelect, className = '' }) => {
  return (
    <div className={`space-y-4 ${className}`}>
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Generated Scenarios</h3>
        <span className="text-sm text-gray-500 bg-gray-100 px-3 py-1 rounded-full">
          {scenarios.length} total
        </span>
      </div>

      <div className="space-y-3">
        {scenarios.map((scenario) => (
          <div
            key={scenario.id}
            onClick={() => onScenarioSelect(scenario)}
            className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${
              selectedScenario?.id === scenario.id
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
            }`}
          >
            <div className="flex items-start justify-between mb-2">
              <h4 className="font-semibold text-gray-900 text-sm">{scenario.name}</h4>
              <div className={`w-3 h-3 rounded-full ${
                scenario.climateRisk < 0 ? 'bg-green-500' : 'bg-orange-500'
              }`} />
            </div>
            
            <p className="text-gray-600 text-sm mb-3">{scenario.description}</p>
            
            <div className="grid grid-cols-3 gap-4 text-xs">
              <div className="text-center">
                <div className="text-gray-500">Growth</div>
                <div className="font-semibold text-gray-900">+{scenario.urbanGrowth}%</div>
              </div>
              <div className="text-center">
                <div className="text-gray-500">Vegetation</div>
                <div className={`font-semibold ${
                  scenario.vegetationChange >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {scenario.vegetationChange >= 0 ? '+' : ''}{scenario.vegetationChange}%
                </div>
              </div>
              <div className="text-center">
                <div className="text-gray-500">Risk</div>
                <div className={`font-semibold ${
                  scenario.climateRisk < 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {scenario.climateRisk >= 0 ? '+' : ''}{scenario.climateRisk}%
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {scenarios.length === 0 && (
        <div className="text-center py-8">
          <div className="text-gray-400 mb-2">No scenarios generated yet</div>
          <div className="text-sm text-gray-500">Generate scenarios to see them listed here</div>
        </div>
      )}
    </div>
  )
}

export default ScenarioList