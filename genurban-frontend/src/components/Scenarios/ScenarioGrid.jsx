// src/components/Scenarios/ScenarioGrid.jsx
import React from "react";

export default function ScenarioGrid({ scenarios = [], onSelect }) {
  if (!scenarios || scenarios.length === 0) {
    return (
      <div className="card p-6 text-center text-gray-500">
        No scenarios generated yet.
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {scenarios.map((s, idx) => (
        <div
          key={s.id || idx}
          onClick={() => onSelect?.(s)}
          className="card p-5 hover:shadow-soft cursor-pointer transition-all"
        >
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-gray-800">
              {s.title || s.name || "Scenario"}
            </h3>
            <span className="text-xs text-gray-500">
              {s.year || s.timeframe || "Future"}
            </span>
          </div>

          {s.summary || s.description ? (
            <p className="text-sm text-gray-600 mt-2">
              {s.summary || s.description}
            </p>
          ) : (
            <p className="text-sm text-gray-400 mt-2">No summary available.</p>
          )}

          {s.metrics && (
            <div className="mt-3 text-xs text-gray-500 space-y-1">
              <p>Urban Density: {s.metrics.urban_density || "—"}</p>
              <p>Vegetation: {s.metrics.vegetation_cover || "—"}</p>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
