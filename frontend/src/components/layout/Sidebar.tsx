import { Activity, Download, Tv, HardDrive, Calendar } from 'lucide-react'

const NAV_ITEMS = [
  { icon: Activity, label: 'Overview', id: 'overview' },
  { icon: Download, label: 'Downloads', id: 'downloads' },
  { icon: Tv, label: 'Plex', id: 'streaming' },
  { icon: HardDrive, label: 'Tdarr', id: 'transcoding' },
  { icon: Calendar, label: 'Calendar', id: 'calendar' },
] as const

interface SidebarProps {
  active: string
  onNavigate: (id: string) => void
}

export function Sidebar({ active, onNavigate }: SidebarProps) {
  return (
    <aside className="fixed left-0 top-0 h-screen w-16 glass-card rounded-none border-r border-t-0 border-b-0 border-l-0 flex flex-col items-center py-6 gap-2 z-50">
      <div className="text-glow-primary font-mono text-xs font-bold mb-6">MCC</div>
      {NAV_ITEMS.map(({ icon: Icon, label, id }) => (
        <button
          key={id}
          onClick={() => onNavigate(id)}
          className={`w-10 h-10 rounded-lg flex items-center justify-center transition-all ${
            active === id
              ? 'bg-[rgba(0,212,255,0.15)] text-glow-primary'
              : 'text-text-secondary hover:text-text-primary hover:bg-surface-hover'
          }`}
          title={label}
        >
          <Icon size={20} />
        </button>
      ))}
    </aside>
  )
}
