// src/App.jsx
import { useState, useEffect } from 'react'
import './App.css'
import { testAPIConnection } from './utils/api'
import Header from './components/Layout/Header'
import Sidebar from './components/Layout/Sidebar'
import MainContent from './components/Layout/MainContent'

function App() {
  const [backendStatus, setBackendStatus] = useState('checking')
  const [currentLocation, setCurrentLocation] = useState(null)
  const [urbanData, setUrbanData] = useState(null)
  const [scenarios, setScenarios] = useState([])
  const [selectedScenario, setSelectedScenario] = useState(null)
  const [activeView, setActiveView] = useState('analysis')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    initializeApp()
  }, [])

  const initializeApp = async () => {
    try {
      setLoading(true)
      const connection = await testAPIConnection()
      setBackendStatus(connection.connected ? 'connected' : 'disconnected')
    } catch (error) {
      console.error('App initialization failed:', error)
      setBackendStatus('error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar - Fixed width */}
      <div className="w-80 flex-shrink-0">
        <Sidebar 
          currentLocation={currentLocation}
          setCurrentLocation={setCurrentLocation}
          setUrbanData={setUrbanData}
          setScenarios={setScenarios}
          setSelectedScenario={setSelectedScenario}
          activeView={activeView}
          setActiveView={setActiveView}
          loading={loading}
          setLoading={setLoading}
        />
      </div>
      
      {/* Main Content Area - Flexible */}
      <div className="flex-1 flex flex-col min-w-0">
        <Header 
          backendStatus={backendStatus}
          activeView={activeView}
          setActiveView={setActiveView}
        />
        
        {/* Main Content takes full width without MapPanel */}
        <div className="flex-1 min-w-0">
          <MainContent 
            urbanData={urbanData}
            scenarios={scenarios}
            selectedScenario={selectedScenario}
            setSelectedScenario={setSelectedScenario}
            currentLocation={currentLocation}
            activeView={activeView}
            loading={loading}
          />
        </div>
      </div>
    </div>
  )
}

export default App