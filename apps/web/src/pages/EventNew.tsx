import { type FormEvent, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { ApiError } from '@/api/client'
import type { EventKind } from '@/api/types'
import { Chip } from '@/design-system/Chip'
import { Field } from '@/design-system/Field'
import { PhantomButton } from '@/design-system/PhantomButton'
import { TopBar } from '@/design-system/TopBar'
import { defaultStart } from '@/lib/format'
import { useAuth } from '@/stores/auth'
import { useEvents } from '@/stores/events'

export function EventNew() {
  const navigate = useNavigate()
  const me = useAuth((s) => s.me)
  const { games, loadGames, create } = useEvents()
  const [kind, setKind] = useState<EventKind>('squad')
  const [pickedGameId, setGameId] = useState<string>('')
  const [title, setTitle] = useState('')
  const [startsAt, setStartsAt] = useState(defaultStart())
  const [slots, setSlots] = useState(2)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const canDate = Boolean(me?.profile.modes.includes('dating'))
  const myGames = useMemo(() => new Set(me?.profile.games.map((g) => g.id)), [me])
  const choices = useMemo(() => {
    const pool = kind === 'game_date' ? games.filter((g) => g.is_chill) : games
    return [...pool].sort((a, b) => Number(myGames.has(b.id)) - Number(myGames.has(a.id)))
  }, [games, kind, myGames])

  // The picked game must exist in the current pool (switching to Game Date narrows it to chill games).
  const gameId = choices.some((g) => g.id === pickedGameId) ? pickedGameId : (choices[0]?.id ?? '')

  useEffect(() => {
    void loadGames()
  }, [loadGames])

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const event = await create({
        game_id: gameId,
        kind,
        title: title.trim(),
        starts_at: new Date(startsAt).toISOString(),
        max_slots: kind === 'game_date' ? 2 : slots,
      })
      navigate(`/events/${event.id}`, { replace: true })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not create the event')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="screen">
      <TopBar title="Host an event" back="/events" />
      <form onSubmit={submit} className="screen-scroll" style={{ padding: '16px 22px 32px', display: 'grid', gap: 18, alignContent: 'start' }}>
        <div>
          <span className="cond" style={{ fontSize: 13, color: 'var(--muted)' }}>
            Type
          </span>
          <div style={{ display: 'flex', gap: 8, marginTop: 6 }}>
            <Chip active={kind === 'squad'} onClick={() => setKind('squad')}>
              Squad
            </Chip>
            <Chip
              active={kind === 'game_date'}
              tone="gold"
              disabled={!canDate}
              onClick={() => canDate && setKind('game_date')}
              title={canDate ? '' : 'Enable Dating mode (18+) to host a game date'}
              style={{ opacity: canDate ? 1 : 0.4 }}
            >
              Game date
            </Chip>
          </div>
          {kind === 'game_date' && (
            <p className="muted" style={{ fontSize: 13, marginTop: 8 }}>
              Two seats, chill games only. Ranked is not a first date.
            </p>
          )}
        </div>

        <div>
          <span className="cond" style={{ fontSize: 13, color: 'var(--muted)' }}>
            Game
          </span>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 6 }}>
            {choices.map((g) => (
              <Chip key={g.id} active={g.id === gameId} onClick={() => setGameId(g.id)}>
                {g.name}
              </Chip>
            ))}
          </div>
        </div>

        <Field
          label="Title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder={kind === 'game_date' ? 'Overcooked, no shouting' : 'Duo to Diamond tonight'}
          minLength={3}
          maxLength={80}
          required
        />
        <Field label="Starts" type="datetime-local" value={startsAt} onChange={(e) => setStartsAt(e.target.value)} required />

        {kind === 'squad' && (
          <div>
            <span className="cond" style={{ fontSize: 13, color: 'var(--muted)' }}>
              Seats (including you)
            </span>
            <div style={{ display: 'flex', gap: 8, marginTop: 6 }}>
              {[2, 3, 4, 5, 6, 8, 10].map((n) => (
                <Chip key={n} active={slots === n} onClick={() => setSlots(n)} style={{ minWidth: 40, justifyContent: 'center' }}>
                  {n}
                </Chip>
              ))}
            </div>
          </div>
        )}

        {error && <p style={{ color: 'var(--blood)', fontWeight: 600, margin: 0 }}>{error}</p>}
        <PhantomButton size="lg" block type="submit" disabled={busy || !gameId}>
          {busy ? 'Posting…' : 'Post event'}
        </PhantomButton>
      </form>
    </div>
  )
}
