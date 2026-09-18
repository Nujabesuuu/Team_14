import type { WsEvent } from './types'

type Handler<T extends WsEvent['type']> = (event: Extract<WsEvent, { type: T }>) => void

/**
 * One socket per session with exponential-backoff reconnect.
 * Stores subscribe by event type; the socket itself is an implementation detail.
 */
export class RealtimeClient {
  private socket: WebSocket | null = null
  private handlers = new Map<string, Set<(e: WsEvent) => void>>()
  private url: string | null = null
  private attempts = 0
  private closedByUser = false
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null

  connect(url: string) {
    this.url = url
    this.closedByUser = false
    this.open()
  }

  disconnect() {
    this.closedByUser = true
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer)
    this.socket?.close()
    this.socket = null
  }

  on<T extends WsEvent['type']>(type: T, handler: Handler<T>): () => void {
    const set = this.handlers.get(type) ?? new Set()
    set.add(handler as (e: WsEvent) => void)
    this.handlers.set(type, set)
    return () => set.delete(handler as (e: WsEvent) => void)
  }

  send(payload: Record<string, unknown>): boolean {
    if (this.socket?.readyState !== WebSocket.OPEN) return false
    this.socket.send(JSON.stringify(payload))
    return true
  }

  /** Exposed for tests: feed a raw event as if it arrived from the server. */
  dispatch(event: WsEvent) {
    this.handlers.get(event.type)?.forEach((h) => h(event))
  }

  get isOpen() {
    return this.socket?.readyState === WebSocket.OPEN
  }

  private open() {
    if (!this.url) return
    const ws = new WebSocket(this.url)
    this.socket = ws
    ws.onopen = () => {
      this.attempts = 0
    }
    ws.onmessage = (msg) => {
      try {
        this.dispatch(JSON.parse(msg.data) as WsEvent)
      } catch {
        /* ignore malformed frames */
      }
    }
    ws.onclose = () => {
      if (this.closedByUser) return
      const delay = Math.min(10_000, 500 * 2 ** this.attempts++)
      this.reconnectTimer = setTimeout(() => this.open(), delay)
    }
  }
}

export const realtime = new RealtimeClient()
