import { useState, type ReactNode } from 'react'
import { Sidebar } from './Sidebar'

interface ShellProps {
  children: (activeView: string) => ReactNode
}

export function Shell({ children }: ShellProps) {
  const [active, setActive] = useState('overview')

  return (
    <div className="min-h-screen bg-bg-base">
      <Sidebar active={active} onNavigate={setActive} />
      <main className="ml-16 p-6">
        <header className="mb-6">
          <h1 className="text-2xl font-semibold text-text-primary">Media Command Center</h1>
          <p className="text-sm text-text-muted">Real-time media infrastructure monitoring</p>
        </header>
        {children(active)}
      </main>
    </div>
  )
}
