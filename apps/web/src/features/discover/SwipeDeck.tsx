import { AnimatePresence, motion, useMotionValue, useTransform } from 'framer-motion'
import { useState } from 'react'

import type { DiscoverCard, SwipeDirection } from '@/api/types'
import { Chip } from '@/design-system/Chip'
import { Stamp } from '@/design-system/Stamp'
import { RevealPhoto } from '@/features/matches/RevealPhoto'
import { MODE_LABEL } from '@/lib/format'

const THRESHOLD = 110

interface Props {
  cards: DiscoverCard[]
  onSwipe: (card: DiscoverCard, direction: SwipeDirection) => Promise<void> | void
}

/** Drag-to-swipe deck. Top card is interactive; the next one peeks from behind, slightly rotated. */
export function SwipeDeck({ cards, onSwipe }: Props) {
  const top = cards[0]
  const next = cards[1]
  return (
    <div style={{ position: 'relative', flex: 1, minHeight: 0 }}>
      {next && (
        <div style={{ position: 'absolute', inset: '14px 10px 30px', transform: 'rotate(-3deg) scale(0.96)', opacity: 0.7 }}>
          <CardFace card={next} stage={0} />
        </div>
      )}
      <AnimatePresence>{top && <DraggableCard key={top.user.id} card={top} onSwipe={onSwipe} />}</AnimatePresence>
    </div>
  )
}

function DraggableCard({ card, onSwipe }: { card: DiscoverCard; onSwipe: Props['onSwipe'] }) {
  const x = useMotionValue(0)
  const rotate = useTransform(x, [-250, 250], [-14, 14])
  const likeOpacity = useTransform(x, [30, THRESHOLD], [0, 1])
  const nopeOpacity = useTransform(x, [-THRESHOLD, -30], [1, 0])
  const [exitX, setExitX] = useState<number | null>(null)

  const fling = (direction: SwipeDirection) => {
    setExitX(direction === 'right' ? 600 : -600)
    void onSwipe(card, direction)
  }

  return (
    <motion.div
      style={{ position: 'absolute', inset: '14px 10px 30px', x, rotate, cursor: 'grab', touchAction: 'none' }}
      drag="x"
      dragElastic={0.9}
      dragConstraints={{ left: 0, right: 0 }}
      onDragEnd={(_, info) => {
        if (info.offset.x > THRESHOLD) fling('right')
        else if (info.offset.x < -THRESHOLD) fling('left')
      }}
      initial={false}
      exit={{ x: exitX ?? 0, opacity: 0, rotate: exitX && exitX > 0 ? 20 : -20, transition: { duration: 0.28 } }}
      whileTap={{ cursor: 'grabbing' }}
    >
      {/* Entrance is a CSS keyframe: Motion's `initial` on a presence child stalls under StrictMode. */}
      <div className="deal-in" style={{ height: '100%' }}>
        <CardFace card={card} stage={0} />
      </div>
      <motion.div style={{ position: 'absolute', top: 26, left: 22, opacity: likeOpacity }}>
        <Stamp text="Like" tone="paper" style={{ transform: 'rotate(-14deg)', animation: 'none' }} />
      </motion.div>
      <motion.div style={{ position: 'absolute', top: 26, right: 22, opacity: nopeOpacity }}>
        <Stamp text="Nope" tone="blood" style={{ transform: 'rotate(14deg)', animation: 'none' }} />
      </motion.div>
    </motion.div>
  )
}

export function CardFace({ card, stage }: { card: DiscoverCard; stage: number }) {
  const u = card.user
  return (
    <div style={{ position: 'relative', height: '100%' }}>
      <div aria-hidden style={{ position: 'absolute', inset: 0, transform: 'translate(6px, 6px)', background: u.accent_color, clipPath: 'var(--cut-card)' }} />
      <div
        style={{
          position: 'relative',
          height: '100%',
          clipPath: 'var(--cut-card)',
          background: 'var(--paper)',
          color: 'var(--ink)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
      >
        <div style={{ position: 'relative', height: '46%', background: 'var(--ink)', display: 'grid', placeItems: 'center' }}>
          <RevealPhoto photoUrl={u.photo_url} stage={stage} avatar={u.avatar_key} accent={u.accent_color} size={170} />
          <div
            className="display"
            style={{
              position: 'absolute',
              right: 14,
              bottom: 10,
              fontSize: 54,
              color: 'var(--blood)',
              lineHeight: 1,
              textShadow: '3px 3px 0 var(--paper)',
            }}
          >
            {card.compatibility}
            <span style={{ fontSize: 22 }}>%</span>
          </div>
        </div>
        <div style={{ padding: '14px 18px', overflow: 'hidden', flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
            <span className="display skew" style={{ fontSize: 34 }}>
              {u.display_name}
            </span>
            <span className="cond" style={{ fontSize: 15, color: 'var(--blood)' }}>
              {u.age}
            </span>
          </div>
          <p style={{ margin: '6px 0 10px', fontSize: 15, lineHeight: 1.35 }}>{card.bio || 'No bio. Mystery build.'}</p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {card.role && <Chip tone="blood">{card.role}</Chip>}
            {card.playstyle && <Chip tone="paper" style={{ borderColor: 'var(--ink)' }}>{card.playstyle}</Chip>}
            {card.comms && <Chip tone="paper" style={{ borderColor: 'var(--ink)' }}>{card.comms}</Chip>}
            {card.modes.map((m) => (
              <Chip key={m} tone="paper" style={{ borderColor: 'var(--ash-2)', color: 'var(--ash-2)' }}>
                {MODE_LABEL[m]}
              </Chip>
            ))}
          </div>
          <div className="cond" style={{ marginTop: 10, fontSize: 13, color: 'var(--ash-2)' }}>
            {card.games.map((g) => g.name).join(' · ')}
          </div>
        </div>
      </div>
    </div>
  )
}
