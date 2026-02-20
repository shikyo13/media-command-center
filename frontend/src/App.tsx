import { useWebSocket } from '@/hooks/useWebSocket'
import { Shell } from '@/components/layout/Shell'
import { HealthGrid } from '@/components/panels/HealthGrid'
import { DownloadsPanel } from '@/components/panels/DownloadsPanel'
import { StreamingPanel } from '@/components/panels/StreamingPanel'
import { TranscodingPanel } from '@/components/panels/TranscodingPanel'
import { CalendarPanel } from '@/components/panels/CalendarPanel'

export default function App() {
  useWebSocket()

  return (
    <Shell>
      {(view) => (
        <>
          {(view === 'overview' || view === 'health') && <HealthGrid />}
          {(view === 'overview' || view === 'downloads') && <DownloadsPanel />}
          {(view === 'overview' || view === 'streaming') && <StreamingPanel />}
          {(view === 'overview' || view === 'transcoding') && <TranscodingPanel />}
          {(view === 'overview' || view === 'calendar') && <CalendarPanel />}
        </>
      )}
    </Shell>
  )
}
