import { create } from 'zustand'

import { api } from '@/api/client'
import { realtime } from '@/api/ws'
import type { Message } from '@/api/types'

interface Thread {
  messages: Message[]
  hasMore: boolean
  loading: boolean
}

interface ChatState {
  threads: Record<string, Thread>
  loadHistory: (conversationId: string, before?: string) => Promise<void>
  send: (conversationId: string, body: string) => Promise<void>
  receive: (message: Message) => void
}

const PAGE = 50

/** Insert keeping messages unique by id and sorted by created_at. */
export function mergeMessages(existing: Message[], incoming: Message[]): Message[] {
  const byId = new Map(existing.map((m) => [m.id, m]))
  for (const m of incoming) byId.set(m.id, m)
  return [...byId.values()].sort((a, b) => a.created_at.localeCompare(b.created_at))
}

export const useChat = create<ChatState>((set, get) => {
  const receive = (message: Message) =>
    set((s) => {
      const thread = s.threads[message.conversation_id] ?? { messages: [], hasMore: false, loading: false }
      return {
        threads: {
          ...s.threads,
          [message.conversation_id]: { ...thread, messages: mergeMessages(thread.messages, [message]) },
        },
      }
    })

  realtime.on('message.new', (e) => receive(e.message))

  return {
    threads: {},

    async loadHistory(conversationId, before) {
      const current = get().threads[conversationId] ?? { messages: [], hasMore: true, loading: false }
      if (current.loading) return
      set((s) => ({ threads: { ...s.threads, [conversationId]: { ...current, loading: true } } }))
      const q = before ? `?before=${encodeURIComponent(before)}&limit=${PAGE}` : `?limit=${PAGE}`
      const page = await api.get<Message[]>(`/conversations/${conversationId}/messages${q}`)
      set((s) => {
        const thread = s.threads[conversationId] ?? current
        return {
          threads: {
            ...s.threads,
            [conversationId]: {
              messages: mergeMessages(thread.messages, page),
              hasMore: page.length === PAGE,
              loading: false,
            },
          },
        }
      })
    },

    async send(conversationId, body) {
      const text = body.trim()
      if (!text) return
      // Prefer the socket; fall back to HTTP so a flaky connection never eats a message.
      const sent = realtime.send({ type: 'message.send', conversation_id: conversationId, body: text })
      if (!sent) {
        const message = await api.post<Message>(`/conversations/${conversationId}/messages`, { body: text })
        receive(message)
      }
    },

    receive,
  }
})
