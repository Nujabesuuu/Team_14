import { motion } from 'framer-motion'

import type { Message, PublicUser } from '@/api/types'
import { Avatar } from '@/design-system/Avatar'
import { formatClock } from '@/lib/format'

interface Props {
  message: Message
  mine: boolean
  author: PublicUser | null
  /** First message in a run from the same sender shows the avatar chip. */
  first: boolean
}

/**
 * Persona-style speech: parallelogram slabs with a sharp tail.
 * Theirs — paper on ink, mask peeking from behind. Mine — ink with a red edge, right-aligned.
 */
export function MessageBubble({ message, mine, author, first }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, x: mine ? 40 : -40, skewX: mine ? 8 : -8 }}
      animate={{ opacity: 1, x: 0, skewX: 0 }}
      transition={{ duration: 0.22, ease: [0.2, 0.9, 0.1, 1] }}
      style={{
        display: 'flex',
        justifyContent: mine ? 'flex-end' : 'flex-start',
        alignItems: 'flex-end',
        gap: 8,
        marginTop: first ? 14 : 4,
      }}
    >
      {!mine && (
        <div style={{ width: 36, flexShrink: 0, visibility: first ? 'visible' : 'hidden' }}>
          {author && <Avatar avatar={author.avatar_key} accent={author.accent_color} size={36} />}
        </div>
      )}
      <div style={{ position: 'relative', maxWidth: '78%' }}>
        {mine && (
          <div
            aria-hidden
            style={{
              position: 'absolute',
              inset: 0,
              transform: 'translate(3px, 3px)',
              background: 'var(--blood)',
              clipPath: 'var(--cut-bubble-me)',
            }}
          />
        )}
        <div
          style={{
            position: 'relative',
            padding: '10px 14px',
            background: mine ? 'var(--ink)' : 'var(--paper)',
            color: mine ? 'var(--paper)' : 'var(--ink)',
            clipPath: mine ? 'var(--cut-bubble-me)' : 'var(--cut-bubble-them)',
            border: mine ? '2px solid var(--paper)' : undefined,
            fontSize: 15,
            lineHeight: 1.35,
            wordBreak: 'break-word',
          }}
        >
          {message.body}
          <span
            className="cond"
            style={{ display: 'block', marginTop: 4, fontSize: 10, opacity: 0.55, textAlign: mine ? 'right' : 'left' }}
          >
            {formatClock(message.created_at)}
          </span>
        </div>
      </div>
    </motion.div>
  )
}
