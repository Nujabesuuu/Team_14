/** Mirrors apps/api/app/schemas. Keep in sync when the API changes. */

export type AvatarKey =
  | 'raven'
  | 'jester'
  | 'kitsune'
  | 'marionette'
  | 'sentinel'
  | 'vesper'
  | 'nomad'
  | 'oracle'

export type Mode = 'duo' | 'friends' | 'dating'
export type Role = 'support' | 'carry' | 'flex' | 'tank' | 'igl'
export type Playstyle = 'casual' | 'competitive'
export type Comms = 'voice' | 'text' | 'both'
export type EventKind = 'squad' | 'game_date'
export type EventStatus = 'open' | 'full' | 'in_progress' | 'finished' | 'cancelled'
export type FeedbackAnswer = 'again' | 'closer' | 'no'
export type SwipeDirection = 'left' | 'right'
export type MatchSource = 'post_game' | 'mutual_like'

export interface Account {
  id: string
  email: string
  display_name: string
  age: number
  is_premium: boolean
}

export interface PublicUser {
  id: string
  display_name: string
  age: number
  avatar_key: AvatarKey
  accent_color: string
  photo_url: string | null
  is_premium: boolean
}

export interface Game {
  id: string
  name: string
  slug: string
  is_chill: boolean
  cover_color: string
}

export interface ProfileGame {
  id: string
  name: string
  slug: string
  rank: string | null
}

export interface Profile {
  bio: string
  avatar_key: AvatarKey
  accent_color: string
  photo_url: string | null
  modes: Mode[]
  role: Role | null
  playstyle: Playstyle | null
  comms: Comms | null
  schedule: string[]
  toxicity_tolerance: number
  timezone: string
  games: ProfileGame[]
  onboarded: boolean
}

export interface Me {
  user: Account
  profile: Profile
}

export interface ProfileUpdate {
  display_name?: string
  bio?: string
  avatar_key?: AvatarKey
  accent_color?: string
  modes?: Mode[]
  role?: Role
  playstyle?: Playstyle
  comms?: Comms
  schedule?: string[]
  toxicity_tolerance?: number
  timezone?: string
  games?: { game_id: string; rank?: string | null }[]
}

export interface TokenResponse {
  access_token: string
  token_type: 'bearer'
  user: Account
}

export interface Event {
  id: string
  host: PublicUser
  game: Game
  kind: EventKind
  title: string
  starts_at: string
  max_slots: number
  status: EventStatus
  participants: PublicUser[]
  is_host: boolean
  is_participant: boolean
  created_at: string
}

export interface EventCreate {
  game_id: string
  kind: EventKind
  title: string
  starts_at: string
  max_slots: number
}

export interface PendingFeedback {
  pending: PublicUser[]
  done: string[]
}

export interface FeedbackResult {
  match_created: boolean
  match_id: string | null
}

export interface Message {
  id: string
  conversation_id: string
  sender_id: string
  body: string
  created_at: string
}

export interface RevealState {
  my_stage: number
  their_stage: number
  my_consent: boolean
  their_consent: boolean
  early_request_from_me: boolean
  early_request_from_them: boolean
}

export interface Match {
  id: string
  other: PublicUser
  source: MatchSource
  conversation_id: string
  reveal: RevealState
  compatibility: number
  last_message: Message | null
  created_at: string
}

export interface DiscoverCard {
  user: PublicUser
  bio: string
  modes: Mode[]
  role: Role | null
  playstyle: Playstyle | null
  comms: Comms | null
  schedule: string[]
  games: ProfileGame[]
  compatibility: number
}

export interface DiscoverResponse {
  cards: DiscoverCard[]
  rights_left: number | null
}

export interface SwipeResult {
  match_created: boolean
  match_id: string | null
  rights_left: number | null
}

/** Server → client WebSocket events. */
export type WsEvent =
  | { type: 'message.new'; message: Message }
  | { type: 'match.new'; match: Match }
  | { type: 'reveal.updated'; match?: Match; match_id?: string }
  | { type: 'event.updated'; event: Event }
  | { type: 'pong' }
  | { type: 'error'; code: string; detail: string }

export const SCHEDULE_SLOTS = ['morning', 'afternoon', 'evening', 'night', 'weekend'] as const
export const ROLES: { value: Role; label: string; hint: string }[] = [
  { value: 'support', label: 'Support', hint: 'I keep the team alive' },
  { value: 'carry', label: 'Carry', hint: 'I take the fights' },
  { value: 'tank', label: 'Tank', hint: 'I absorb the damage' },
  { value: 'igl', label: 'IGL', hint: 'I call the shots' },
  { value: 'flex', label: 'Flex', hint: 'Whatever the team needs' },
]
