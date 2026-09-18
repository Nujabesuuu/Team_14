import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'

import type { Event } from '@/api/types'
import { Avatar } from '@/design-system/Avatar'
import { Chip } from '@/design-system/Chip'
import { formatWhen, STATUS_LABEL } from '@/lib/format'

export function EventCard({ event, index = 0 }: { event: Event; index?: number }) {
  const navigate = useNavigate()
  const filled = event.participants.length
  const isDate = event.kind === 'game_date'
  return (
    <motion.button
      type="button"
      onClick={() => navigate(`/events/${event.id}`)}
      initial={{ opacity: 0, x: -30, skewX: -6 }}
      animate={{ opacity: 1, x: 0, skewX: 0 }}
      transition={{ delay: index * 0.05, duration: 0.28, ease: [0.2, 0.9, 0.1, 1] }}
      style={{
        position: 'relative',
        display: 'block',
        width: '100%',
        padding: 0,
        border: 0,
        background: 'transparent',
        cursor: 'pointer',
        textAlign: 'left',
      }}
    >
      <div
        aria-hidden
        style={{
          position: 'absolute',
          inset: 0,
          transform: 'translate(5px, 5px)',
          background: isDate ? 'var(--gold)' : event.game.cover_color,
          clipPath: index % 2 ? 'var(--cut-card-alt)' : 'var(--cut-card)',
        }}
      />
      <div
        style={{
          position: 'relative',
          clipPath: index % 2 ? 'var(--cut-card-alt)' : 'var(--cut-card)',
          background: 'var(--paper)',
          color: 'var(--ink)',
          padding: '14px 16px 14px 18px',
          display: 'grid',
          gridTemplateColumns: '1fr auto',
          gap: 10,
        }}
      >
        <div style={{ minWidth: 0 }}>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 6 }}>
            <Chip tone="paper" style={{ background: event.game.cover_color, color: '#fff', borderColor: event.game.cover_color }}>
              {event.game.name}
            </Chip>
            {isDate && <Chip tone="gold">Game date</Chip>}
            {event.status !== 'open' && <Chip tone="blood">{STATUS_LABEL[event.status]}</Chip>}
          </div>
          <div className="display" style={{ fontSize: 24, lineHeight: 0.95, overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {event.title}
          </div>
          <div className="cond" style={{ fontSize: 13, marginTop: 6, color: 'var(--blood)' }}>
            {formatWhen(event.starts_at)}
          </div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 8 }}>
          <Avatar avatar={event.host.avatar_key} accent={event.host.accent_color} size={44} />
          <div className="display" style={{ fontSize: 26, lineHeight: 1 }}>
            {filled}
            <span style={{ fontSize: 16, opacity: 0.5 }}>/{event.max_slots}</span>
          </div>
        </div>
      </div>
    </motion.button>
  )
}
