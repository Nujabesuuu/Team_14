import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { api, ApiError } from '@/api/client'
import type { DiscoverCard, SwipeResult } from '@/api/types'
import { Avatar } from '@/design-system/Avatar'
import { Empty } from '@/design-system/Empty'
import { Panel } from '@/design-system/Panel'
import { PhantomButton } from '@/design-system/PhantomButton'
import { TopBar } from '@/design-system/TopBar'
import { useAuth } from '@/stores/auth'

/** Teamate+ only: who already liked you. Liking back is an instant match. */
export function Likes() {
  const navigate = useNavigate()
  const { me, setPremium } = useAuth()
  const premium = me?.user.is_premium ?? false
  const [likes, setLikes] = useState<DiscoverCard[] | null>(null)

  useEffect(() => {
    if (!premium) return
    api
      .get<DiscoverCard[]>('/likes/incoming')
      .then(setLikes)
      .catch(() => setLikes([]))
  }, [premium])

  const likeBack = async (card: DiscoverCard) => {
    try {
      const res = await api.post<SwipeResult>('/swipes', { to_user_id: card.user.id, direction: 'right' })
      setLikes((l) => (l ? l.filter((x) => x.user.id !== card.user.id) : l))
      if (res.match_created && res.match_id) navigate(`/match/${res.match_id}`)
    } catch (err) {
      alert(err instanceof ApiError ? err.message : 'Failed')
    }
  }

  return (
    <div className="screen">
      <TopBar title="Who likes you" back="/matches" kicker="Teamate+" />
      <div className="screen-scroll" style={{ padding: '14px 18px 24px', display: 'grid', gap: 12, alignContent: 'start' }}>
        {!premium && (
          <Panel tone="ink" ghost>
            <div className="display skew" style={{ fontSize: 30, color: 'var(--gold)' }}>
              See who already said yes
            </div>
            <p style={{ fontSize: 14, margin: '8px 0 14px' }}>
              Teamate+ shows incoming likes, removes the daily limit, lets you undo a swipe and ask for an early photo reveal.
              This demo build flips the flag instantly — no card required.
            </p>
            <PhantomButton variant="gold" block onClick={() => setPremium(true)}>
              Activate Teamate+ (demo)
            </PhantomButton>
          </Panel>
        )}
        {premium && likes && likes.length === 0 && <Empty title="No likes yet" hint="Host an event. Visibility beats waiting." />}
        {premium &&
          likes?.map((c) => (
            <div key={c.user.id} style={{ display: 'flex', gap: 12, alignItems: 'center', padding: '12px 14px', background: 'var(--ink-2)', clipPath: 'var(--cut-button)', borderLeft: '6px solid var(--gold)' }}>
              <Avatar avatar={c.user.avatar_key} accent={c.user.accent_color} size={52} />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div className="display" style={{ fontSize: 22 }}>
                  {c.user.display_name} <span className="cond" style={{ fontSize: 13, color: 'var(--gold)' }}>{c.compatibility}%</span>
                </div>
                <div className="muted" style={{ fontSize: 13, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {c.bio}
                </div>
              </div>
              <PhantomButton size="sm" variant="gold" onClick={() => likeBack(c)}>
                Like back
              </PhantomButton>
            </div>
          ))}
      </div>
    </div>
  )
}
