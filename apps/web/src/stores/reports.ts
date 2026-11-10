import { create } from 'zustand'

import { api } from '@/api/client'
import type { ModerationReport, MyReport, ReportCreate, ReportDecision } from '@/api/types'
import { useAuth } from '@/stores/auth'

interface ReportsState {
  /** Reports I sent, newest first. */
  mine: MyReport[]
  mineLoaded: boolean
  /** Moderator only: reports waiting for a decision. */
  queue: ModerationReport[]
  /** Moderator only: reports that already have a decision. */
  decided: ModerationReport[]
  queueLoaded: boolean
  submit: (input: ReportCreate) => Promise<MyReport>
  loadMine: () => Promise<void>
  loadQueue: () => Promise<void>
  decide: (id: string, decision: ReportDecision) => Promise<ModerationReport>
}

const EMPTY = { mine: [], mineLoaded: false, queue: [], decided: [], queueLoaded: false }

export const useReports = create<ReportsState>((set) => ({
  ...EMPTY,

  async submit(input) {
    const report = await api.post<MyReport>('/reports', input)
    set((s) => ({ mine: [report, ...s.mine] }))
    return report
  },

  async loadMine() {
    set({ mine: await api.get<MyReport[]>('/reports/mine'), mineLoaded: true })
  },

  async loadQueue() {
    const all = await api.get<ModerationReport[]>('/moderation/reports')
    set({
      queue: all.filter((r) => r.status === 'new'),
      decided: all.filter((r) => r.status !== 'new'),
      queueLoaded: true,
    })
  },

  async decide(id, decision) {
    const report = await api.post<ModerationReport>(`/moderation/reports/${id}/decision`, { decision })
    set((s) => ({ queue: s.queue.filter((r) => r.id !== id), decided: [report, ...s.decided] }))
    return report
  },
}))

// Two demo accounts can share one tab: never show one person's reports or the queue to the next.
useAuth.subscribe((state, previous) => {
  if (previous.token && !state.token) useReports.setState(EMPTY)
})
