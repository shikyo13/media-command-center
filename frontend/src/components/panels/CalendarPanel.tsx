import { useCalendarStore } from '@/hooks/useStore'
import { relativeTime } from '@/lib/utils'

export function CalendarPanel() {
  const { episodes, movies } = useCalendarStore((s) => s.data)

  return (
    <section className="mb-8">
      <h2 className="text-lg font-semibold text-text-primary mb-4">Upcoming</h2>
      <div className="grid md:grid-cols-2 gap-4">
        <div className="glass-card p-4">
          <h3 className="text-sm font-semibold text-glow-primary mb-3">Episodes</h3>
          {episodes.length === 0 && <p className="text-text-muted text-sm">Nothing upcoming</p>}
          <div className="space-y-2">
            {episodes.map((ep, i) => (
              <div key={i} className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-text-primary">{ep.series}</p>
                  <p className="text-xs text-text-muted">
                    S{String(ep.season).padStart(2, '0')}E{String(ep.episode).padStart(2, '0')} — {ep.title}
                  </p>
                </div>
                <div className="text-right shrink-0 ml-4">
                  <p className="text-xs font-mono text-text-secondary">{relativeTime(ep.airDate)}</p>
                  {ep.hasFile && <span className="text-xs text-glow-success">Downloaded</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="glass-card p-4">
          <h3 className="text-sm font-semibold text-glow-info mb-3">Movies</h3>
          {movies.length === 0 && <p className="text-text-muted text-sm">Nothing upcoming</p>}
          <div className="space-y-2">
            {movies.map((m, i) => (
              <div key={i} className="flex items-center justify-between">
                <p className="text-sm text-text-primary">{m.title}</p>
                <div className="text-right shrink-0 ml-4">
                  <p className="text-xs font-mono text-text-secondary">{relativeTime(m.releaseDate)}</p>
                  {m.hasFile && <span className="text-xs text-glow-success">Downloaded</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
