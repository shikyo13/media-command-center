/* Types matching backend WebSocket message shapes. */

export interface WsMessage<T = unknown> {
  type: 'health' | 'downloads' | 'streaming' | 'transcoding' | 'calendar'
  timestamp: string
  data: T
}

export interface ServiceHealth {
  name: string
  status: 'online' | 'offline'
  version: string
  response_ms: number
}

export interface HealthData {
  services: ServiceHealth[]
}

export interface SabItem {
  name: string
  percentage: string
  sizeleft: string
  status: string
  timeleft: string
}

export interface DownloadsData {
  sabnzbd: {
    speed: string
    sizeleft: string
    timeleft: string
    items: SabItem[]
  }
  sonarr_queue: { title: string; status: string; sizeleft: number; size: number }[]
  radarr_queue: { title: string; status: string; sizeleft: number; size: number }[]
}

export interface PlexSession {
  user: string
  title: string
  decision: string
  grandparentTitle: string
  parentIndex: string
  index: string
}

export interface StreamingData {
  stream_count: number
  transcode_count: number
  sessions: PlexSession[]
}

export interface TdarrNode {
  id: string
  name: string
  workers: Record<string, unknown>
}

export interface TranscodingData {
  nodes: TdarrNode[]
  queue_size: number
  total_files: number
  total_transcodes: number
  size_diff_bytes: number
}

export interface CalendarEpisode {
  series: string
  title: string
  airDate: string
  season: number
  episode: number
  hasFile: boolean
}

export interface CalendarMovie {
  title: string
  releaseDate: string
  hasFile: boolean
}

export interface CalendarData {
  episodes: CalendarEpisode[]
  movies: CalendarMovie[]
}
