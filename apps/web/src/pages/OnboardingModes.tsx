import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { ApiError } from '@/api/client'
import type { Mode } from '@/api/types'
import { PhantomButton } from '@/design-system/PhantomButton'
import { OnboardingFrame, Question } from '@/features/onboarding/OnboardingFrame'
import { ModeToggles } from '@/features/profile/ModeToggles'
import { useAuth } from '@/stores/auth'

export function OnboardingModes() {
  const navigate = useNavigate()
  const me = useAuth((s) => s.me)
  const updateProfile = useAuth((s) => s.updateProfile)
  const [modes, setModes] = useState<Mode[]>(me?.profile.modes.length ? me.profile.modes : ['duo'])
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const finish = async () => {
    setBusy(true)
    setError(null)
    try {
      await updateProfile({ modes })
      navigate('/events', { replace: true })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not save')
    } finally {
      setBusy(false)
    }
  }

  return (
    <OnboardingFrame
      step={3}
      title="What are you here for?"
      back="/onboarding/avatar"
      footer={
        <PhantomButton block size="lg" disabled={!modes.length || busy} onClick={finish}>
          {busy ? 'Saving…' : 'Enter Teamate'}
        </PhantomButton>
      }
    >
      <Question title="Modes" hint="You can change these any time. People only see you in modes you share.">
        <ModeToggles value={modes} onChange={setModes} age={me?.user.age ?? 0} />
        {error && (
          <p style={{ color: 'var(--blood)', fontWeight: 600, marginTop: 10 }}>{error}</p>
        )}
      </Question>
    </OnboardingFrame>
  )
}
