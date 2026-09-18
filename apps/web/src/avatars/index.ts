import type { AvatarKey } from '@/api/types'

/**
 * Eight hero archetypes, generated as stylised portraits (see apps/api/scripts/generate_images.py).
 * They evoke roles any gamer recognises without copying characters from existing games.
 */
export const AVATAR_KEYS: AvatarKey[] = [
  'duelist',
  'sage',
  'impostor',
  'builder',
  'pilot',
  'operator',
  'vanguard',
  'strategist',
]

export const AVATAR_META: Record<AvatarKey, { name: string; tagline: string; accent: string }> = {
  duelist: { name: 'Duelist', tagline: 'First in, last to flinch.', accent: '#D8323C' },
  sage: { name: 'Sage', tagline: 'Keeps everyone alive. Roasts them after.', accent: '#3AA46B' },
  impostor: { name: 'Impostor', tagline: 'Definitely not sus.', accent: '#2FA7B8' },
  builder: { name: 'Builder', tagline: 'Farms first, fights later.', accent: '#6E9F3A' },
  pilot: { name: 'Pilot', tagline: 'Aerials, not apologies.', accent: '#3B7DD8' },
  operator: { name: 'Operator', tagline: 'One shot. Usually.', accent: '#7C8797' },
  vanguard: { name: 'Vanguard', tagline: 'The wall the team hides behind.', accent: '#E07A3F' },
  strategist: { name: 'Strategist', tagline: 'Calls the play before it happens.', accent: '#8E5CC8' },
}

export function avatarSrc(key: AvatarKey | 'guide'): string {
  return `/avatars/${key}.jpg`
}
