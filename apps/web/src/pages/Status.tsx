import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { api, ApiError } from '@/api/client'
import { Chip } from '@/design-system/Chip'
import { Panel } from '@/design-system/Panel'
import { PhantomButton } from '@/design-system/PhantomButton'
import { TopBar } from '@/design-system/TopBar'

type Check = { state: 'pending' } | { state: 'ok'; info: string } | { state: 'down'; info: string }

/** Every screen of the MVP and the user stories it serves (docs/requirements.md). */
const SCREENS:{ path: string; name: string; stories: string }[] = [
  { path: '/welcome', name: 'Welcome', stories: 'US-01' },
  { path: '/register', name: 'Register (18+)', stories: 'US-01' },
  { path: '/onboarding/dna', name: 'Game DNA', stories: 'US-02' },
  { path: '/onboarding/avatar', name: 'Hero mask', stories: 'US-18' },
  { path: '/onboarding/modes', name: 'Modes & photo', stories: 'US-03, US-04' },
  { path: '/events', name: 'Tonight’s events', stories: 'US-05' },
  { path: '/events/new', name: 'Host an event', stories: 'US-19' },
  { path: '/events/:id', name: 'Event lobby', stories: 'US-06, US-07, US-08' },
  { path: '/events/:id/feedback', name: 'Play again?', stories: 'US-11' },
  { path: '/match/:id', name: 'It’s a match', stories: 'US-12' },
  { path: '/discover', name: 'Discover (swipes)', stories: 'US-13' },
  { path: '/matches', name: 'Matches', stories: 'US-12, US-16' },
  { path: '/chat/:id', name: 'Chat + photo reveal', stories: 'US-14, US-15, US-16, US-17' },
  { path: '/me', name: 'Profile', stories: 'US-02, US-03, US-08' },
]

async function probe(path: string, describe: (body: Record<string, string>) => string): Promise<Check> {
  try {
    return { state: 'ok', info: describe(await api.get<Record<string, string>>(path)) }
  } catch (err) {
    return { state: 'down', info: err instanceof ApiError ? `${err.status} ${err.code}` : 'API is not reachable' }
  }
}

function CheckRow({ label, check }: { label: string; check: Check }) {
  const tone = check.state === 'ok' ? 'gold' : check.state === 'down' ? 'blood' : 'outline'
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
      <span className="cond" style={{ fontSize: 14 }}>
        {label}
      </span>
      <span style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13 }}>
        {check.state !== 'pending' && <span style={{ opacity: 0.8 }}>{check.info}</span>}
        <Chip tone={tone}>{check.state === 'pending' ? '…' : check.state === 'ok' ? 'OK' : 'DOWN'}</Chip>
      </span>
    </div>
  )
}

/**
 * Walking-skeleton page: proves UI → API → DB are wired, without logging in.
 * Public on purpose, so the demo can open it from a clean browser.
 */
export function Status() {
  const navigate = useNavigate()
  const [apiCheck, setApi] = useState<Check>({ state: 'pending' })
  const [db, setDb] = useState<Check>({ state: 'pending' })

  const probeAll = useCallback(() => {
    void probe('/health', (b) => `GET /api/v1/health → ${b.status}`).then(setApi)
    void probe('/health/db', (b) => `${b.database} → ${b.status}`).then(setDb)
  }, [])

  useEffect(probeAll, [probeAll])

  const recheck = () => {
    setApi({ state: 'pending' })
    setDb({ state: 'pending' })
    probeAll()
  }

  return (
    <div className="screen">
      <TopBar title="Teamate" kicker="Walking skeleton" />
      <div className="screen-scroll" style={{ padding: '14px 18px 24px', display: 'grid', gap: 14, alignContent: 'start' }}>
        <Panel tone="ink" ghost>
          <div className="display skew" style={{ fontSize: 26, color: 'var(--gold)', marginBottom: 12 }}>
            System check
          </div>
          <div style={{ display: 'grid', gap: 10 }}>
            <CheckRow label="Web (React)" check={{ state: 'ok', info: 'rendered' }} />
            <CheckRow label="API (FastAPI)" check={apiCheck} />
            <CheckRow label="Database" check={db} />
          </div>
          <div style={{ marginTop: 14 }}>
            <PhantomButton variant="ghost" block onClick={recheck}>
              Check again
            </PhantomButton>
          </div>
        </Panel>

        <Panel tone="paper">
          <div className="display skew" style={{ fontSize: 24, marginBottom: 10 }}>
            Screens
          </div>
          <ol style={{ margin: 0, paddingLeft: 20, display: 'grid', gap: 6, fontSize: 14 }}>
            {SCREENS.map((s) => (
              <li key={s.path}>
                <b>{s.name}</b> <code style={{ opacity: 0.7 }}>{s.path}</code>{' '}
                <span style={{ opacity: 0.6 }}>· {s.stories}</span>
              </li>
            ))}
          </ol>
        </Panel>

        <PhantomButton block onClick={() => navigate('/welcome')}>
          Open the app
        </PhantomButton>
      </div>
    </div>
  )
}
