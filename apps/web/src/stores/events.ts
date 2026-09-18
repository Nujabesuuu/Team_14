import { create } from 'zustand'

import { api } from '@/api/client'
import { realtime } from '@/api/ws'
import type { Event, EventCreate, EventKind, Game } from '@/api/types'

interface EventsState {
  games: Game[]
  feed: Event[]
  mine: Event[]
  byId: Record<string, Event>
  loaded: boolean
  loadGames: () => Promise<Game[]>
  loadFeed: (kind?: EventKind) => Promise<void>
  loadMine: () => Promise<void>
  load: (id: string) => Promise<Event>
  create: (input: EventCreate) => Promise<Event>
  act: (id: string, action: 'join' | 'leave' | 'start' | 'finish' | 'cancel') => Promise<Event>
  upsert: (event: Event) => void
}

export const useEvents = create<EventsState>((set, get) => {
  const upsert = (event: Event) =>
    set((s) => ({
      byId: { ...s.byId, [event.id]: event },
      feed: s.feed.some((e) => e.id === event.id) ? s.feed.map((e) => (e.id === event.id ? event : e)) : s.feed,
      mine: s.mine.some((e) => e.id === event.id)
        ? s.mine.map((e) => (e.id === event.id ? event : e))
        : event.is_participant
          ? [event, ...s.mine]
          : s.mine,
    }))

  realtime.on('event.updated', (e) => upsert(e.event))

  return {
    games: [],
    feed: [],
    mine: [],
    byId: {},
    loaded: false,

    async loadGames() {
      if (get().games.length) return get().games
      const games = await api.get<Game[]>('/games')
      set({ games })
      return games
    },

    async loadFeed(kind) {
      const q = kind ? `?kind=${kind}` : ''
      const feed = await api.get<Event[]>(`/events${q}`)
      set((s) => ({ feed, loaded: true, byId: { ...s.byId, ...Object.fromEntries(feed.map((e) => [e.id, e])) } }))
    },

    async loadMine() {
      const mine = await api.get<Event[]>('/events?mine=true')
      set((s) => ({ mine, byId: { ...s.byId, ...Object.fromEntries(mine.map((e) => [e.id, e])) } }))
    },

    async load(id) {
      const event = await api.get<Event>(`/events/${id}`)
      upsert(event)
      return event
    },

    async create(input) {
      const event = await api.post<Event>('/events', input)
      set((s) => ({ feed: [event, ...s.feed], mine: [event, ...s.mine], byId: { ...s.byId, [event.id]: event } }))
      return event
    },

    async act(id, action) {
      const event = await api.post<Event>(`/events/${id}/${action}`)
      upsert(event)
      return event
    },

    upsert,
  }
})
