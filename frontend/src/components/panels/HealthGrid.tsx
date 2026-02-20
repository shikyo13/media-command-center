import { useHealthStore } from '@/hooks/useStore'

export function HealthGrid() {
  const { services } = useHealthStore((s) => s.data)

  return (
    <section className="mb-8">
      <h2 className="text-lg font-semibold text-text-primary mb-4">Service Health</h2>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
        {services.map((svc, i) => (
          <div
            key={svc.name}
            className={`glass-card p-4 animate-fade-in transition-all ${
              svc.status === 'online' ? 'glow-success' : 'glow-danger'
            }`}
            style={{ animationDelay: `${i * 50}ms` }}
          >
            <div className="flex items-center gap-2 mb-2">
              <span className={`status-dot ${svc.status === 'online' ? 'status-dot-online' : 'status-dot-offline'}`} />
              <span className="text-sm font-medium capitalize">{svc.name}</span>
            </div>
            <div className="flex items-baseline justify-between">
              <span className="text-xs text-text-muted font-mono">{svc.version || '\u2014'}</span>
              <span className="text-xs text-text-muted font-mono">{svc.response_ms}ms</span>
            </div>
          </div>
        ))}
        {services.length === 0 && (
          <div className="glass-card p-4 col-span-full text-center text-text-muted">
            No services configured
          </div>
        )}
      </div>
    </section>
  )
}
