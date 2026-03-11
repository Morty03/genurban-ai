// src/components/MapView.jsx
import React, { useMemo, useEffect } from "react";
import {
  MapContainer,
  TileLayer,
  ImageOverlay,
  useMap,
  Marker,
  Popup,
  Rectangle
} from "react-leaflet";
import { storageUrl } from "../utils/api";

/**
 * FitToBounds component — fits map to provided Leaflet bounds once.
 * bounds expected: [[south, west], [north, east]]
 */
function FitToBounds({ bounds }) {
  const map = useMap();

  useEffect(() => {
    if (!bounds) return;
    try {
      map.fitBounds(bounds, { maxZoom: 16, padding: [20, 20] });
    } catch (e) {
      console.warn("FitToBounds failed", e);
    }
  }, [map, bounds]);

  return null;
}

/**
 * Floating map controls (top-right)
 * - zoomToBounds: fit to provided bounds
 * - centerOnMarker: fly to marker if lat/lon present (selected)
 * - downloadOverlay: download overlay image if available (opens URL)
 */
function MapControls({ map, bounds, selected, overlayUrl }) {
  if (!map) return null;

  const zoomToBounds = () => {
    if (!bounds) {
      map.setView(map.getCenter(), Math.max(map.getZoom(), 6));
      return;
    }
    try {
      map.fitBounds(bounds, { maxZoom: 16, padding: [24, 24] });
    } catch (e) {
      console.warn("zoomToBounds failed", e);
    }
  };

  const centerOnMarker = () => {
    if (!selected || (!selected.lat && !selected.lon)) {
      map.setView(map.getCenter(), Math.max(map.getZoom(), 6));
      return;
    }
    const lat = Number(selected.lat);
    const lon = Number(selected.lon);
    if (Number.isFinite(lat) && Number.isFinite(lon)) {
      try {
        map.flyTo([lat, lon], 12, { duration: 0.7 });
      } catch (e) {
        map.setView([lat, lon], 12);
      }
    }
  };

  const downloadOverlay = () => {
    if (!overlayUrl) return;
    window.open(overlayUrl, "_blank", "noopener,noreferrer");
  };

  // Light theme button styles
  const btnBase = "inline-flex items-center justify-center gap-2 px-3 py-2 rounded-xl text-sm font-medium transition-all focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2";
  const primary = "bg-blue-600 text-white shadow-sm hover:bg-blue-700 hover:shadow-md";
  const secondary = "bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 hover:border-gray-400";

  return (
    <div
      className="absolute top-4 right-4 z-30 flex flex-col gap-3 pointer-events-auto"
      style={{ width: 200 }}
      aria-hidden={false}
    >
      <div className="bg-white/95 border border-gray-200 rounded-xl p-4 shadow-lg backdrop-blur-sm">
        <div className="text-xs font-semibold text-gray-700 mb-3">Map Controls</div>

        <div className="flex flex-col gap-2">
          <button
            type="button"
            onClick={zoomToBounds}
            title={bounds ? "Zoom to overlay bounds" : "Zoom to region"}
            className={`${btnBase} ${primary}`}
          >
            <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M3 7v13l6-3 6 3 6-3V4L15 7 9 4 3 7z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <span>Zoom to Bounds</span>
          </button>

          <button
            type="button"
            onClick={centerOnMarker}
            title="Center on selected location"
            className={`${btnBase} ${secondary}`}
          >
            <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M12 2v4M12 18v4M4 12H0M24 12h-4M4.9 4.9L2.8 2.8M21.2 21.2l-2.1-2.1M2.8 21.2l2.1-2.1M21.2 2.8l-2.1 2.1" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.5" />
            </svg>
            <span>Center Location</span>
          </button>

          <button
            type="button"
            onClick={downloadOverlay}
            title={overlayUrl ? "Open overlay image" : "No overlay available"}
            className={`${btnBase} ${secondary} ${!overlayUrl ? "opacity-50 cursor-not-allowed" : ""}`}
            disabled={!overlayUrl}
            aria-disabled={!overlayUrl}
          >
            <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M12 3v12M9 9l3 3 3-3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M21 21H3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <span>Open Overlay</span>
          </button>
        </div>
      </div>
    </div>
  );
}

