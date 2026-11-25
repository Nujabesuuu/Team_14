import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { ApiError } from '@/api/client'
import type { PublicUser } from '@/api/types'
import { Avatar } from '@/design-system/Avatar'
import { Chip } from '@/design-system/Chip'
import { Panel } from '@/design-system/Panel'
import { PhantomButton } from '@/design-system/PhantomButton'
import { TopBar } from '@/design-system/TopBar'
import { ReportSheet } from '@/features/reports/ReportSheet'
import { afterGame, formatLeft } from '@/lib/afterGame'
import { formatWhen, STATUS_LABEL } from '@/lib/format'
import { useAuth } from '@/stores/auth'
import { type EventAction, useEvents } from '@/stores/events'

export function EventDetail() {
  const { id = '' } = useParams()
  const navigate = useNavigate()
  const me = useAuth((s) => s.me)
  const event = useEvents((s) => s.byId[id])
  const { load, act } = useEvents()
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [reporting, setReporting] = useState<PublicUser | null>(null)
  // Ticks the "answer within" countdown and flips to "time's up" without a reload.
  const [now, setNow] = useState(() => Date.now())

  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 30_000)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    load(id).catch(() => navigate('/events', { replace: true }))
  }, [id, load, navigate])

  if (!event) return <div className="screen" />

  const run = async (action: EventAction) => {
    setBusy(true)
    setError(null)
    try {
      await act(id, action)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Action failed')
    } finally {
      setBusy(false)
    }
  }

  const isDate = event.kind === 'game_date'
  const status = event.status
  const actions = (() => {
    if (status === 'finished') {
      const after = afterGame(event, now)
      switch (after.kind) {
        case 'confirm':
          return (
            <div style={{ display: 'grid', gap: 8 }}>
              <PhantomButton block size="lg" onClick={() => run('confirm')} disabled={busy}>
                We played — confirm
              </PhantomButton>
              <div className="muted" style={{ fontSize: 13, textAlign: 'center' }}>
                The game counts when 2 players confirm it. Then you get to answer "play again?".
              </div>
            </div>
          )
        case 'waiting':
          return (
            <Panel tone="ink">
              <div className="cond" style={{ color: 'var(--blood)' }}>
                Confirmed {after.confirmations}/2
              </div>
              <div style={{ fontSize: 14 }}>Waiting for a teammate to confirm the game.</div>
            </Panel>
          )
        case 'too_short':
          return (
            <Panel tone="ink">
              <div className="cond" style={{ color: 'var(--blood)' }}>
                Not counted
              </div>
              <div style={{ fontSize: 14 }}>
                {after.minutes > 0 ? `You played ${after.minutes} min. ` : ''}A game counts from 15 minutes of play, so there is no
                "play again?" this time.
              </div>
            </Panel>
          )
        case 'play_again':
          return (
            <div style={{ display: 'grid', gap: 8 }}>
              <PhantomButton block size="lg" onClick={() => navigate(`/events/${id}/feedback`)}>
                Play again?
              </PhantomButton>
              <div className="muted" style={{ fontSize: 13, textAlign: 'center' }}>
                Answer within {formatLeft(after.leftMs)}. Nobody sees a one-sided answer.
              </div>
            </div>
          )
        case 'expired':
          return (
            <Panel tone="ink">
              <div className="cond" style={{ color: 'var(--blood)' }}>
                Time's up
              </div>
              <div style={{ fontSize: 14 }}>The 24 hours to answer "play again?" have passed.</div>
            </Panel>
          )
        default:
          return null
      }
    }
    if (status === 'cancelled') return null
    if (event.is_host) {
      return (
        <div style={{ display: 'grid', gap: 12 }}>
          {status === 'in_progress' ? (
            <PhantomButton block size="lg" onClick={() => run('finish')} disabled={busy}>
              We're done — finish
            </PhantomButton>
          ) : (
            <PhantomButton block size="lg" onClick={() => run('start')} disabled={busy}>
              {event.participants.length > 1 ? 'Start the game' : 'Start anyway'}
            </PhantomButton>
          )}
          {status !== 'in_progress' && (
            <PhantomButton block variant="danger" onClick={() => run('cancel')} disabled={busy}>
              Cancel event
            </PhantomButton>
          )}
        </div>
      )
    }
    if (event.is_participant) {
      return status === 'in_progress' ? (
        <Panel tone="ink">
          <div className="cond" style={{ color: 'var(--blood)' }}>
            Game in progress
          </div>
          <div style={{ fontSize: 14 }}>
            The host finishes the event when you're done. Then you both confirm you played: games of 15+ minutes count.
          </div>
        </Panel>
      ) : (
        <PhantomButton block variant="ghost" onClick={() => run('leave')} disabled={busy}>
          Leave
        </PhantomButton>
      )
    }
    return (
      <PhantomButton block size="lg" onClick={() => run('join')} disabled={busy || status !== 'open'}>
        {status === 'open' ? (isDate ? 'Take the seat' : 'Join squad') : STATUS_LABEL[status]}
      </PhantomButton>
    )
  })()

  return (
    <div className="screen">
      <TopBar title={event.game.name} back="/events" kicker={isDate ? 'Game date' : 'Squad'} />
      <div className="screen-scroll" style={{ padding: '14px 22px 24px', display: 'grid', gap: 18, alignContent: 'start' }}>
        <Panel ghost tone="paper">
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 8 }}>
            <Chip tone="blood">{STATUS_LABEL[status]}</Chip>
            {event.counted_at && <Chip tone="gold">Counted</Chip>}
            {isDate && <Chip tone="gold">2 seats</Chip>}
          </div>
          <div className="display skew" style={{ fontSize: 34, lineHeight: 0.95 }}>
            {event.title}
          </div>
          <div className="cond" style={{ fontSize: 15, color: 'var(--blood)', marginTop: 10 }}>
            {formatWhen(event.starts_at)}
          </div>
        </Panel>

        <section>
          <div className="cond" style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 10 }}>
            Squad {event.participants.length}/{event.max_slots}
          </div>
          <div style={{ display: 'grid', gap: 10 }}>
            {event.participants.map((p) => (
              <div
                key={p.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  padding: '10px 14px',
                  background: 'var(--ink-2)',
                  clipPath: 'var(--cut-button)',
                }}
              >
                <Avatar avatar={p.avatar_key} accent={p.accent_color} size={44} />
                <div style={{ flex: 1 }}>
                  <div className="cond" style={{ fontSize: 17 }}>
                    {p.display_name}
                    {p.id === me?.user.id && <span className="muted"> · you</span>}
                  </div>
                  <div className="muted" style={{ fontSize: 13 }}>
                    {p.id === event.host.id ? 'Host' : 'Player'} · {p.age}
                  </div>
                </div>
                {p.is_premium && <Chip tone="gold">+</Chip>}
                {event.is_participant && p.id !== me?.user.id && (
                  <Chip onClick={() => setReporting(p)} aria-label={`Report ${p.display_name}`}>
                    Report
                  </Chip>
                )}
              </div>
            ))}
            {Array.from({ length: Math.max(0, event.max_slots - event.participants.length) }).map((_, i) => (
              <div
                key={`empty-${i}`}
                className="cond"
                style={{
                  padding: '14px',
                  border: '2px dashed var(--ash-2)',
                  clipPath: 'var(--cut-button)',
                  color: 'var(--ash-2)',
                  textAlign: 'center',
                  fontSize: 13,
                }}
              >
                Open seat
              </div>
            ))}
          </div>
        </section>

        {error && <p style={{ color: 'var(--blood)', fontWeight: 600, margin: 0 }}>{error}</p>}
        {actions}
      </div>

      {reporting && <ReportSheet target={reporting} context="event" contextId={event.id} onClose={() => setReporting(null)} />}
    </div>
  )
}
