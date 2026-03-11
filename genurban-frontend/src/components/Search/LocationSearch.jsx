// src/components/Search/LocationSearch.jsx
import { useState } from 'react'
import { Search } from "lucide-react"        // ← proper icon
import { urbanAPI, formatUrbanData } from '../../utils/api'

const LocationSearch = ({ currentLocation, setCurrentLocation, setUrbanData }) => {
  const [searchQuery, setSearchQuery] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleSearch = async () => {
    if (!searchQuery.trim()) return
    
    setIsLoading(true)
    try {
      const results = await urbanAPI.searchLocation(searchQuery)
      if (results && results.length > 0) {
        await handleSelectLocation(results[0])
      }
    } catch (error) {
      console.error('Location search failed:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSelectLocation = async (location) => {
    setCurrentLocation(location)
    
    try {
      const analysis = await urbanAPI.analyzeUrbanMorphology({
        lat: location.lat,
        lng: location.lng,
        years: 5
      })
      setUrbanData(formatUrbanData(analysis.data))
    } catch (error) {
      console.error('Analysis failed:', error)
    }
  }

  return (
    <div className="space-y-3">
      
      {/* Search Box */}
      <div className="flex gap-3">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          placeholder="Search city…"
          className="flex-1 px-4 py-3 text-sm border border-gray-300 rounded-xl shadow-sm
                     focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />

        {/* BIG SEARCH BUTTON */}
        <button
          onClick={handleSearch}
          disabled={!searchQuery.trim() || isLoading}
          className={`flex items-center justify-center px-4 rounded-xl
                     transition-all duration-200 shadow-md
                     ${isLoading 
                        ? 'bg-blue-400 cursor-not-allowed'
                        : 'bg-blue-600 hover:bg-blue-700 active:scale-95'}
                    `}
        >
          {isLoading ? (
            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          ) : (
            <Search className="w-6 h-6 text-white" />    // ← clean big icon
          )}
        </button>
      </div>

      {/* Selected Location Card */}
      {currentLocation && (
        <div className="p-3 bg-green-50 rounded-lg border border-green-200 shadow-sm">
          <div className="flex items-center gap-2 mb-1">
            <div className="w-2 h-2 bg-green-500 rounded-full" />
            <span className="text-sm font-medium text-green-800">Selected</span>
          </div>
          <div className="font-semibold text-gray-900 text-sm">{currentLocation.name}</div>
          <div className="text-gray-600 text-xs">{currentLocation.address}</div>
        </div>
      )}
    </div>
  )
}

export default LocationSearch
