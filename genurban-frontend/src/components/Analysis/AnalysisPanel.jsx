// src/components/Analysis/AnalysisPanel.jsx
import { useState } from 'react'
import { urbanAPI, formatUrbanData } from '../../utils/api'

/**
 * createGenerativeSeed(urbanData, parameters)
 * Produces a generative "seed" object (drivers & weights) from analysis interpretation.
 * - urbanData.interpretation is preferred
 * - falls back to metrics if interpretation absent
 *
 * The seed object is intentionally simple and explainable:
 * {
 *   focus: "sustainable" | "compact" | "green_invest" | "infra_first",
 *   weights: { vegetation: 0.3, built_up: 0.4, density: 0.3 },
 *   actions: [ "protect_green", "increase_infill", "improve_drainage" ],
 *   notes: "string human readable summary"
 * }
 */
function createGenerativeSeed(urbanData, parameters) {
  const seed = {
    focus: parameters.scenarioType || 'balanced',
    weights: { vegetation: 0.33, built_up: 0.33, density: 0.34 },
    actions: [],
    notes: '',
  };

  if (!urbanData) {
    seed.notes = 'No analysis available; using default balanced weights.';
    return seed;
  }

  const interp = urbanData.interpretation || urbanData.interpretations || urbanData?.raw?.interpretation || null;

  // Helper: safe score getter from metrics (0..1)
  const m = (k) => {
    const v = urbanData.metrics?.[k] ?? urbanData?.raw?.[k] ?? urbanData?.[k] ?? null;
    if (!v) return null;
    const mean = v.mean ?? v.score ?? v.value ?? null;
    return typeof mean === 'number' ? mean : null;
  };

  // Use interpretation text levels if available
  if (interp) {
    // example keys: urban_density, vegetation_cover, built_up_area
    const ud = interp.urban_density;
    const veg = interp.vegetation_cover;
    const built = interp.built_up_area;

    // Simple heuristics
    if (ud?.level?.toLowerCase?.().includes('high') || (m('urban_density') && m('urban_density') > 0.6)) {
      seed.actions.push('promote_infill');
      seed.weights.density = 0.5;
      seed.focus = 'compact';
      seed.notes += 'High urban density detected. ';
    }

    if (veg?.level?.toLowerCase?.().includes('low') || (m('vegetation_cover') && m('vegetation_cover') < 0.35)) {
      seed.actions.push('protect_green', 'urban_tree_planting');
      seed.weights.vegetation = 0.5;
      seed.focus = 'green_invest';
      seed.notes += 'Low vegetation cover — prioritize green interventions. ';
    }

    if (built?.description?.toLowerCase?.().includes('impervious') || (m('built_up_area') && m('built_up_area') > 0.45)) {
      seed.actions.push('sustainable_draining', 'reduce_impervious');
      seed.weights.built_up = 0.5;
      seed.notes += 'High built-up / impervious surfaces detected. ';
    }

    // if multiple flags exist, blend weights instead of overwrite
    // Normalize weights so they sum to 1
    const values = Object.values(seed.weights);
    const sum = values.reduce((a, b) => a + b, 0) || 1;
    Object.keys(seed.weights).forEach(k => { seed.weights[k] = +(seed.weights[k] / sum).toFixed(3); });
  } else {
    // fallback to metrics only
    const urban = m('urban_density');
    const vegetation = m('vegetation_cover');
    const builtup = m('built_up_area');

    // map 0..1 metrics into weights (if present)
    if (urban != null || vegetation != null || builtup != null) {
      const vals = {
        density: urban ?? 0.33,
        vegetation: (1 - (vegetation ?? 0.33)), // lower vegetation -> stronger weight to protect
        built_up: builtup ?? 0.33,
      };
      const total = vals.density + vals.vegetation + vals.built_up || 1;
      seed.weights = {
        vegetation: +(vals.vegetation / total).toFixed(3),
        built_up: +(vals.built_up / total).toFixed(3),
        density: +(vals.density / total).toFixed(3),
      };
      seed.notes = 'Seed derived from raw metrics.';
      if (vals.vegetation / total > 0.45) seed.actions.push('protect_green');
      if (vals.density / total > 0.45) seed.actions.push('promote_infill');
      if (vals.built_up / total > 0.45) seed.actions.push('reduce_impervious');
    } else {
      seed.notes = 'No metrics available; default seed used.';
    }
  }

  // Respect user-selected density preference (nudging)
  if (parameters.density === 'low') {
    seed.actions.push('limit_sprawl');
    seed.weights.density = +(seed.weights.density * 0.8).toFixed(3);
    seed.weights.vegetation = +(seed.weights.vegetation * 1.2).toFixed(3);
  } else if (parameters.density === 'high') {
    seed.actions.push('allow_higher_density');
    seed.weights.density = +(seed.weights.density * 1.2).toFixed(3);
  }

  // Normalize weights again
  const total2 = Object.values(seed.weights).reduce((a, b) => a + b, 0) || 1;
  Object.keys(seed.weights).forEach(k => { seed.weights[k] = +(seed.weights[k] / total2).toFixed(3); });

  // Ensure uniqueness in actions
  seed.actions = Array.from(new Set(seed.actions));

  return seed;
}

