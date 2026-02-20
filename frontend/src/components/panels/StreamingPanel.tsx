import { useStreamingStore } from '@/hooks/useStore'

export function StreamingPanel() {
  const { stream_count, transcode_count, sessions } = useStreamingStore((s) => s.data)

  return (
    <section className="mb-8">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-text-primary">Plex Streaming</h2>
        <div className="flex gap-4 text-sm font-mono">
          <span className="text-glow-success">{stream_count} stream{stream_count !== 1 ? 's' : ''}</span>
          {transcode_count > 0 && (
            <span className="text-glow-warning">{transcode_count} transcode{transcode_count !== 1 ? 's' : ''}</span>
          )}
        </div>
      </div>
      <div className="glass-card p-4 glow-info">
        {sessions.length === 0 && <p className="text-text-muted text-sm text-center py-4">No active streams</p>}
        <div className="space-y-3">
          {sessions.map((s, i) => {
            const mediaTitle = s.grandparentTitle
              ? `${s.grandparentTitle} \u2014 S${s.parentIndex}E${s.index}`
              : s.title
            return (
              <div key={i} className="flex items-center justify-between animate-fade-in" style={{ animationDelay: `${i * 80}ms` }}>
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-surface flex items-center justify-center text-xs font-mono text-glow-primary">
                    {s.user.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <p className="text-sm text-text-primary">{mediaTitle}</p>
                    <p className="text-xs text-text-muted">{s.user}</p>
                  </div>
                </div>
                <span className={`text-xs font-mono px-2 py-0.5 rounded ${
                  s.decision === 'directplay' ? 'bg-[rgba(0,255,136,0.1)] text-glow-success' : 'bg-[rgba(255,170,0,0.1)] text-glow-warning'
                }`}>
                  {s.decision === 'directplay' ? 'Direct Play' : 'Transcode'}
                </span>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
