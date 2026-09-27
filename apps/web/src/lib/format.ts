export function formatWhen(iso: string): string {
  const d = new Date(iso)
  const now = new Date()
  const sameDay = d.toDateString() === now.toDateString()
  const tomorrow = new Date(now)
  tomorrow.setDate(now.getDate() + 1)
  const time = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  if (sameDay) return `Today ${time}`
  if (d.toDateString() === tomorrow.toDateString()) return `Tomorrow ${time}`
  return `${d.toLocaleDateString([], { weekday: 'short', day: 'numeric', month: 'short' })} ${time}`
}

export function formatClock(iso: string): string {
  return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

/** ISO string for "in N hours" rounded to the next half hour, used as event default. */
export function defaultStart(hoursAhead = 2): string {
  const d = new Date(Date.now() + hoursAhead * 3600_000)
  d.setMinutes(d.getMinutes() < 30 ? 30 : 60, 0, 0)
  return toLocalInput(d)
}

export function toLocalInput(d: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

export const MODE_LABEL: Record<string, string> = { duo: 'Duo', friends: 'Friends', dating: 'Dating' }
export const STATUS_LABEL: Record<string, string> = {
  open: 'Open',
  full: 'Full',
  in_progress: 'Live',
  finished: 'Finished',
  cancelled: 'Cancelled',
}
