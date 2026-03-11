// src/components/ScenarioUpload.jsx
import { useState } from 'react'

const ScenarioUpload = ({ onUpload, className = '' }) => {
  const [isDragging, setIsDragging] = useState(false)

  const handleDragOver = (e) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragging(false)
    
    const files = e.dataTransfer.files
    if (files.length > 0) {
      handleFiles(files)
    }
  }

  const handleFileSelect = (e) => {
    const files = e.target.files
    if (files.length > 0) {
      handleFiles(files)
    }
  }

  const handleFiles = (files) => {
    // Process uploaded files
    const file = files[0]
    if (file) {
      console.log('File selected:', file)
      if (onUpload) {
        onUpload({
          name: file.name,
          size: file.size,
          type: file.type
        })
      }
    }
  }

  return (
    <div className={`bg-white rounded-2xl border border-gray-200 p-6 ${className}`}>
      <div className="text-center">
        <div className="w-12 h-12 bg-blue-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
        </div>
        
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Upload Scenario Data</h3>
        <p className="text-gray-600 text-sm mb-6">
          Upload GIS data, satellite imagery, or scenario files for analysis
        </p>

        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-xl p-8 transition-colors ${
            isDragging 
              ? 'border-blue-500 bg-blue-50' 
              : 'border-gray-300 hover:border-gray-400'
          }`}
        >
          <div className="space-y-3">
            <svg className="w-8 h-8 text-gray-400 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            
            <div className="text-sm text-gray-600">
              <span className="font-medium text-blue-600">Click to upload</span> or drag and drop
            </div>
            <div className="text-xs text-gray-500">
              Supports GeoJSON, KML, GeoTIFF, CSV (Max 100MB)
            </div>
          </div>

          <input
            type="file"
            onChange={handleFileSelect}
            className="hidden"
            id="file-upload"
            accept=".geojson,.kml,.tif,.tiff,.csv,.json"
          />
          
          <label
            htmlFor="file-upload"
            className="mt-4 inline-block px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 cursor-pointer transition-colors"
          >
            Choose Files
          </label>
        </div>

        <div className="mt-6 text-xs text-gray-500 space-y-1">
          <div>Supported formats: GeoJSON, KML, GeoTIFF, CSV</div>
          <div>Maximum file size: 100MB per file</div>
        </div>
      </div>
    </div>
  )
}

export default ScenarioUpload