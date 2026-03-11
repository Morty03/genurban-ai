// src/components/Layout/Header.jsx
const Header = ({ backendStatus, activeView, setActiveView }) => {
  const StatusBadge = () => {
    const statusConfig = {
      connected: { color: 'bg-green-500', label: 'Connected' },
      disconnected: { color: 'bg-red-500', label: 'Disconnected' },
      checking: { color: 'bg-yellow-500', label: 'Checking...' },
      error: { color: 'bg-gray-500', label: 'Error' }
    }
    
    const config = statusConfig[backendStatus] || statusConfig.error
    
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white border border-gray-300 shadow-sm">
        <span className={`w-2 h-2 rounded-full ${config.color}`} />
        <span className="text-sm font-medium text-gray-700">{config.label}</span>
      </div>
    )
  }

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-blue-700 rounded-xl flex items-center justify-center shadow-sm">
            <span className="text-white font-bold text-lg">G</span>
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">GenUrban</h1>
            <p className="text-sm text-gray-500">Urban Planning Intelligence Platform</p>
          </div>
        </div>

        <div className="flex items-center gap-6">
          <nav className="flex gap-6">
            {[
              { id: 'analysis', label: 'Analysis' },
              { id: 'scenarios', label: 'Scenarios' },
              { id: 'data', label: 'Data' },
              { id: 'models', label: 'Models' }
            ].map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveView(item.id)}
                className={`capitalize font-medium text-sm transition-colors ${
                  activeView === item.id 
                    ? 'text-blue-600 border-b-2 border-blue-600 pb-1' 
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {item.label}
              </button>
            ))}
          </nav>
          <StatusBadge />
        </div>
      </div>
    </header>
  )
}

export default Header