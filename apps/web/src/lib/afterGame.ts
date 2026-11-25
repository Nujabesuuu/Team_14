import type { Event } from '@/api/types'

/** Mirrors apps/api/app/domain/events.py and feedback.py — the server decides, this only picks what to show. */
export const MIN_PLAY_MS = 15 * 60_000

export type AfterGame =
  | { kind: 'none' }
  | { kind: 'confirm' }
  | { kind: 'too_short'; minutes: number }
  | { kind: 'waiting'; confirmations: number }
  | { kind: 'play_again'; leftMs: number }
  | { kind: 'expired' }

/** What a participant of a finished event sees under the lobby (US-07, US-11). */
export function afterGame(event: Event, now: number): AfterGame {
  if (event.status !== 'finished' || !event.is_participant) return { kind: 'none' }
  if (event.counted_at && event.feedback_closes_at) {
    const leftMs = Date.parse(event.feedback_closes_at) - now
    return leftMs > 0 ? { kind: 'play_again', leftMs } : { kind: 'expired' }
  }
  if (!event.started_at || !event.finished_at) return { kind: 'too_short', minutes: 0 }
  const playedMs = Date.parse(event.finished_at) - Date.parse(event.started_at)
  if (playedMs < MIN_PLAY_MS) return { kind: 'too_short', minutes: Math.floor(playedMs / 60_000) }
  return event.confirmed_by_me ? { kind: 'waiting', confirmations: event.confirmations } : { kind: 'confirm' }
}

/** "23h 59m" / "12m" — time left to answer "Play again?". */
export function formatLeft(ms: number): string {
  const minutes = Math.max(0, Math.floor(ms / 60_000))
  const h = Math.floor(minutes / 60)
  return h > 0 ? `${h}h ${minutes % 60}m` : `${minutes}m`
}
