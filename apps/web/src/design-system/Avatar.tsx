import { AVATARS } from '@/avatars'
import type { AvatarKey } from '@/api/types'

interface Props {
  avatar: AvatarKey
  accent: string
  size?: number
  /** Ring the avatar with the ink border and accent shadow used in chat and lists. */
  framed?: boolean
}

/** Renders one of the 8 masks inside a circular chip. */
export function Avatar({ avatar, accent, size = 48, framed = true }: Props) {
  const Mask = AVATARS[avatar] ?? AVATARS.raven
  return (
    <div
      style={{
        width: size,
        height: size,
        borderRadius: '50%',
        background: 'var(--ink)',
        border: framed ? `3px solid var(--paper)` : undefined,
        boxShadow: framed ? `3px 3px 0 ${accent}` : undefined,
        display: 'grid',
        placeItems: 'center',
        overflow: 'hidden',
        flexShrink: 0,
      }}
    >
      <Mask accent={accent} size={size * 0.78} />
    </div>
  )
}
