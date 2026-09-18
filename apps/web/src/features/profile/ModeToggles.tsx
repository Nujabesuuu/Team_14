import type { Mode } from '@/api/types'

const MODES: { value: Mode; title: string; body: string }[] = [
  { value: 'duo', title: 'Duo', body: 'I need someone to queue with. Nothing more, nothing less.' },
  { value: 'friends', title: 'Friends', body: 'Looking for people to hang out with beyond one match.' },
  { value: 'dating', title: 'Dating', body: 'Open to something romantic if the game clicks. 18+ only.' },
]

export function ModeToggles({ value, onChange, age }: { value: Mode[]; onChange: (m: Mode[]) => void; age: number }) {
  const toggle = (m: Mode) => onChange(value.includes(m) ? value.filter((v) => v !== m) : [...value, m])
  return (
    <div style={{ display: 'grid', gap: 10 }}>
      {MODES.map((m) => {
        const locked = m.value === 'dating' && age < 18
        const active = value.includes(m.value)
        return (
          <button
            key={m.value}
            type="button"
            disabled={locked}
            aria-pressed={active}
            onClick={() => toggle(m.value)}
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr auto',
              gap: 12,
              alignItems: 'center',
              padding: '14px 16px',
              textAlign: 'left',
              background: active ? 'var(--blood)' : 'var(--ink-2)',
              color: active ? 'var(--chalk)' : 'var(--paper)',
              border: `2px solid ${active ? 'var(--blood)' : 'var(--ash-2)'}`,
              clipPath: 'var(--cut-card)',
              cursor: locked ? 'not-allowed' : 'pointer',
              opacity: locked ? 0.45 : 1,
            }}
          >
            <span>
              <span className="display" style={{ fontSize: 24, display: 'block' }}>
                {m.title}
              </span>
              <span style={{ fontSize: 13, opacity: 0.85 }}>{locked ? 'Available from 18 years old.' : m.body}</span>
            </span>
            <span className="cond" style={{ fontSize: 13, opacity: 0.9 }}>
              {active ? 'ON' : 'OFF'}
            </span>
          </button>
        )
      })}
    </div>
  )
}
