import { AnimatePresence, motion } from 'framer-motion'
import type { ReactNode } from 'react'
import { useLocation } from 'react-router-dom'

/**
 * Route transition: the new screen slides in while a red diagonal slab
 * wipes across. Keyed on pathname so every navigation gets the effect.
 */
export function Wipe({ children }: { children: ReactNode }) {
  const { pathname } = useLocation()
  return (
    <AnimatePresence mode="wait" initial={false}>
      <motion.div
        key={pathname}
        style={{ position: 'relative', flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}
        initial={{ opacity: 0, x: 24 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: -24 }}
        transition={{ duration: 0.18, ease: [0.2, 0.9, 0.1, 1] }}
      >
        <motion.div
          aria-hidden
          style={{
            position: 'absolute',
            inset: 0,
            background: 'var(--blood)',
            clipPath: 'polygon(0 0, 100% 0, 80% 100%, 0 100%)',
            zIndex: 30,
            pointerEvents: 'none',
            transformOrigin: 'left',
          }}
          initial={{ scaleX: 1 }}
          animate={{ scaleX: 0 }}
          transition={{ duration: 0.26, ease: [0.7, 0, 0.2, 1] }}
        />
        {children}
      </motion.div>
    </AnimatePresence>
  )
}
