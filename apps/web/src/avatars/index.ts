import type { FC } from 'react'

import type { AvatarKey } from '@/api/types'
import { Builder } from './Builder'
import { Duelist } from './Duelist'
import { Impostor } from './Impostor'
import { Operator } from './Operator'
import { Pilot } from './Pilot'
import { Sage } from './Sage'
import { Strategist } from './Strategist'
import { Vanguard } from './Vanguard'

export interface MaskProps {
  accent: string
  size?: number
}

/**
 * Eight hero archetypes. Each has an original SVG mask; some also have a generated
 * flat cel-shaded portrait in public/avatars/<key>.jpg (see PORTRAIT_KEYS).
 * Archetypes evoke roles any gamer recognises without copying existing game characters.
 */
export const MASKS: Record<AvatarKey, FC<MaskProps>> = {
  duelist: Duelist,
  sage: Sage,
  impostor: Impostor,
  builder: Builder,
  pilot: Pilot,
  operator: Operator,
  vanguard: Vanguard,
  strategist: Strategist,
}

export const AVATAR_KEYS = Object.keys(MASKS) as AvatarKey[]

/** Keys that ship with a generated portrait. Add a key here after dropping its jpg into public/avatars. */
export const PORTRAIT_KEYS: ReadonlySet<AvatarKey> = new Set<AvatarKey>([])

export const AVATAR_META: Record<AvatarKey, { name: string; tagline: string; accent: string }> = {
  duelist: { name: 'Duelist', tagline: 'First in, last to flinch.', accent: '#E60012' },
  sage: { name: 'Sage', tagline: 'Keeps everyone alive. Roasts them after.', accent: '#2ECC71' },
  impostor: { name: 'Impostor', tagline: 'Definitely not sus.', accent: '#F5C518' },
  builder: { name: 'Builder', tagline: 'Farms first, fights later.', accent: '#8BC34A' },
  pilot: { name: 'Pilot', tagline: 'Aerials, not apologies.', accent: '#1E90FF' },
  operator: { name: 'Operator', tagline: 'One shot. Usually.', accent: '#607D8B' },
  vanguard: { name: 'Vanguard', tagline: 'The wall the team hides behind.', accent: '#FF6B35' },
  strategist: { name: 'Strategist', tagline: 'Calls the play before it happens.', accent: '#9B59B6' },
}

export function hasPortrait(key: AvatarKey): boolean {
  return PORTRAIT_KEYS.has(key)
}

export function avatarSrc(key: AvatarKey): string {
  return `/avatars/${key}.jpg`
}
