import type { FC } from 'react'

import type { AvatarKey } from '@/api/types'
import { Jester } from './Jester'
import { Kitsune } from './Kitsune'
import { Marionette } from './Marionette'
import { Nomad } from './Nomad'
import { Oracle } from './Oracle'
import { Raven } from './Raven'
import { Sentinel } from './Sentinel'
import { Vesper } from './Vesper'

export interface MaskProps {
  accent: string
  size?: number
}

/**
 * Eight original masks. Each is a flat, high-contrast silhouette in paper + ink with one accent.
 * They are inspired by theatrical masks, not by any existing characters.
 */
export const AVATARS: Record<AvatarKey, FC<MaskProps>> = {
  raven: Raven,
  jester: Jester,
  kitsune: Kitsune,
  marionette: Marionette,
  sentinel: Sentinel,
  vesper: Vesper,
  nomad: Nomad,
  oracle: Oracle,
}

export const AVATAR_KEYS = Object.keys(AVATARS) as AvatarKey[]

export const AVATAR_META: Record<AvatarKey, { name: string; tagline: string }> = {
  raven: { name: 'Raven', tagline: 'Sees everything. Says little.' },
  jester: { name: 'Jester', tagline: 'Chaos with a smile.' },
  kitsune: { name: 'Kitsune', tagline: 'Sly, quick, loyal.' },
  marionette: { name: 'Marionette', tagline: 'Pulls strings. Never pulled.' },
  sentinel: { name: 'Sentinel', tagline: 'The wall the team hides behind.' },
  vesper: { name: 'Vesper', tagline: 'Night owl. Late queue.' },
  nomad: { name: 'Nomad', tagline: 'No main. Every map.' },
  oracle: { name: 'Oracle', tagline: 'Calls the play before it happens.' },
}
