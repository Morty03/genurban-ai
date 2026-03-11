// src/components/Layout/AppLayout.jsx
import { useState } from 'react'
import Header from './Header'
import Sidebar from './Sidebar'
import MainContent from './MainContent'
import MapPanel from '../Map/MapPanel'

const AppLayout = () => {
  const [currentLocation, setCurrentLocation] = useState(null)
  const [urbanData, setUrbanData] = useState(null)
  const [scenarios, setScenarios] = useState([])
  const [selectedScenario, setSelectedScenario] = useState(null)
  const [activeView, setActiveView] = useState('analysis')

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <Sidebar 
        currentLocation={currentLocation}
        setCurrentLocation={setCurrentLocation}
        setUrbanData={setUrbanData}
        setScenarios={setScenarios}
        setSelectedScenario={setSelectedScenario}
        activeView={activeView}
        setActiveView={setActiveView}
      />
      
      {/* Main Content Area */}
      <div className="flex-1 flex flex-col">
        <Header />
        
        <div className="flex-1 flex">
          {/* Left Panel - Analysis & Scenarios */}
          <MainContent 
            urbanData={urbanData}
            scenarios={scenarios}
            selectedScenario={selectedScenario}
            setSelectedScenario={setSelectedScenario}
            currentLocation={currentLocation}
            activeView={activeView}
          />
          
          {/* Right Panel - Map */}
          <MapPanel 
            currentLocation={currentLocation}
            selectedScenario={selectedScenario}
          />
        </div>
      </div>
    </div>
  )
}

export default AppLayout