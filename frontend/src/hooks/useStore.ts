import { create } from 'zustand'
import type {
  HealthData,
  DownloadsData,
  StreamingData,
  TranscodingData,
  CalendarData,
} from '@/lib/types'

interface HealthStore {
  data: HealthData
  setData: (d: HealthData) => void
}

export const useHealthStore = create<HealthStore>((set) => ({
  data: { services: [] },
  setData: (data) => set({ data }),
}))

interface DownloadsStore {
  data: DownloadsData
  setData: (d: DownloadsData) => void
}

export const useDownloadsStore = create<DownloadsStore>((set) => ({
  data: {
    sabnzbd: { speed: '0', sizeleft: '0', timeleft: '0', items: [] },
    sonarr_queue: [],
    radarr_queue: [],
  },
  setData: (data) => set({ data }),
}))

interface StreamingStore {
  data: StreamingData
  setData: (d: StreamingData) => void
}

export const useStreamingStore = create<StreamingStore>((set) => ({
  data: { stream_count: 0, transcode_count: 0, sessions: [] },
  setData: (data) => set({ data }),
}))

interface TranscodingStore {
  data: TranscodingData
  setData: (d: TranscodingData) => void
}

export const useTranscodingStore = create<TranscodingStore>((set) => ({
  data: {
    nodes: [],
    queue_size: 0,
    total_files: 0,
    total_transcodes: 0,
    size_diff_bytes: 0,
  },
  setData: (data) => set({ data }),
}))

interface CalendarStore {
  data: CalendarData
  setData: (d: CalendarData) => void
}

export const useCalendarStore = create<CalendarStore>((set) => ({
  data: { episodes: [], movies: [] },
  setData: (data) => set({ data }),
}))
