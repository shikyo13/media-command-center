function App() {
  return (
    <div className="min-h-screen p-8">
      <h1 className="text-2xl font-bold text-glow-primary mb-4">
        Media Command Center
      </h1>
      <div className="glass-card glow-primary p-6 max-w-md">
        <div className="flex items-center gap-3 mb-4">
          <div className="status-dot status-dot-online" />
          <span className="text-text-primary">System Online</span>
        </div>
        <div className="progress-bar">
          <div className="progress-bar-fill active" style={{ width: '65%' }} />
        </div>
      </div>
    </div>
  )
}

export default App
