import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { ROLES, SCHEDULE_SLOTS, type Comms, type Playstyle, type Role } from '@/api/types'
import { Chip } from '@/design-system/Chip'
import { PhantomButton } from '@/design-system/PhantomButton'
import { TextArea } from '@/design-system/Field'
import { OnboardingFrame, Question } from '@/features/onboarding/OnboardingFrame'
import { useAuth } from '@/stores/auth'
import { useEvents } from '@/stores/events'

/** Game DNA: the questions the compatibility score is built from. */
export function OnboardingDna() {
  const navigate = useNavigate()
  const me = useAuth((s) => s.me)
  const updateProfile = useAuth((s) => s.updateProfile)
  const { games, loadGames } = useEvents()

  const [selectedGames, setSelectedGames] = useState<string[]>(me?.profile.games.map((g) => g.id) ?? [])
  const [role, setRole] = useState<Role | null>(me?.profile.role ?? null)
  const [playstyle, setPlaystyle] = useState<Playstyle | null>(me?.profile.playstyle ?? null)
  const [comms, setComms] = useState<Comms | null>(me?.profile.comms ?? null)
  const [schedule, setSchedule] = useState<string[]>(me?.profile.schedule ?? [])
  const [toxicity, setToxicity] = useState(me?.profile.toxicity_tolerance ?? 3)
  const [bio, setBio] = useState(me?.profile.bio ?? '')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    void loadGames()
  }, [loadGames])

  const toggle = (list: string[], value: string, set: (v: string[]) => void) =>
    set(list.includes(value) ? list.filter((v) => v !== value) : [...list, value])

  const valid = selectedGames.length > 0 && role && playstyle && comms && schedule.length > 0

  const next = async () => {
    if (!valid) return
    setBusy(true)
    try {
      await updateProfile({
        games: selectedGames.map((id) => ({ game_id: id })),
        role: role!,
        playstyle: playstyle!,
        comms: comms!,
        schedule,
        toxicity_tolerance: toxicity,
        bio,
      })
      navigate('/onboarding/avatar')
    } finally {
      setBusy(false)
    }
  }

  return (
    <OnboardingFrame
      step={1}
      title="Game DNA"
      footer={
        <PhantomButton block size="lg" disabled={!valid || busy} onClick={next}>
          {busy ? 'Saving…' : 'Next: pick a mask'}
        </PhantomButton>
      }
    >
      <Question title="What do you play?" hint="Pick everything you actually queue for.">
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {games.map((g) => (
            <Chip key={g.id} active={selectedGames.includes(g.id)} onClick={() => toggle(selectedGames, g.id, setSelectedGames)}>
              {g.name}
              {g.is_chill && <span style={{ opacity: 0.7 }}>· chill</span>}
            </Chip>
          ))}
        </div>
      </Question>

      <Question title="Your role" hint="How you show up in a team.">
        <div style={{ display: 'grid', gap: 8 }}>
          {ROLES.map((r) => (
            <button
              key={r.value}
              type="button"
              onClick={() => setRole(r.value)}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '12px 16px',
                background: role === r.value ? 'var(--paper)' : 'var(--ink-2)',
                color: role === r.value ? 'var(--ink)' : 'var(--paper)',
                border: '2px solid',
                borderColor: role === r.value ? 'var(--paper)' : 'var(--ash-2)',
                clipPath: 'var(--cut-button)',
                cursor: 'pointer',
                textAlign: 'left',
              }}
            >
              <span className="cond" style={{ fontSize: 17 }}>
                {r.label}
              </span>
              <span style={{ fontSize: 13, opacity: 0.75 }}>{r.hint}</span>
            </button>
          ))}
        </div>
      </Question>

      <Question title="Playstyle">
        <div style={{ display: 'flex', gap: 8 }}>
          <Chip active={playstyle === 'casual'} onClick={() => setPlaystyle('casual')}>
            For fun
          </Chip>
          <Chip active={playstyle === 'competitive'} onClick={() => setPlaystyle('competitive')}>
            For the win
          </Chip>
        </div>
      </Question>

      <Question title="Comms">
        <div style={{ display: 'flex', gap: 8 }}>
          {(['voice', 'text', 'both'] as Comms[]).map((c) => (
            <Chip key={c} active={comms === c} onClick={() => setComms(c)}>
              {c}
            </Chip>
          ))}
        </div>
      </Question>

      <Question title="When do you play?">
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {SCHEDULE_SLOTS.map((s) => (
            <Chip key={s} active={schedule.includes(s)} onClick={() => toggle(schedule, s, setSchedule)}>
              {s}
            </Chip>
          ))}
        </div>
      </Question>

      <Question title="Toxicity tolerance" hint="1 = mute on first insult, 5 = flame is a love language.">
        <div style={{ display: 'flex', gap: 8 }}>
          {[1, 2, 3, 4, 5].map((n) => (
            <Chip key={n} active={toxicity === n} onClick={() => setToxicity(n)} style={{ minWidth: 44, justifyContent: 'center' }}>
              {n}
            </Chip>
          ))}
        </div>
      </Question>

      <Question title="One line about you">
        <TextArea label="Bio" value={bio} maxLength={300} onChange={(e) => setBio(e.target.value)} placeholder="Sage main. Will heal and roast." />
      </Question>
    </OnboardingFrame>
  )
}
