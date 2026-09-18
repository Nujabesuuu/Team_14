import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'

import { PhantomButton } from '@/design-system/PhantomButton'
import { AVATARS } from '@/avatars'

const stagger = { hidden: { opacity: 0, x: -40 }, show: { opacity: 1, x: 0 } }

export function Welcome() {
  const navigate = useNavigate()
  return (
    <div className="screen" style={{ overflow: 'hidden' }}>
      {/* Diagonal red slab */}
      <div
        aria-hidden
        style={{
          position: 'absolute',
          top: -40,
          right: -120,
          width: 360,
          height: 640,
          background: 'var(--blood)',
          clipPath: 'polygon(30% 0, 100% 0, 100% 100%, 0 100%)',
          transform: 'rotate(8deg)',
        }}
      />
      <div style={{ position: 'absolute', top: 70, right: 24, opacity: 0.95 }}>
        <motion.div
          initial={{ rotate: -14, scale: 0.6, opacity: 0 }}
          animate={{ rotate: -8, scale: 1, opacity: 1 }}
          transition={{ delay: 0.25, type: 'spring', stiffness: 220, damping: 16 }}
        >
          <AVATARS.kitsune accent="#0A0A0A" size={150} />
        </motion.div>
      </div>

      <motion.div
        initial="hidden"
        animate="show"
        transition={{ staggerChildren: 0.09, delayChildren: 0.1 }}
        style={{ position: 'relative', marginTop: 'auto', padding: '0 26px 40px' }}
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
          Find a teammate. Play a round. If it clicks, get closer — photos stay blurred until you both say so.
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
