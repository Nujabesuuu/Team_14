import { create } from 'zustand'

import { api } from '@/api/client'
import { realtime } from '@/api/ws'
import type { Match } from '@/api/types'

interface MatchesState {
  list: Match[]
  loaded: boolean
  /** A match that just happened and has not been celebrated on screen yet. */
  pendingCelebration: Match | null
  load: () => Promise<Match[]>
  get: (id: string) => Promise<Match>
  upsert: (match: Match) => void
  consent: (id: string) => Promise<Match>
  earlyRequest: (id: string) => Promise<Match>
  earlyAccept: (id: string) => Promise<Match>
  clearCelebration: () => void
}

export const useMatches = create<MatchesState>((set, get) => {
  const upsert = (match: Match) =>
    set((s) => ({
      list: s.list.some((m) => m.id === match.id)
        ? s.list.map((m) => (m.id === match.id ? match : m))
        : [match, ...s.list],
    }))

  realtime.on('match.new', (e) => {
    upsert(e.match)
    set({ pendingCelebration: e.match })
  })
  realtime.on('reveal.updated', (e) => {
    if (e.match) upsert(e.match)
    else if (e.match_id) void get().get(e.match_id)
  })
  realtime.on('message.new', (e) => {
    set((s) => ({
      list: s.list.map((m) => (m.conversation_id === e.message.conversation_id ? { ...m, last_message: e.message } : m)),
    }))
  })

  return {
    list: [],
    loaded: false,
    pendingCelebration: null,

    async load() {
      const list = await api.get<Match[]>('/matches')
      set({ list, loaded: true })
      return list
    },

    async get(id) {
      const match = await api.get<Match>(`/matches/${id}`)
      upsert(match)
      return match
    },

    upsert,

    async consent(id) {
      const match = await api.post<Match>(`/matches/${id}/reveal/consent`)
      upsert(match)
      return match
    },

    async earlyRequest(id) {
      const match = await api.post<Match>(`/matches/${id}/reveal/early-request`)
      upsert(match)
      return match
    },

    async earlyAccept(id) {
      const match = await api.post<Match>(`/matches/${id}/reveal/early-accept`)
      upsert(match)
      return match
    },

    clearCelebration() {
      set({ pendingCelebration: null })
    },
  }
})
