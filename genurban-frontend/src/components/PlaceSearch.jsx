// src/components/PlaceSearch.jsx
import { useState } from 'react'

const PlaceSearch = ({ onLocationSelect, className = '' }) => {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [isLoading, setIsLoading] = useState(false)

  const handleSearch = async () => {
    if (!query.trim()) return
    
    setIsLoading(true)
    try {
      // Mock search results - replace with actual API call
      const mockResults = [
        {
          id: 1,
          name: 'Bangalore, Karnataka',
          address: 'Bangalore Urban, Karnataka, India',
          lat: 12.9716,
          lng: 77.5946
        },
        {
          id: 2,
          name: 'Delhi',
          address: 'National Capital Territory of Delhi, India',
          lat: 28.6139,
          lng: 77.2090
        },
        {
          id: 3,
          name: 'Mumbai, Maharashtra',
          address: 'Mumbai, Maharashtra, India',
          lat: 19.0760,
          lng: 72.8777
        }
      ]
      setResults(mockResults)
    } catch (error) {
      console.error('Search failed:', error)
      setResults([])
    } finally {
      setIsLoading(false)
    }
  }

  const handleSelect = (location) => {
    setQuery(location.name)
    setResults([])
    if (onLocationSelect) {
      onLocationSelect(location)
    }
  }

  return (
    <div className={`space-y-3 ${className}`}>
      <div className="flex gap-3">
        <div className="flex-1">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Search for a city in India..."
            className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
          />
        </div>
        <button
          onClick={handleSearch}
          disabled={!query.trim() || isLoading}
          className="px-6 py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? '...' : 'Search'}
        </button>
      </div>

      {results.length > 0 && (
        <div className="border border-gray-200 rounded-xl bg-white shadow-sm overflow-hidden">
          {results.map((location) => (
            <div
              key={location.id}
              onClick={() => handleSelect(location)}
              className="p-4 border-b border-gray-100 last:border-b-0 hover:bg-gray-50 cursor-pointer transition-colors"
            >
              <div className="font-medium text-gray-900">{location.name}</div>
              <div className="text-sm text-gray-600 mt-1">{location.address}</div>
            </div>
          ))}
        </div>
      )}

      {query && results.length === 0 && !isLoading && (
        <div className="text-center py-4 text-gray-500 text-sm">
          No locations found. Try another search.
        </div>
      )}
    </div>
  )
}

export default PlaceSearch