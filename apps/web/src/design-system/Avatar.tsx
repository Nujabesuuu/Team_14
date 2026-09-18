import { AVATAR_META, avatarSrc } from '@/avatars'
import type { AvatarKey } from '@/api/types'

interface Props {
  avatar: AvatarKey
  accent: string
  size?: number
  /** Paper ring + hard accent shadow: the Phantom UI sticker look. */
  framed?: boolean
  /** Override the portrait (e.g. the demo guide). */
  src?: string
}

/** Hero portrait in a round sticker: paper border, hard accent offset shadow. */
export function Avatar({ avatar, accent, size = 48, framed = true, src }: Props) {
  const meta = AVATAR_META[avatar] ?? AVATAR_META.duelist
  const ring = size >= 96 ? 4 : 3
  return (
    <div
      data-testid="avatar"
      data-avatar={avatar}
      style={{
        width: size,
        height: size,
        borderRadius: '50%',
        background: 'var(--ink)',
        border: framed ? `${ring}px solid var(--paper)` : undefined,
        boxShadow: framed ? `${ring + 1}px ${ring + 1}px 0 ${accent}` : undefined,
        overflow: 'hidden',
        flexShrink: 0,
      }}
    >
      <img
        src={src ?? avatarSrc(avatar)}
        alt={`${meta.name} portrait`}
        width={size}
        height={size}
        loading="lazy"
        style={{ width: '100%', height: '100%', objectFit: 'cover', objectPosition: '50% 20%', display: 'block' }}
      />
    </div>
  )
}
