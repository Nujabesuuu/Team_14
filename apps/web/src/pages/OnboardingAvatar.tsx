import { motion } from 'framer-motion'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import type { AvatarKey } from '@/api/types'
import { AVATAR_KEYS, AVATAR_META, avatarSrc, hasPortrait, MASKS } from '@/avatars'
import { PhantomButton } from '@/design-system/PhantomButton'
import { accentPalette } from '@/design-system/tokens'
import { OnboardingFrame, Question } from '@/features/onboarding/OnboardingFrame'
import { useAuth } from '@/stores/auth'

export function OnboardingAvatar() {
  const navigate = useNavigate()
  const me = useAuth((s) => s.me)
  const updateProfile = useAuth((s) => s.updateProfile)
  const [avatar, setAvatar] = useState<AvatarKey>(me?.profile.avatar_key ?? 'duelist')
  const [accent, setAccent] = useState(me?.profile.accent_color ?? accentPalette[0])
  const [busy, setBusy] = useState(false)
  const HeroMask = MASKS[avatar]

  const pick = (key: AvatarKey) => {
    setAvatar(key)
    setAccent(AVATAR_META[key].accent)
  }

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
      title="Pick a hero"
      back="/onboarding/dna"
      footer={
        <PhantomButton block size="lg" disabled={busy} onClick={next}>
          {busy ? 'Saving' : 'Next: choose modes'}
        </PhantomButton>
      }
    >
      {/* Hero card: portrait on a paper sticker with the accent slab misprinted behind it. */}
      <div style={{ position: 'relative', margin: '4px 0 22px', padding: '0 6px' }}>
        <div aria-hidden style={{ position: 'absolute', inset: '10px -6px -10px 6px', background: accent, clipPath: 'var(--cut-card-alt)' }} />
        <motion.div
          key={avatar}
          initial={{ scale: 0.92, rotate: -3, opacity: 0 }}
          animate={{ scale: 1, rotate: 0, opacity: 1 }}
          transition={{ type: 'spring', stiffness: 260, damping: 20 }}
          style={{ position: 'relative', clipPath: 'var(--cut-card)', background: 'var(--paper)', padding: 8 }}
        >
          <div
            style={{
              position: 'relative',
              clipPath: 'var(--cut-card)',
              overflow: 'hidden',
              aspectRatio: '4 / 3',
              background: hasPortrait(avatar) ? 'var(--blood)' : 'var(--ink)',
              display: 'grid',
              placeItems: 'center',
            }}
          >
            {hasPortrait(avatar) ? (
              <img
                src={avatarSrc(avatar)}
                alt={`${AVATAR_META[avatar].name} portrait`}
                style={{ width: '100%', height: '100%', objectFit: 'cover', objectPosition: '50% 12%', display: 'block' }}
              />
            ) : (
              <HeroMask accent={accent} size={180} />
            )}
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, padding: '10px 8px 4px', color: 'var(--ink)' }}>
            <span className="display skew" style={{ fontSize: 36 }}>
              {AVATAR_META[avatar].name}
            </span>
            <span style={{ fontSize: 13, color: 'var(--ash-2)' }}>{AVATAR_META[avatar].tagline}</span>
          </div>
        </motion.div>
      </div>

      <Question title="Heroes" hint="This is how people see you before your photo. Pick your energy, not your looks.">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10 }}>
          {AVATAR_KEYS.map((key) => {
            const active = key === avatar
            return (
              <button
                key={key}
                type="button"
                onClick={() => pick(key)}
                aria-label={AVATAR_META[key].name}
                aria-pressed={active}
                style={{
                  aspectRatio: '1',
                  padding: active ? 3 : 0,
                  border: 0,
                  background: active ? 'var(--paper)' : 'transparent',
                  clipPath: 'var(--cut-chip)',
                  cursor: 'pointer',
                  boxShadow: active ? `4px 4px 0 ${AVATAR_META[key].accent}` : 'none',
                  opacity: active ? 1 : 0.72,
                  transition: 'opacity var(--dur-fast)',
                }}
              >
                {hasPortrait(key) ? (
                  <img
                    src={avatarSrc(key)}
                    alt=""
                    style={{ width: '100%', height: '100%', objectFit: 'cover', objectPosition: '50% 15%', display: 'block', clipPath: 'var(--cut-chip)' }}
                  />
                ) : (
                  <span style={{ display: 'grid', placeItems: 'center', width: '100%', height: '100%', background: 'var(--ink-2)', clipPath: 'var(--cut-chip)' }}>
                    <GridMask k={key} accent={active ? AVATAR_META[key].accent : '#F4F1EA'} />
                  </span>
                )}
              </button>
            )
          })}
        </div>
      </Question>

      <Question title="Accent" hint="Your color in chat, cards and the match screen.">
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

function GridMask({ k, accent }: { k: AvatarKey; accent: string }) {
  const Mask = MASKS[k]
  return <Mask accent={accent} size={54} />
}
