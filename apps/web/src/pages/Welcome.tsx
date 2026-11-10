import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'

import { avatarSrc, hasPortrait, MASKS } from '@/avatars'
import { Panel } from '@/design-system/Panel'
import { PhantomButton } from '@/design-system/PhantomButton'
import { useAuth } from '@/stores/auth'

const stagger = { hidden: { opacity: 0, x: -40 }, show: { opacity: 1, x: 0 } }
const HERO = 'duelist' as const

export function Welcome() {
  const navigate = useNavigate()
  const notice = useAuth((s) => s.notice)
  const HeroMask = MASKS[HERO]
  return (
    <div className="screen" style={{ overflow: 'hidden' }}>
      {/* Red diagonal slab, then the hero as a tilted paper sticker on top of it. */}
      <motion.div
        aria-hidden
        initial={{ x: 120, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ duration: 0.5, ease: [0.2, 0.9, 0.1, 1] }}
        style={{
          position: 'absolute',
          top: -30,
          right: -90,
          width: 360,
          height: 620,
          background: 'var(--blood)',
          clipPath: 'polygon(28% 0, 100% 0, 100% 100%, 0 100%)',
          transform: 'rotate(8deg)',
        }}
      />
      <motion.div
        initial={{ rotate: -12, scale: 0.7, opacity: 0, x: 60 }}
        animate={{ rotate: -6, scale: 1, opacity: 1, x: 0 }}
        transition={{ delay: 0.2, type: 'spring', stiffness: 200, damping: 18 }}
        style={{
          position: 'absolute',
          top: 54,
          right: 18,
          width: 236,
          height: 290,
          clipPath: 'var(--cut-card)',
          background: 'var(--paper)',
          padding: 8,
        }}
      >
        <div
          style={{
            width: '100%',
            height: '100%',
            clipPath: 'var(--cut-card)',
            overflow: 'hidden',
            background: hasPortrait(HERO) ? 'var(--blood)' : 'var(--ink)',
            display: 'grid',
            placeItems: 'center',
          }}
        >
          {hasPortrait(HERO) ? (
            <img src={avatarSrc(HERO)} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover', objectPosition: '50% 10%', display: 'block' }} />
          ) : (
            <HeroMask accent="var(--blood)" size={170} />
          )}
        </div>
        <div
          className="cond"
          style={{
            position: 'absolute',
            left: 6,
            bottom: 22,
            padding: '5px 12px',
            background: 'var(--ink)',
            color: 'var(--paper)',
            clipPath: 'var(--cut-chip)',
            fontSize: 13,
            transform: 'rotate(-4deg)',
          }}
        >
          Duelist
        </div>
      </motion.div>

      <motion.div
        initial="hidden"
        animate="show"
        transition={{ staggerChildren: 0.09, delayChildren: 0.25 }}
        style={{ position: 'relative', marginTop: 'auto', padding: '0 26px calc(32px + var(--safe-bottom))' }}
      >
        {notice && (
          <Panel tone="paper" role="alert" style={{ marginBottom: 18 }}>
            <div className="cond" style={{ fontSize: 12, color: 'var(--blood)' }}>
              Session ended
            </div>
            <div style={{ fontSize: 15, fontWeight: 600, marginTop: 4 }}>{notice}</div>
          </Panel>
        )}
        <motion.div variants={stagger} className="cond" style={{ color: 'var(--blood)', fontSize: 14 }}>
          Game first. Faces later.
        </motion.div>
        <motion.h1
          variants={stagger}
          className="display skew"
          style={{ fontSize: 74, margin: '6px 0 0', color: 'var(--paper)', lineHeight: 0.9, textShadow: '5px 5px 0 var(--blood)' }}
        >
          Teamate
        </motion.h1>
        <motion.p variants={stagger} style={{ fontSize: 16, maxWidth: 300, marginTop: 16, color: 'var(--muted)' }}>
          Find a teammate. Play a round. If it clicks, get closer. Photos stay blurred until you both say so.
        </motion.p>
        <motion.div variants={stagger} style={{ display: 'grid', gap: 14, marginTop: 26 }}>
          <PhantomButton size="lg" block onClick={() => navigate('/register')}>
            Create profile
          </PhantomButton>
          <PhantomButton variant="ghost" block onClick={() => navigate('/login')}>
            I have an account
          </PhantomButton>
        </motion.div>
      </motion.div>
    </div>
  )
}
