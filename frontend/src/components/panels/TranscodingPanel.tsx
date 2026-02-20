import { useTranscodingStore } from '@/hooks/useStore'
import { formatBytes } from '@/lib/utils'

export function TranscodingPanel() {
  const { nodes, queue_size, total_files, total_transcodes, size_diff_bytes } = useTranscodingStore((s) => s.data)

  return (
    <section className="mb-8">
      <h2 className="text-lg font-semibold text-text-primary mb-4">Tdarr Transcode Pipeline</h2>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        {[
          { label: 'Queue', value: queue_size, glow: queue_size > 0 ? 'text-glow-warning' : 'text-glow-success' },
          { label: 'Total Files', value: total_files.toLocaleString(), glow: 'text-glow-primary' },
          { label: 'Transcoded', value: total_transcodes.toLocaleString(), glow: 'text-glow-info' },
          { label: 'Space Saved', value: formatBytes(Math.abs(size_diff_bytes)), glow: 'text-glow-success' },
        ].map((stat) => (
          <div key={stat.label} className="glass-card p-3 text-center">
            <p className={`text-xl font-mono font-bold ${stat.glow}`}>{stat.value}</p>
            <p className="text-xs text-text-muted">{stat.label}</p>
          </div>
        ))}
      </div>
      <div className="glass-card p-4 glow-info">
        {nodes.length === 0 && <p className="text-text-muted text-sm text-center py-4">No Tdarr nodes connected</p>}
        {nodes.map((node) => {
          const workerCount = Object.keys(node.workers).length
          return (
            <div key={node.id} className="flex items-center justify-between py-2">
              <div className="flex items-center gap-2">
                <span className="status-dot status-dot-online" />
                <span className="text-sm">{node.name}</span>
              </div>
              <span className="text-xs font-mono text-text-muted">
                {workerCount} worker{workerCount !== 1 ? 's' : ''}
              </span>
            </div>
          )
        })}
      </div>
    </section>
  )
}
