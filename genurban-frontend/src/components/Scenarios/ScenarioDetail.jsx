// src/components/Scenarios/ScenarioDetail.jsx
import React from "react";

export default function ScenarioDetail({ scenario, onBack }) {
  if (!scenario) {
    return (
      <div className="card p-6">
        <p className="text-gray-500 text-sm">No scenario selected.</p>
      </div>
    );
  }

  return (
    <div className="card p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-800">
          {scenario.title || scenario.name || "Scenario Details"}
        </h2>

        <button
          onClick={onBack}
          className="text-sm text-blue-600 hover:underline"
        >
          ← Back
        </button>
      </div>

      {scenario.summary || scenario.description ? (
        <p className="text-gray-600 text-sm leading-relaxed">
          {scenario.summary || scenario.description}
        </p>
      ) : (
        <p className="text-gray-500 text-sm">No description available.</p>
      )}

      {scenario.metrics && (
        <div className="p-4 bg-gray-50 border rounded space-y-2">
          <h3 className="text-sm font-semibold text-gray-700">Metrics</h3>

          <ul className="text-sm text-gray-600 space-y-1">
            <li>Urban Density: {scenario.metrics.urban_density || "—"}</li>
            <li>Vegetation Cover: {scenario.metrics.vegetation_cover || "—"}</li>
            <li>Built-up Area: {scenario.metrics.built_up_area || "—"}</li>
          </ul>
        </div>
      )}

      {scenario.recommendations && scenario.recommendations.length > 0 && (
        <div className="p-4 bg-green-50 border border-green-200 rounded">
          <h3 className="text-sm font-semibold text-green-700 mb-2">
            Recommendations
          </h3>

          <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
            {scenario.recommendations.map((r, idx) => (
              <li key={idx}>{r}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
