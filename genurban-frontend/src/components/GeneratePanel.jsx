// src/components/GeneratePanel.jsx
import { useState } from 'react'

const GeneratePanel = ({ onGenerate }) => {
  const [parameters, setParameters] = useState({
    density: 50,
    buildingHeight: 'medium',
    landUse: 'mixed',
    sustainability: 75
  })

  const handleGenerate = () => {
    console.log('Generating with parameters:', parameters)
    if (typeof onGenerate === 'function') onGenerate(parameters)
  }

  return (
    <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-2">Generate Urban Scenario</h2>
        <p className="text-gray-600 text-sm">Create urban development scenarios based on adjustable parameters</p>
      </div>

      <div className="space-y-6">
        {/* Population Density */}
        <div>
          <label htmlFor="density" className="flex items-center justify-between text-sm font-medium text-gray-700 mb-3">
            <span>Population Density</span>
            <span className="text-blue-600 font-semibold">{parameters.density}%</span>
          </label>

          <input
            id="density"
            type="range"
            min="0"
            max="100"
            value={parameters.density}
            onChange={(e) => setParameters({ ...parameters, density: Number(e.target.value) })}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={parameters.density}
            aria-label="Population density"
          />
        </div>

        {/* Building Height */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">Building Height</label>
          <div className="grid grid-cols-3 gap-2">
            {['low', 'medium', 'high'].map((height) => {
              const active = parameters.buildingHeight === height
              return (
                <button
                  key={height}
                  type="button"
                  onClick={() => setParameters({ ...parameters, buildingHeight: height })}
                  aria-pressed={active}
                  className={[
                    'px-3 py-2 text-sm rounded-xl border transition-all duration-200 font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
                    active
                      ? 'border-blue-500 bg-blue-50 text-blue-700 shadow-sm'
                      : 'border-gray-300 text-gray-600 hover:border-gray-400 hover:bg-gray-50'
                  ].join(' ')}
                >
                  {height.charAt(0).toUpperCase() + height.slice(1)}
                </button>
              )
            })}
          </div>
        </div>

        {/* Land Use */}
        <div>
          <label htmlFor="landuse" className="block text-sm font-medium text-gray-700 mb-3">Land Use Type</label>
          <select
            id="landuse"
            value={parameters.landUse}
            onChange={(e) => setParameters({ ...parameters, landUse: e.target.value })}
            className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl text-gray-900 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
            aria-label="Land use type"
          >
            <option value="mixed">Mixed Use</option>
            <option value="residential">Residential</option>
            <option value="commercial">Commercial</option>
            <option value="industrial">Industrial</option>
          </select>
        </div>

        {/* Sustainability */}
        <div>
          <label htmlFor="sustainability" className="flex items-center justify-between text-sm font-medium text-gray-700 mb-3">
            <span>Sustainability Score</span>
            <span className="text-green-600 font-semibold">{parameters.sustainability}%</span>
          </label>

          <input
            id="sustainability"
            type="range"
            min="0"
            max="100"
            value={parameters.sustainability}
            onChange={(e) => setParameters({ ...parameters, sustainability: Number(e.target.value) })}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={parameters.sustainability}
            aria-label="Sustainability score"
          />
        </div>
      </div>

      <div className="mt-6 pt-6 border-t border-gray-200">
        <button
          type="button"
          onClick={handleGenerate}
          className="w-full inline-flex items-center justify-center bg-blue-600 text-white py-3 px-4 rounded-xl font-semibold hover:bg-blue-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 shadow-sm"
        >
          Generate Scenario
        </button>
      </div>

      {/* Preview Summary */}
      <div className="mt-4 p-4 bg-gray-50 rounded-xl border border-gray-200">
        <h4 className="text-sm font-medium text-gray-700 mb-2">Scenario Preview</h4>
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div>
            <span className="text-gray-500">Density:</span>
            <span className="text-gray-900 font-medium ml-1">{parameters.density}%</span>
          </div>
          <div>
            <span className="text-gray-500">Height:</span>
            <span className="text-gray-900 font-medium ml-1 capitalize">{parameters.buildingHeight}</span>
          </div>
          <div>
            <span className="text-gray-500">Land Use:</span>
            <span className="text-gray-900 font-medium ml-1 capitalize">{parameters.landUse}</span>
          </div>
          <div>
            <span className="text-gray-500">Sustainability:</span>
            <span className="text-green-600 font-medium ml-1">{parameters.sustainability}%</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default GeneratePanel