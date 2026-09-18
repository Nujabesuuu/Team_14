import { motion } from 'framer-motion'
import { useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { Avatar } from '@/design-system/Avatar'
import { PhantomButton } from '@/design-system/PhantomButton'
import { useAuth } from '@/stores/auth'
import { useMatches } from '@/stores/matches'

/** The red screen. Two masks slam in from the edges; the headline stamps on top. */
export function MatchCelebration() {
  const { id = '' } = useParams()
  const navigate = useNavigate()
  const me = useAuth((s) => s.me)
  const match = useMatches((s) => s.list.find((m) => m.id === id))
  const { get, clearCelebration } = useMatches()

  useEffect(() => {
    clearCelebration()
    if (!match) get(id).catch(() => navigate('/matches', { replace: true }))
  }, [id, match, get, clearCelebration, navigate])

  if (!match || !me) return <div className="screen" style={{ background: 'var(--blood)' }} />

  const slam = (from: number) => ({
    initial: { x: from, rotate: from > 0 ? 25 : -25, opacity: 0 },
    animate: { x: 0, rotate: from > 0 ? 6 : -6, opacity: 1 },
    transition: { type: 'spring' as const, stiffness: 280, damping: 18, delay: 0.1 },
  })

  return (
    <div className="screen" style={{ background: 'var(--blood)', overflow: 'hidden', justifyContent: 'center' }}>
      <div
        aria-hidden
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: 'repeating-linear-gradient(-30deg, transparent 0 26px, rgba(10,10,10,0.12) 26px 30px)',
        }}
      />
      <div style={{ position: 'relative', display: 'flex', justifyContent: 'center', gap: -20 }}>
        <motion.div {...slam(-240)} style={{ marginRight: -18, zIndex: 1 }}>
          <Avatar avatar={me.profile.avatar_key} accent={me.profile.accent_color} size={150} />
        </motion.div>
        <motion.div {...slam(240)} style={{ marginLeft: -18 }}>
          <Avatar avatar={match.other.avatar_key} accent={match.other.accent_color} size={150} />
        </motion.div>
      </div>
      <motion.div
        initial={{ scale: 3, opacity: 0, rotate: -10 }}
        animate={{ scale: 1, opacity: 1, rotate: -6 }}
        transition={{ delay: 0.45, type: 'spring', stiffness: 300, damping: 14 }}
        className="display"
        style={{
          position: 'relative',
          textAlign: 'center',
          fontSize: 76,
          lineHeight: 0.85,
          color: 'var(--paper)',
          textShadow: '6px 6px 0 var(--ink)',
          marginTop: 28,
        }}
      >
        It's a<br />match
      </motion.div>
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8 }}
        style={{ position: 'relative', textAlign: 'center', color: 'var(--chalk)', padding: '18px 40px 0', fontSize: 16 }}
      >
        You and <strong>{match.other.display_name}</strong> both want to get closer. Photos just got a little clearer.
        <br />
        <span className="cond" style={{ fontSize: 13, opacity: 0.85 }}>
          {match.compatibility}% Game DNA match
        </span>
      </motion.p>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1 }}
        style={{ position: 'relative', display: 'grid', gap: 12, padding: '28px 32px 0' }}
      >
        <PhantomButton variant="paper" size="lg" block onClick={() => navigate(`/chat/${match.conversation_id}`, { replace: true })}>
          Say something
        </PhantomButton>
        <PhantomButton variant="ghost" block onClick={() => navigate('/matches', { replace: true })}>
          Later
        </PhantomButton>
      </motion.div>
    </div>
  )
}
