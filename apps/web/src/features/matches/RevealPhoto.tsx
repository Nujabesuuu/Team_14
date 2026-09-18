import type { CSSProperties } from 'react'

import { mediaUrl } from '@/api/client'
import type { AvatarKey } from '@/api/types'
import { Avatar } from '@/design-system/Avatar'
import { blurPx } from '@/lib/reveal'

interface Props {
  photoUrl: string | null
  stage: number
  avatar: AvatarKey
  accent: string
  size?: number
  style?: CSSProperties
}

/**
 * The other person's photo at *their* reveal stage. No photo → the mask.
 * Blur is applied with an overscaled image so edges never leak the unblurred pixels.
 */
export function RevealPhoto({ photoUrl, stage, avatar, accent, size = 96, style }: Props) {
  const url = mediaUrl(photoUrl)
  if (!url) return <Avatar avatar={avatar} accent={accent} size={size} />
  const blur = blurPx(stage)
  return (
    <div
      data-testid="reveal-photo"
      data-stage={stage}
      style={{
        width: size,
        height: size,
        overflow: 'hidden',
        clipPath: 'var(--cut-card-alt)',
        background: 'var(--ink-2)',
        position: 'relative',
        flexShrink: 0,
        ...style,
      }}
    >
      <img
        src={url}
        alt=""
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          transform: blur ? 'scale(1.15)' : undefined,
          filter: `blur(${blur}px) grayscale(${stage === 0 ? 1 : 0})`,
          transition: 'filter 900ms var(--ease-snap), transform 900ms var(--ease-snap)',
        }}
      />
      {stage < 3 && (
        <div
          aria-hidden
          style={{
            position: 'absolute',
            right: -2,
            bottom: -2,
            padding: '2px 8px',
            background: 'var(--ink)',
            color: 'var(--paper)',
            fontFamily: 'var(--font-cond)',
            fontSize: 11,
            letterSpacing: '0.08em',
            clipPath: 'var(--cut-chip)',
          }}
        >
          {stage}/3
        </div>
      )}
    </div>
  )
}
