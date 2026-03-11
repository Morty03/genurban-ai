// src/components/Layout/MainContent.jsx
import React from "react";
import ScenarioGrid from "../Scenarios/ScenarioGrid";
import ScenarioDetail from "../Scenarios/ScenarioDetail";

function MetricCard({ title, value, trend, desc }) {
  const up = trend > 0;
  const trendText = trend === null || trend === undefined ? "—" : `${trend > 0 ? "+" : ""}${(trend * 100).toFixed(2)}%`;
  return (
    <div className="card p-4">
      <div className="flex items-start justify-between">
        <div>
          <div className="text-xs text-gray-500">{title}</div>
          <div className="mt-2 text-xl font-semibold text-gray-900">{value}</div>
          {desc && <div className="text-xs text-gray-500 mt-1">{desc}</div>}
        </div>
        <div className="text-sm text-right">
          <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs ${up ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
            <span className="mr-2">{up ? "▲" : "▼"}</span>
            <span>{trendText}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function MainContent({
  urbanData,
  scenarios = [],
  selectedScenario,
  setSelectedScenario,
  currentLocation,
  activeView,
  loading,
}) {
  const safePercent = (v) => {
    if (v === null || v === undefined || isNaN(v)) return "—";
    if (v <= 1 && v >= 0) return `${(v * 100).toFixed(1)}%`;
    return String(v);
  };

  const getMetric = (key) => {
    if (!urbanData) return { value: "—", trend: null, desc: "" };
    const maybe = urbanData.metrics?.[key] || urbanData?.raw?.[key] || urbanData?.[key] || null;
    if (!maybe) return { value: "—", trend: null, desc: "" };

    const mean = maybe.mean ?? maybe.score ?? maybe.value ?? null;
    const trend = maybe.trend ?? maybe.trend_pct ?? null;
    const desc = maybe.description ?? maybe.summary ?? "";
    return { value: safePercent(mean), trend, desc };
  };

  const interpretations = urbanData?.interpretation || urbanData?.interpretations || urbanData?.analysis?.interpretation || null;
  const recommendations = urbanData?.recommendations || urbanData?.suggestions || urbanData?.tips || null;

  const RenderScenariosArea = () => {
    if (selectedScenario) {
      return <ScenarioDetail scenario={selectedScenario} onBack={() => setSelectedScenario(null)} />;
    }

    if (ScenarioGrid) {
      return <ScenarioGrid scenarios={scenarios} onSelect={setSelectedScenario} />;
    }

    // final fallback UI
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {(!scenarios || scenarios.length === 0) ? (
          <div className="card p-6 text-center text-gray-500">No scenarios found. Run analysis to generate scenarios.</div>
        ) : scenarios.map((s) => (
          <div key={s.id || s.title} className="card p-4 hover:shadow-soft cursor-pointer" onClick={() => setSelectedScenario?.(s)}>
            <div className="flex items-center justify-between">
              <div>
                <div className="font-semibold text-gray-800">{s.title || s.name || "Untitled"}</div>
                <div className="text-xs text-gray-500 mt-1">{s.summary || s.description || ""}</div>
              </div>
              <div className="text-xs text-gray-400">{s.timeframe || s.year || ""}</div>
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <main className="p-6 min-h-screen">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-lg font-semibold text-gray-800">
            {activeView === "analysis" ? "Analysis Overview" : activeView === "scenarios" ? "Scenarios" : activeView === "data" ? "Data Library" : "GenUrban"}
          </h1>
          <div className="text-sm text-gray-500">{currentLocation ? `${currentLocation.name || currentLocation.display_name || ''}` : "No location selected"}</div>
        </div>

        {activeView === "analysis" && (
          <section>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <MetricCard title="Urban Density" {...getMetric("urban_density")} />
              <MetricCard title="Vegetation Cover" {...getMetric("vegetation_cover")} />
              <MetricCard title="Built-up Area" {...getMetric("built_up_area")} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              <div className="lg:col-span-2 card p-4">
                <h3 className="text-sm font-semibold mb-2">Interpretation</h3>
                {!interpretations ? (
                  <p className="text-sm text-gray-500">No interpretation available. Run an analysis to generate insights.</p>
                ) : (
                  <div className="space-y-3">
                    {Object.entries(interpretations).map(([k, v]) => (
                      <div key={k} className="p-3 rounded border border-gray-100 bg-white">
                        <div className="flex items-start justify-between">
                          <div>
                            <div className="text-sm font-medium text-gray-800 capitalize">{k.replace(/_/g, " ")}</div>
                            {v?.level && <div className="text-xs text-gray-500 mt-1">{v.level} — {v.description || ""}</div>}
                            {!v?.level && v?.description && <div className="text-xs text-gray-500 mt-1">{v.description}</div>}
                          </div>
                          <div className="text-xs text-gray-400">{v?.score ? (typeof v.score === "number" ? (v.score * 100).toFixed(0) + "%" : v.score) : ""}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <aside className="card p-4">
                <h3 className="text-sm font-semibold mb-2">Recommendations</h3>
                {Array.isArray(recommendations) && recommendations.length > 0 ? (
                  <ul className="list-disc list-inside text-sm text-gray-700 space-y-2">
                    {recommendations.map((r, idx) => <li key={idx}>{r}</li>)}
                  </ul>
                ) : (
                  <p className="text-sm text-gray-500">No recommendations available.</p>
                )}

                <div className="mt-4">
                  <button className="btn-primary">Export Report</button>
                </div>
              </aside>
            </div>

            <details className="mt-6 p-3 bg-gray-50 border rounded">
              <summary className="cursor-pointer text-sm">Debug: raw analysis payload</summary>
              <pre className="text-xs overflow-auto mt-2 max-h-64">{JSON.stringify(urbanData, null, 2)}</pre>
            </details>
          </section>
        )}

        {activeView === "scenarios" && (
          <section>
            <div className="mb-4 flex items-center justify-between">
              <div>
                <h2 className="text-base font-semibold">Scenarios</h2>
                <p className="text-sm text-gray-500">Browse or select a scenario to view details.</p>
              </div>
              <div>
                <button className="btn-primary" onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}>Generate New</button>
              </div>
            </div>

            <RenderScenariosArea />

            <details className="mt-6 p-3 bg-gray-50 border rounded">
              <summary className="cursor-pointer text-sm">Debug: raw scenarios payload</summary>
              <pre className="text-xs overflow-auto mt-2 max-h-64">{JSON.stringify(scenarios, null, 2)}</pre>
            </details>
          </section>
        )}

        {activeView === "data" && (
          <section>
            <div className="card p-6">
              <h3 className="text-base font-semibold">Data Library</h3>
              <p className="text-sm text-gray-500">Data assets and layers will appear here.</p>
            </div>
          </section>
        )}
      </div>
    </main>
  );
}
