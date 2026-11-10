import { useEffect, useState } from 'react'

import { ApiError } from '@/api/client'
import type { ReportStatus } from '@/api/types'
import { Avatar } from '@/design-system/Avatar'
import { Chip } from '@/design-system/Chip'
import { Empty } from '@/design-system/Empty'
import { TopBar } from '@/design-system/TopBar'
import { formatWhen } from '@/lib/format'
import { CONTEXT_LABEL, REASON_LABEL, STATUS_LABEL } from '@/lib/reports'
import { useReports } from '@/stores/reports'

const STATUS_TONE: Record<ReportStatus, 'outline' | 'paper' | 'blood'> = {
  new: 'outline',
  dismissed: 'paper',
  warned: 'blood',
  banned: 'blood',
}

/** Reports I sent and what the team decided (US-10: the reporter sees that it was reviewed). */
export function MyReports() {
  const { mine, mineLoaded, loadMine } = useReports()
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadMine().catch((err) => setError(err instanceof ApiError ? err.message : 'Could not load your reports'))
  }, [loadMine])

  return (
    <div className="screen">
      <TopBar title="My reports" back="/me" kicker="Safety" />
      <div className="screen-scroll" style={{ padding: '14px 18px 24px', display: 'grid', gap: 10, alignContent: 'start' }}>
        {error && (
          <p role="alert" style={{ color: 'var(--blood)', fontWeight: 600, margin: 0 }}>
            {error}
          </p>
        )}
        {mineLoaded && mine.length === 0 && (
          <Empty title="Nothing reported" hint="If someone crosses the line, use Report in the chat or in the event lobby." />
        )}
        {mine.map((r) => (
          <div
            key={r.id}
            style={{
              display: 'grid',
              gridTemplateColumns: 'auto 1fr auto',
              gap: 12,
              alignItems: 'center',
              padding: '12px 14px',
              background: 'var(--ink-2)',
              clipPath: 'var(--cut-button)',
            }}
          >
            <Avatar avatar={r.reported.avatar_key} accent={r.reported.accent_color} size={44} />
            <div style={{ minWidth: 0 }}>
              <div className="cond" style={{ fontSize: 17 }}>
                {r.reported.display_name}
              </div>
              <div className="muted" style={{ fontSize: 13 }}>
                {CONTEXT_LABEL[r.context]} · {REASON_LABEL[r.reason]} · {formatWhen(r.created_at)}
              </div>
            </div>
            <Chip tone={STATUS_TONE[r.status]}>{STATUS_LABEL[r.status]}</Chip>
          </div>
        ))}
      </div>
    </div>
  )
}
