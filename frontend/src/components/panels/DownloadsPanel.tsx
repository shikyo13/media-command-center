import { useDownloadsStore } from '@/hooks/useStore'

export function DownloadsPanel() {
  const { sabnzbd, sonarr_queue, radarr_queue } = useDownloadsStore((s) => s.data)
  const hasItems = sabnzbd.items.length > 0 || sonarr_queue.length > 0 || radarr_queue.length > 0

  return (
    <section className="mb-8">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-text-primary">Active Downloads</h2>
        {sabnzbd.speed && (
          <span className="text-sm font-mono text-glow-primary">{sabnzbd.speed}/s</span>
        )}
      </div>
      <div className="glass-card p-4 glow-primary">
        {!hasItems && <p className="text-text-muted text-sm text-center py-4">No active downloads</p>}
        {sabnzbd.items.map((item, i) => (
          <div key={i} className="mb-4 last:mb-0">
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm text-text-primary truncate mr-4">{item.name}</span>
              <span className="text-xs font-mono text-text-secondary shrink-0">
                {item.percentage}% · {item.timeleft}
              </span>
            </div>
            <div className="progress-bar">
              <div className={`progress-bar-fill ${item.status === 'Downloading' ? 'active' : ''}`}
                style={{ width: `${item.percentage}%` }} />
            </div>
          </div>
        ))}
        {(sonarr_queue.length > 0 || radarr_queue.length > 0) && sabnzbd.items.length > 0 && (
          <hr className="border-border my-4" />
        )}
        {[...sonarr_queue, ...radarr_queue].map((item, i) => (
          <div key={`q-${i}`} className="flex items-center justify-between py-1">
            <span className="text-sm text-text-secondary truncate mr-4">{item.title}</span>
            <span className="text-xs font-mono text-text-muted">{item.status}</span>
          </div>
        ))}
      </div>
    </section>
  )
}
