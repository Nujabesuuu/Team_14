import { AVATAR_META, avatarSrc, hasPortrait, MASKS } from '@/avatars'
import type { AvatarKey } from '@/api/types'

interface Props {
  avatar: AvatarKey
  accent: string
  size?: number
  /** Paper ring + hard accent shadow: the Phantom UI sticker look. */
  framed?: boolean
}

/**
 * Hero avatar in a round sticker: paper border, hard accent offset shadow.
 * Uses the generated portrait when the archetype has one, otherwise its SVG mask.
 */
export function Avatar({ avatar, accent, size = 48, framed = true }: Props) {
  const Mask = MASKS[avatar] ?? MASKS.duelist
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
        display: 'grid',
        placeItems: 'center',
        overflow: 'hidden',
        flexShrink: 0,
      }}
    >
      {hasPortrait(avatar) ? (
        <img
          src={avatarSrc(avatar)}
          alt={`${meta.name} portrait`}
          width={size}
          height={size}
          loading="lazy"
          style={{ width: '100%', height: '100%', objectFit: 'cover', objectPosition: '50% 18%', display: 'block' }}
        />
      ) : (
        <Mask accent={accent} size={size * 0.78} />
      )}
    </div>
  )
}
