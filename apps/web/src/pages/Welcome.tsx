import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'

import { avatarSrc } from '@/avatars'
import { PhantomButton } from '@/design-system/PhantomButton'

const stagger = { hidden: { opacity: 0, x: -40 }, show: { opacity: 1, x: 0 } }

export function Welcome() {
  const navigate = useNavigate()
  return (
    <div className="screen" style={{ overflow: 'hidden' }}>
      {/* Red diagonal slab, then the hero portrait as a tilted paper sticker on top of it. */}
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
          height: 300,
          clipPath: 'var(--cut-card)',
          background: 'var(--paper)',
          padding: 8,
        }}
      >
        <div style={{ width: '100%', height: '100%', clipPath: 'var(--cut-card)', overflow: 'hidden', background: 'var(--ink)' }}>
          <img
            src={avatarSrc('duelist')}
            alt=""
            style={{ width: '100%', height: '100%', objectFit: 'cover', objectPosition: '55% 10%', display: 'block', filter: 'contrast(1.08) saturate(1.05)' }}
          />
        </div>
        <div
          className="cond"
          style={{
            position: 'absolute',
            left: -10,
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
        <motion.div variants={stagger} className="cond" style={{ color: 'var(--blood)', fontSize: 14 }}>
          Game first. Faces later.
        </motion.div>
        <motion.h1
          variants={stagger}
          className="display skew"
          style={{ fontSize: 88, margin: '4px 0 0', color: 'var(--paper)', lineHeight: 0.86 }}
        >
          Team
          <br />
          <span style={{ color: 'var(--blood)', textShadow: '4px 4px 0 var(--paper)' }}>ate</span>
        </motion.h1>
        <motion.p variants={stagger} style={{ fontSize: 16, maxWidth: 300, marginTop: 18, color: 'var(--muted)' }}>
          Find a teammate. Play a round. If it clicks, get closer. Photos stay blurred until you both say so.
        </motion.p>
        <motion.div variants={stagger} style={{ display: 'grid', gap: 14, marginTop: 28 }}>
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
