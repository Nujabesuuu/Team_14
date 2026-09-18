import { motion } from 'framer-motion'
import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

import { Chip } from '@/design-system/Chip'
import { Empty } from '@/design-system/Empty'
import { PhantomButton } from '@/design-system/PhantomButton'
import { TopBar } from '@/design-system/TopBar'
import { RevealPhoto } from '@/features/matches/RevealPhoto'
import { formatClock } from '@/lib/format'
import { useAuth } from '@/stores/auth'
import { useMatches } from '@/stores/matches'

export function Matches() {
  const navigate = useNavigate()
  const premium = useAuth((s) => s.me?.user.is_premium)
  const { list, loaded, load } = useMatches()

  useEffect(() => {
    void load()
  }, [load])

  return (
    <div className="screen">
      <TopBar
        title="Matches"
        right={
          <PhantomButton size="sm" variant={premium ? 'gold' : 'ghost'} onClick={() => navigate('/likes')}>
            Likes
          </PhantomButton>
        }
      />
      <div className="screen-scroll" style={{ padding: '10px 18px 24px', display: 'grid', gap: 12, alignContent: 'start' }}>
        {loaded && list.length === 0 && (
          <Empty
            title="No matches yet"
            hint="Join an event, play, and pick “get closer”. Or swipe in Discover."
            action={<PhantomButton onClick={() => navigate('/events')}>Find an event</PhantomButton>}
          />
        )}
        {list.map((m, i) => (
          <motion.button
            key={m.id}
            type="button"
            onClick={() => navigate(`/chat/${m.conversation_id}`)}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.04 }}
            style={{
              display: 'grid',
              gridTemplateColumns: 'auto 1fr auto',
              gap: 14,
              alignItems: 'center',
              padding: '12px 14px',
              background: 'var(--ink-2)',
              color: 'var(--paper)',
              border: 0,
              borderLeft: `6px solid ${m.other.accent_color}`,
              clipPath: 'var(--cut-button)',
              textAlign: 'left',
              cursor: 'pointer',
            }}
          >
            <RevealPhoto
              photoUrl={m.other.photo_url}
              stage={m.reveal.their_stage}
              avatar={m.other.avatar_key}
              accent={m.other.accent_color}
              size={62}
            />
            <div style={{ minWidth: 0 }}>
              <div style={{ display: 'flex', gap: 8, alignItems: 'baseline' }}>
                <span className="display" style={{ fontSize: 22 }}>
                  {m.other.display_name}
                </span>
                <span className="cond" style={{ fontSize: 12, color: 'var(--blood)' }}>
                  {m.compatibility}%
                </span>
              </div>
              <div className="muted" style={{ fontSize: 14, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {m.last_message ? m.last_message.body : m.source === 'post_game' ? 'Matched after a game' : 'Matched by mutual like'}
              </div>
            </div>
            <div style={{ display: 'grid', gap: 6, justifyItems: 'end' }}>
              {m.last_message && (
                <span className="muted" style={{ fontSize: 12 }}>
                  {formatClock(m.last_message.created_at)}
                </span>
              )}
              {m.reveal.their_consent && !m.reveal.my_consent && <Chip tone="blood">Reveal?</Chip>}
              {m.reveal.early_request_from_them && <Chip tone="gold">Early</Chip>}
            </div>
          </motion.button>
        ))}
      </div>
    </div>
  )
}
