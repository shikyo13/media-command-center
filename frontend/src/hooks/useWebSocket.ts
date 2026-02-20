import { useEffect, useRef } from 'react'
import type {
  WsMessage,
  HealthData,
  DownloadsData,
  StreamingData,
  TranscodingData,
  CalendarData,
} from '@/lib/types'
import {
  useHealthStore,
  useDownloadsStore,
  useStreamingStore,
  useTranscodingStore,
  useCalendarStore,
} from './useStore'

const WS_URL = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws`
const RECONNECT_DELAY = 3000

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>(undefined)

  useEffect(() => {
    function connect() {
      const ws = new WebSocket(WS_URL)
      wsRef.current = ws

      ws.onmessage = (event: MessageEvent) => {
        try {
          const msg: WsMessage = JSON.parse(event.data as string)
          switch (msg.type) {
            case 'health':
              useHealthStore.getState().setData(msg.data as HealthData)
              break
            case 'downloads':
              useDownloadsStore.getState().setData(msg.data as DownloadsData)
              break
            case 'streaming':
              useStreamingStore.getState().setData(msg.data as StreamingData)
              break
            case 'transcoding':
              useTranscodingStore.getState().setData(msg.data as TranscodingData)
              break
            case 'calendar':
              useCalendarStore.getState().setData(msg.data as CalendarData)
              break
          }
        } catch {
          /* ignore malformed messages */
        }
      }

      ws.onclose = () => {
        reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY)
      }

      ws.onerror = () => ws.close()
    }

    connect()

    return () => {
      clearTimeout(reconnectTimer.current)
      wsRef.current?.close()
    }
  }, [])
}