const AnalysisPanel = ({
  currentLocation,
  setUrbanData,
  setScenarios,
  setSelectedScenario,
  loading,
  setLoading
}) => {
  const [isLoading, setIsLoading] = useState(false)
  const [analysisLoading, setAnalysisLoading] = useState(false)
  const [errorMsg, setErrorMsg] = useState(null)
  const [useInterpretation, setUseInterpretation] = useState(true) // new toggle
  const [lastSeed, setLastSeed] = useState(null)

  const [parameters, setParameters] = useState({
    timeFrame: '10',
    scenarioType: 'balanced',
    density: 'medium',
    includeClimate: true,
    includeInfrastructure: true
  })

  // Run analysis endpoint and normalize
  const handleRunAnalysis = async () => {
    if (!currentLocation) return
    setErrorMsg(null)
    setAnalysisLoading(true)
    setLoading?.(true)
    try {
      const payload = {
        lat: currentLocation.lat || currentLocation.latitude,
        lng: currentLocation.lng || currentLocation.longitude,
        years: Number(parameters.timeFrame) || 10,
        include_climate: !!parameters.includeClimate,
        include_infra: !!parameters.includeInfrastructure,
      }
      const res = await urbanAPI.analyzeUrbanMorphology(payload)
      const normalized = formatUrbanData(res)
      setUrbanData(normalized)
      return normalized
    } catch (err) {
      console.error('Analysis failed:', err)
      setErrorMsg(err?.message || 'Analysis failed')
      return null
    } finally {
      setAnalysisLoading(false)
      setLoading?.(false)
    }
  }

  // Generate scenarios; if useInterpretation=true build seed from urbanData
  const handleGenerateScenarios = async () => {
    setIsLoading(true)
    setErrorMsg(null)

    try {
      // Ensure we have analysis data first (run if absent)
      let urbanData = null
      if (!useInterpretation) {
        // user explicitly doesn't want interpretation-based seed; use basic payload
        // We'll still run analysis optionally for consistency but not required
        urbanData = null
      } else {
        // run analysis to get latest interpretations (always helpful)
        urbanData = await handleRunAnalysis()
      }

      // Build payload
      const payload = {
        location: currentLocation,
        scenario_type: parameters.scenarioType,
        time_frame: parameters.timeFrame,
        density: parameters.density,
        include_climate: parameters.includeClimate,
        include_infrastructure: parameters.includeInfrastructure,
      }

      // when generative requested, create seed and attach
      if (useInterpretation) {
        const seed = createGenerativeSeed(urbanData, parameters)
        payload.generative_seed = seed
        setLastSeed(seed) // show preview in UI
      }

      // Call API
      const response = await urbanAPI.generateScenario(payload)
      const scenarios = response?.scenarios || response?.data || response || []
      setScenarios(Array.isArray(scenarios) ? scenarios : [])
      if (Array.isArray(scenarios) && scenarios.length > 0) {
        setSelectedScenario(scenarios[0])
      }
    } catch (error) {
      console.error('Scenario generation failed:', error)
      setErrorMsg(error?.message || 'Scenario generation failed')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">Analysis Parameters</h3>

      <div className="space-y-3">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Time Horizon (Years)</label>
          <select
            value={parameters.timeFrame}
            onChange={(e) => setParameters({...parameters, timeFrame: e.target.value})}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
          >
            <option value="5">5 Years</option>
            <option value="10">10 Years</option>
            <option value="15">15 Years</option>
            <option value="20">20 Years</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Development Scenario</label>
          <select
            value={parameters.scenarioType}
            onChange={(e) => setParameters({...parameters, scenarioType: e.target.value})}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
          >
            <option value="sustainable">Sustainable Development</option>
            <option value="compact">Compact City</option>
            <option value="balanced">Balanced Growth</option>
            <option value="rapid">Rapid Urbanization</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Urban Density</label>
          <div className="grid grid-cols-3 gap-2">
            {['low', 'medium', 'high'].map((density) => (
              <button
                key={density}
                onClick={() => setParameters({...parameters, density})}
                className={`p-2 text-xs rounded border transition-colors ${
                  parameters.density === density
                    ? 'bg-blue-100 border-blue-500 text-blue-700'
                    : 'bg-gray-100 border-gray-300 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {density}
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-2">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={parameters.includeClimate}
              onChange={(e) => setParameters({...parameters, includeClimate: e.target.checked})}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="ml-2 text-sm text-gray-700">Climate Impact Analysis</span>
          </label>

          <label className="flex items-center">
            <input
              type="checkbox"
              checked={parameters.includeInfrastructure}
              onChange={(e) => setParameters({...parameters, includeInfrastructure: e.target.checked})}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="ml-2 text-sm text-gray-700">Infrastructure Planning</span>
          </label>
        </div>

        {/* New toggle: generate from interpretation */}
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={useInterpretation}
              onChange={() => setUseInterpretation(!useInterpretation)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-700">Generate from interpretation (recommended)</span>
          </label>
        </div>

        {/* action buttons */}
        <div className="flex gap-2">
          <button
            onClick={handleRunAnalysis}
            disabled={analysisLoading}
            className="flex-1 bg-white border border-gray-300 text-gray-800 py-2.5 rounded-lg font-semibold hover:bg-gray-50 text-sm"
          >
            {analysisLoading ? 'Analyzing…' : 'Run Analysis'}
          </button>

          <button
            onClick={handleGenerateScenarios}
            disabled={isLoading}
            className="flex-1 bg-blue-600 text-white py-2.5 rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50 text-sm"
          >
            {isLoading ? 'Generating…' : 'Generate Scenarios'}
          </button>
        </div>

        {errorMsg && <div className="text-sm text-red-600">{errorMsg}</div>}

        {/* Seed preview */}
        {lastSeed && (
          <div className="mt-3 p-3 bg-gray-50 border rounded text-sm">
            <div className="font-medium mb-2">Generative Seed Preview</div>
            <div className="text-xs text-gray-700 mb-2">{lastSeed.notes}</div>
            <div className="flex gap-3 text-xs">
              <div>Focus: <strong>{lastSeed.focus}</strong></div>
              <div>Actions: <strong>{lastSeed.actions.join(', ') || '—'}</strong></div>
              <div>Weights: <strong>{JSON.stringify(lastSeed.weights)}</strong></div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default AnalysisPanel
// src/components/Layout/Sidebar.jsx