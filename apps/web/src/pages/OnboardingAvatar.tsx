import { motion } from 'framer-motion'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import type { AvatarKey } from '@/api/types'
import { AVATAR_KEYS, AVATAR_META, AVATARS } from '@/avatars'
import { PhantomButton } from '@/design-system/PhantomButton'
import { accentPalette } from '@/design-system/tokens'
import { OnboardingFrame, Question } from '@/features/onboarding/OnboardingFrame'
import { useAuth } from '@/stores/auth'

export function OnboardingAvatar() {
  const navigate = useNavigate()
  const me = useAuth((s) => s.me)
  const updateProfile = useAuth((s) => s.updateProfile)
  const [avatar, setAvatar] = useState<AvatarKey>(me?.profile.avatar_key ?? 'raven')
  const [accent, setAccent] = useState(me?.profile.accent_color ?? accentPalette[0])
  const [busy, setBusy] = useState(false)

  const Mask = AVATARS[avatar]

  const next = async () => {
    setBusy(true)
    try {
      await updateProfile({ avatar_key: avatar, accent_color: accent })
      navigate('/onboarding/modes')
    } finally {
      setBusy(false)
    }
  }

  return (
    <OnboardingFrame
      step={2}
      title="Pick a mask"
      back="/onboarding/dna"
      footer={
        <PhantomButton block size="lg" disabled={busy} onClick={next}>
          {busy ? 'Saving…' : 'Next: choose modes'}
        </PhantomButton>
      }
    >
      <div style={{ display: 'grid', placeItems: 'center', padding: '6px 0 18px' }}>
        <motion.div
          key={avatar}
          initial={{ scale: 0.6, rotate: -18, opacity: 0 }}
          animate={{ scale: 1, rotate: 0, opacity: 1 }}
          transition={{ type: 'spring', stiffness: 260, damping: 18 }}
          style={{
            width: 200,
            height: 200,
            background: accent,
            clipPath: 'var(--cut-card-alt)',
            display: 'grid',
            placeItems: 'center',
          }}
        >
          <Mask accent="#0A0A0A" size={150} />
        </motion.div>
        <div className="display skew" style={{ fontSize: 34, marginTop: 14 }}>
          {AVATAR_META[avatar].name}
        </div>
        <div className="muted" style={{ fontSize: 14 }}>
          {AVATAR_META[avatar].tagline}
        </div>
      </div>

      <Question title="Masks" hint="This is how people see you before your photo. Choose your energy.">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10 }}>
          {AVATAR_KEYS.map((key) => {
            const M = AVATARS[key]
            const active = key === avatar
            return (
              <button
                key={key}
                type="button"
                onClick={() => setAvatar(key)}
                aria-label={AVATAR_META[key].name}
                aria-pressed={active}
                style={{
                  aspectRatio: '1',
                  background: active ? 'var(--paper)' : 'var(--ink-2)',
                  border: `2px solid ${active ? 'var(--paper)' : 'var(--ash-2)'}`,
                  clipPath: 'var(--cut-chip)',
                  display: 'grid',
                  placeItems: 'center',
                  cursor: 'pointer',
                  padding: 0,
                }}
              >
                <M accent={active ? accent : '#F4F1EA'} size={54} />
              </button>
            )
          })}
        </div>
      </Question>

      <Question title="Accent">
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          {accentPalette.map((c) => (
            <button
              key={c}
              type="button"
              aria-label={`Accent ${c}`}
              aria-pressed={c === accent}
              onClick={() => setAccent(c)}
              style={{
                width: 40,
                height: 40,
                background: c,
                border: `3px solid ${c === accent ? 'var(--paper)' : 'transparent'}`,
                clipPath: 'var(--cut-chip)',
                cursor: 'pointer',
              }}
            />
          ))}
        </div>
      </Question>
    </OnboardingFrame>
  )
}
