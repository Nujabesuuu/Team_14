import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { api, ApiError } from '@/api/client'
import type { DiscoverCard, DiscoverResponse, Mode, SwipeDirection, SwipeResult } from '@/api/types'
import { Chip } from '@/design-system/Chip'
import { Empty } from '@/design-system/Empty'
import { PhantomButton } from '@/design-system/PhantomButton'
import { TopBar } from '@/design-system/TopBar'
import { SwipeDeck } from '@/features/discover/SwipeDeck'
import { MODE_LABEL } from '@/lib/format'
import { useAuth } from '@/stores/auth'

export function Discover() {
  const navigate = useNavigate()
  const me = useAuth((s) => s.me)
  const modes = me?.profile.modes ?? []
  const premium = me?.user.is_premium ?? false
  const [mode, setMode] = useState<Mode>(modes[0] ?? 'duo')
  const [cards, setCards] = useState<DiscoverCard[] | null>(null)
  const [rightsLeft, setRightsLeft] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [lastSwiped, setLastSwiped] = useState<DiscoverCard | null>(null)

  const load = useCallback(async (m: Mode) => {
    try {
      const res = await api.get<DiscoverResponse>(`/discover?mode=${m}`)
      setCards(res.cards)
      setRightsLeft(res.rights_left)
      setError(null)
    } catch (err) {
      setCards([])
      setError(err instanceof ApiError ? err.message : 'Could not load')
    }
  }, [])

  useEffect(() => {
    void load(mode)
  }, [mode, load])

  const swipe = async (card: DiscoverCard, direction: SwipeDirection) => {
    setCards((c) => (c ? c.filter((x) => x.user.id !== card.user.id) : c))
    setLastSwiped(card)
    try {
      const res = await api.post<SwipeResult>('/swipes', { to_user_id: card.user.id, direction })
      setRightsLeft(res.rights_left)
      if (res.match_created && res.match_id) navigate(`/match/${res.match_id}`)
    } catch (err) {
      if (err instanceof ApiError && err.code === 'SWIPE_LIMIT') {
        setError('Daily likes used up. Teamate+ removes the limit.')
        setCards((c) => (c ? [card, ...c] : c))
      }
    }
  }

  const undo = async () => {
    if (!lastSwiped) return
    try {
      await api.post('/swipes/undo')
      setCards((c) => (c ? [lastSwiped, ...c] : c))
      setLastSwiped(null)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Undo failed')
    }
  }

  return (
    <div className="screen">
      <TopBar
        title="Discover"
        kicker={rightsLeft === null ? 'Unlimited likes' : `${rightsLeft} likes left today`}
        right={
          premium && lastSwiped ? (
            <PhantomButton size="sm" variant="gold" onClick={undo}>
              Undo
            </PhantomButton>
          ) : undefined
        }
      />
      <div style={{ display: 'flex', gap: 8, padding: '8px 18px 0' }}>
        {modes.map((m) => (
          <Chip key={m} active={mode === m} onClick={() => setMode(m)} tone={m === 'dating' ? 'gold' : 'outline'}>
            {MODE_LABEL[m]}
          </Chip>
        ))}
      </div>
      {error && (
        <div style={{ margin: '10px 18px 0', padding: '10px 14px', background: 'var(--blood)', color: 'var(--chalk)', clipPath: 'var(--cut-button)', fontSize: 14, fontWeight: 600 }}>
          {error}
        </div>
      )}
      <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column', padding: '0 8px' }}>
        {cards && cards.length === 0 && !error && (
          <Empty title="Deck's empty" hint="Everyone in this mode has been seen. Host an event — that's where the real matches happen." action={<PhantomButton onClick={() => navigate('/events/new')}>Host an event</PhantomButton>} />
        )}
        {cards && cards.length > 0 && <SwipeDeck cards={cards} onSwipe={swipe} />}
      </div>
      {cards && cards.length > 0 && (
        <div style={{ display: 'flex', justifyContent: 'center', gap: 18, padding: '0 18px 14px' }}>
          <PhantomButton variant="ghost" onClick={() => swipe(cards[0], 'left')}>
            Nope
          </PhantomButton>
          <PhantomButton onClick={() => swipe(cards[0], 'right')}>Like</PhantomButton>
        </div>
      )}
    </div>
  )
}
