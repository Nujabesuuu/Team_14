import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { api, ApiError } from '@/api/client'
import type { Event, FeedbackAnswer, FeedbackResult, PendingFeedback, PublicUser } from '@/api/types'
import { Avatar } from '@/design-system/Avatar'
import { Empty } from '@/design-system/Empty'
import { PhantomButton } from '@/design-system/PhantomButton'
import { TopBar } from '@/design-system/TopBar'
import { afterGame } from '@/lib/afterGame'

/** Codes that mean "there is nothing to answer here", each with its own title. Anything else is a plain error. */
const CLOSED: Record<string, string> = {
  FEEDBACK_WINDOW_CLOSED: "Time's up",
  GAME_NOT_COUNTED: 'Not counted',
  EVENT_NOT_FINISHED: 'Not yet',
}

const OPTIONS: { value: FeedbackAnswer; label: string; sub: string; variant: 'paper' | 'primary' | 'ghost' }[] = [
  { value: 'again', label: 'Play again', sub: 'Solid teammate. Same time next week.', variant: 'paper' },
  { value: 'closer', label: 'Get closer', sub: 'Private. Only shows if they feel the same.', variant: 'primary' },
  { value: 'no', label: 'Nope', sub: 'No hard feelings.', variant: 'ghost' },
]

/** "Play again?" — one teammate at a time. A mutual "closer" becomes a match. */
export function Feedback() {
  const { id = '' } = useParams()
  const navigate = useNavigate()
  const [queue, setQueue] = useState<PublicUser[] | null>(null)
  const [closerAllowed, setCloserAllowed] = useState<Record<string, boolean>>({})
  const [error, setError] = useState<{ title: string; hint: string } | null>(null)
  const [busy, setBusy] = useState(false)

  const fail = (err: unknown, fallback: string) =>
    setError(
      err instanceof ApiError
        ? { title: CLOSED[err.code] ?? 'Something went wrong', hint: err.message }
        : { title: 'Something went wrong', hint: fallback },
    )

  useEffect(() => {
    // The event says when the 24 hours end, so a late visitor sees "Time's up" before tapping anything (US-12).
    Promise.all([api.get<PendingFeedback>(`/events/${id}/feedback`), api.get<Event>(`/events/${id}`)])
      .then(([r, event]) => {
        if (afterGame(event, Date.now()).kind === 'expired') {
          setError({ title: CLOSED.FEEDBACK_WINDOW_CLOSED, hint: 'The 24 hours to answer "play again?" have passed.' })
          return
        }
        setQueue(r.pending)
        setCloserAllowed(r.closer_allowed)
      })
      .catch((err) => fail(err, 'Could not load'))
  }, [id])

  const current = queue?.[0]

  const answer = async (value: FeedbackAnswer) => {
    if (!current || busy) return
    setBusy(true)
    try {
      const res = await api.post<FeedbackResult>(`/events/${id}/feedback`, { to_user_id: current.id, answer: value })
      if (res.match_created && res.match_id) {
        navigate(`/match/${res.match_id}`, { replace: true })
        return
      }
      setQueue((q) => (q ? q.slice(1) : q))
    } catch (err) {
      fail(err, 'Could not send')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="screen">
      <TopBar title="Play again?" back={`/events/${id}`} kicker="After the game" />
      <div className="screen-scroll" style={{ padding: '20px 22px 32px' }}>
        {error && (
          <Empty
            title={error.title}
            hint={error.hint}
            action={<PhantomButton onClick={() => navigate(`/events/${id}`)}>Back to the event</PhantomButton>}
          />
        )}
        {!error && queue && !current && (
          <Empty
            title="All rated"
            hint="If someone also picked “get closer”, you'll see a match screen the moment they answer."
            action={<PhantomButton onClick={() => navigate('/matches')}>Go to matches</PhantomButton>}
          />
        )}
        {!error && current && (
            <div key={current.id} className="deal-in">
              <div style={{ display: 'grid', placeItems: 'center', gap: 10, marginBottom: 26 }}>
                <Avatar avatar={current.avatar_key} accent={current.accent_color} size={120} />
                <div className="display skew" style={{ fontSize: 40 }}>
                  {current.display_name}
                </div>
                <div className="muted">{queue!.length > 1 ? `${queue!.length - 1} more after this` : 'Last one'}</div>
              </div>
              <div style={{ display: 'grid', gap: 16 }}>
                {OPTIONS.map((o) => {
                  // US-11: "closer" only when both have Dating on. The server refuses it anyway (CLOSER_REQUIRES_DATING).
                  const locked = o.value === 'closer' && !closerAllowed[current.id]
                  return (
                    <div key={o.value}>
                      <PhantomButton
                        block
                        size="lg"
                        variant={o.variant}
                        onClick={() => answer(o.value)}
                        disabled={busy || locked}
                      >
                        {o.label}
                      </PhantomButton>
                      <div className="muted" style={{ fontSize: 13, textAlign: 'center', marginTop: 6 }}>
                        {locked ? 'Available only when you both have Dating on.' : o.sub}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
        )}
      </div>
    </div>
  )
}
