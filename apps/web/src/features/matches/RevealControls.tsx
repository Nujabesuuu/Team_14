import { useState } from 'react'

import { ApiError } from '@/api/client'
import type { Match } from '@/api/types'
import { Chip } from '@/design-system/Chip'
import { PhantomButton } from '@/design-system/PhantomButton'
import { REVEAL_LABEL } from '@/lib/reveal'
import { useAuth } from '@/stores/auth'
import { useMatches } from '@/stores/matches'

/** Consent buttons for the gradual reveal. Reads like a two-key launch: both must turn. */
export function RevealControls({ match }: { match: Match }) {
  const premium = useAuth((s) => s.me?.user.is_premium)
  const { consent, earlyRequest, earlyAccept } = useMatches()
  const [error, setError] = useState<string | null>(null)
  const r = match.reveal
  const wrap = (fn: () => Promise<unknown>) => async () => {
    setError(null)
    try {
      await fn()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed')
    }
  }

  const done = r.my_stage === 3 && r.their_stage === 3
  return (
    <div style={{ display: 'grid', gap: 10 }}>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
        <Chip tone={done ? 'gold' : 'paper'}>{REVEAL_LABEL[r.their_stage]}</Chip>
        <span className="muted" style={{ fontSize: 13 }}>
          {done
            ? 'Both photos are clear.'
            : r.my_consent && !r.their_consent
              ? 'You said yes. Waiting for them.'
              : r.their_consent && !r.my_consent
                ? `${match.other.display_name} wants to reveal. Your call.`
                : 'Reveal only happens when you both agree.'}
        </span>
      </div>
      {!done && (
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <PhantomButton size="sm" variant={r.their_consent ? 'primary' : 'paper'} onClick={wrap(() => consent(match.id))} disabled={r.my_consent}>
            {r.my_consent ? 'You agreed' : 'Reveal photos'}
          </PhantomButton>
          {r.early_request_from_them && (
            <PhantomButton size="sm" variant="gold" onClick={wrap(() => earlyAccept(match.id))}>
              Accept early reveal
            </PhantomButton>
          )}
          {premium && !r.early_request_from_me && !r.early_request_from_them && (
            <PhantomButton size="sm" variant="gold" onClick={wrap(() => earlyRequest(match.id))}>
              Ask to reveal now
            </PhantomButton>
          )}
          {r.early_request_from_me && <Chip tone="gold">Early request sent</Chip>}
        </div>
      )}
      {error && (
        <span style={{ color: 'var(--blood)', fontSize: 13, fontWeight: 600 }}>{error}</span>
      )}
    </div>
  )
}