/**
 * MapView
 * Props:
 *  - selected: object that may contain .path, .bounds (minx,miny,maxx,maxy OR [[s,w],[n,e]]),
 *              or .lat/.lon and display_name
 *  - mapRef: React ref from parent to expose the map instance (optional)
 */
export default function MapView({ selected, mapRef }) {
  const overlayUrl = selected && selected.path ? storageUrl(selected.path) : null;

  // compute leaflet bounds from selected.bounds which can be two formats
  const bounds = useMemo(() => {
    if (!selected || !selected.bounds) return null;

    const b = selected.bounds;
    // Case: [minx, miny, maxx, maxy]
    if (Array.isArray(b) && b.length === 4 && typeof b[0] === "number") {
      const [minx, miny, maxx, maxy] = b;
      return [[miny, minx], [maxy, maxx]];
    }
    // Case: [[south, west],[north, east]] already
    if (Array.isArray(b) && b.length === 2 && Array.isArray(b[0])) {
      return b;
    }
    return null;
  }, [selected]);

  const hasLatLon = selected && (selected.lat || selected.lon);

  // default view (country / region friendly)
  const defaultCenter = [20.5937, 78.9629]; // India center fallback
  const defaultZoom = 5;

  return (
    <div className="relative h-full w-full bg-gray-100 rounded-xl overflow-hidden border border-gray-200">
      <MapContainer
        center={defaultCenter}
        zoom={defaultZoom}
        style={{ height: "100%", width: "100%" }}
        whenCreated={(mapInstance) => {
          if (mapRef) mapRef.current = mapInstance;
        }}
      >
        {/* Light-themed map tiles */}
        <TileLayer 
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
        />

        {/* If overlay available and bounds provided, show overlay and fit bounds */}
        {overlayUrl && bounds && (
          <>
            <ImageOverlay url={overlayUrl} bounds={bounds} opacity={0.7} />
            <FitToBounds bounds={bounds} />
            {/* Draw a rectangle to visualize footprint */}
            <Rectangle 
              bounds={bounds} 
              pathOptions={{ 
                color: "#3b82f6", 
                weight: 2, 
                fillOpacity: 0.1,
                fillColor: "#3b82f6"
              }} 
            />
          </>
        )}

        {/* If overlay exists but bounds missing, do not overlay */}
        {overlayUrl && !bounds && null}

        {/* If selected has lat/lon show a marker and pan/fly to it */}
        {hasLatLon && <SelectedMarkerFlyTo selected={selected} />}

        {/* Render map controls inside the map so they float above tiles */}
        <MapInnerControls bounds={bounds} selected={selected} overlayUrl={overlayUrl} />
      </MapContainer>
    </div>
  );
}

/**
 * A wrapper to access the map object inside react-leaflet render tree and render MapControls
 */
function MapInnerControls({ bounds, selected, overlayUrl }) {
  const map = useMap();
  return <MapControls map={map} bounds={bounds} selected={selected} overlayUrl={overlayUrl} />;
}

/**
 * Helper component: places a marker and flies the map to lat/lon when selected changes.
 */
function SelectedMarkerFlyTo({ selected }) {
  const map = useMap();

  useEffect(() => {
    if (!selected || (!selected.lat && !selected.lon)) return;

    const lat = Number(selected.lat);
    const lon = Number(selected.lon);
    if (Number.isFinite(lat) && Number.isFinite(lon)) {
      try {
        if (map.flyTo) {
          map.flyTo([lat, lon], 12, { duration: 0.8 });
        } else {
          map.setView([lat, lon], 12);
        }
      } catch (e) {
        console.warn("flyTo failed", e);
      }
    }
  }, [map, selected]);

  if (!selected || (!selected.lat && !selected.lon)) return null;

  const lat = Number(selected.lat);
  const lon = Number(selected.lon);
  return (
    <Marker 
      position={[lat, lon]}
      icon={L.divIcon({
        className: 'custom-marker',
        html: `<div style="background-color: #3b82f6; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.2);"></div>`,
        iconSize: [12, 12],
        iconAnchor: [6, 6]
      })}
    >
      <Popup className="custom-popup">
        <div className="text-sm font-medium text-gray-900">
          {selected.display_name || selected.name || `${lat.toFixed(4)}, ${lon.toFixed(4)}`}
        </div>
        {selected.address && (
          <div className="text-xs text-gray-600 mt-1">{selected.address}</div>
        )}
      </Popup>
    </Marker>
  );
}