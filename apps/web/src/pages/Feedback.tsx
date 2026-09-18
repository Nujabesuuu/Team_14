import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { api, ApiError } from '@/api/client'
import type { FeedbackAnswer, FeedbackResult, PendingFeedback, PublicUser } from '@/api/types'
import { Avatar } from '@/design-system/Avatar'
import { Empty } from '@/design-system/Empty'
import { PhantomButton } from '@/design-system/PhantomButton'
import { TopBar } from '@/design-system/TopBar'

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
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    api
      .get<PendingFeedback>(`/events/${id}/feedback`)
      .then((r) => setQueue(r.pending))
      .catch((err) => setError(err instanceof ApiError ? err.message : 'Could not load'))
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
      setError(err instanceof ApiError ? err.message : 'Could not send')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="screen">
      <TopBar title="Play again?" back={`/events/${id}`} kicker="After the game" />
      <div className="screen-scroll" style={{ padding: '20px 22px 32px' }}>
        {error && <Empty title="Not yet" hint={error} action={<PhantomButton onClick={() => navigate(-1)}>Back</PhantomButton>} />}
        {!error && queue && !current && (
          <Empty
            title="All rated"
            hint="If someone also picked “get closer”, you'll see a match screen the moment they answer."
            action={<PhantomButton onClick={() => navigate('/matches')}>Go to matches</PhantomButton>}
          />
        )}
        {current && (
            <div key={current.id} className="deal-in">
              <div style={{ display: 'grid', placeItems: 'center', gap: 10, marginBottom: 26 }}>
                <Avatar avatar={current.avatar_key} accent={current.accent_color} size={120} />
                <div className="display skew" style={{ fontSize: 40 }}>
                  {current.display_name}
                </div>
                <div className="muted">{queue!.length > 1 ? `${queue!.length - 1} more after this` : 'Last one'}</div>
              </div>
              <div style={{ display: 'grid', gap: 16 }}>
                {OPTIONS.map((o) => (
                  <div key={o.value}>
                    <PhantomButton block size="lg" variant={o.variant} onClick={() => answer(o.value)} disabled={busy}>
                      {o.label}
                    </PhantomButton>
                    <div className="muted" style={{ fontSize: 13, textAlign: 'center', marginTop: 6 }}>
                      {o.sub}
                    </div>
                  </div>
                ))}
              </div>
            </div>
        )}
      </div>
    </div>
  )
}
