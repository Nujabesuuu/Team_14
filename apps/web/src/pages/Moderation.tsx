import { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'

import { ApiError } from '@/api/client'
import type { ModerationReport, PublicUser, ReportDecision } from '@/api/types'
import { Avatar } from '@/design-system/Avatar'
import { Chip } from '@/design-system/Chip'
import { Empty } from '@/design-system/Empty'
import { Panel } from '@/design-system/Panel'
import { PhantomButton } from '@/design-system/PhantomButton'
import { TopBar } from '@/design-system/TopBar'
import { formatWhen } from '@/lib/format'
import { CONTEXT_LABEL, REASON_LABEL, STATUS_LABEL } from '@/lib/reports'
import { useAuth } from '@/stores/auth'
import { useReports } from '@/stores/reports'

function Person({ label, user }: { label: string; user: PublicUser }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 0 }}>
      <Avatar avatar={user.avatar_key} accent={user.accent_color} size={38} />
      <div style={{ minWidth: 0 }}>
        <div className="cond muted" style={{ fontSize: 11 }}>
          {label}
        </div>
        <div className="cond" style={{ fontSize: 16, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
          {user.display_name}
        </div>
      </div>
    </div>
  )
}

function ReportCard({
  report,
  alt,
  busy,
  onDecide,
}: {
  report: ModerationReport
  alt: boolean
  busy: boolean
  onDecide?: (decision: ReportDecision) => void
}) {
  return (
    <Panel tone="ink" alt={alt}>
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center', marginBottom: 12 }}>
        <Chip tone="blood">{REASON_LABEL[report.reason]}</Chip>
        <Chip>{CONTEXT_LABEL[report.context]}</Chip>
        <span className="muted" style={{ fontSize: 12, marginLeft: 'auto' }}>
          {formatWhen(report.created_at)}
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr', gap: 8, alignItems: 'center' }}>
        <Person label="Reported by" user={report.reporter} />
        <span aria-hidden className="display" style={{ fontSize: 22, color: 'var(--blood)' }}>
          ›
        </span>
        <Person label="About" user={report.reported} />
      </div>

      <div className="cond" style={{ fontSize: 13, marginTop: 12 }}>
        {report.context_label}
      </div>
      {report.comment ? (
        <p style={{ margin: '6px 0 0', fontSize: 14, paddingLeft: 10, borderLeft: '3px solid var(--blood)' }}>{report.comment}</p>
      ) : (
        <p className="muted" style={{ margin: '6px 0 0', fontSize: 13 }}>
          No comment.
        </p>
      )}

      {onDecide ? (
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 16 }}>
          <PhantomButton size="sm" onClick={() => onDecide('banned')} disabled={busy}>
            Ban
          </PhantomButton>
          <PhantomButton size="sm" variant="paper" onClick={() => onDecide('warned')} disabled={busy}>
            Warn
          </PhantomButton>
          <PhantomButton size="sm" variant="ghost" onClick={() => onDecide('dismissed')} disabled={busy}>
            Dismiss
          </PhantomButton>
        </div>
      ) : (
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center', marginTop: 14 }}>
          <Chip tone={report.status === 'dismissed' ? 'paper' : 'blood'}>{STATUS_LABEL[report.status]}</Chip>
          <span className="muted" style={{ fontSize: 13 }}>
            {report.moderator ? `by ${report.moderator.display_name}` : 'by a removed moderator'}
            {report.decided_at ? ` · ${formatWhen(report.decided_at)}` : ''}
          </span>
        </div>
      )}
    </Panel>
  )
}

/** Manual report queue (US-10). The link is hidden from players, and the API refuses them anyway. */
export function Moderation() {
  const role = useAuth((s) => s.me?.user.role)
  const { queue, decided, queueLoaded, loadQueue, decide } = useReports()
  const [tab, setTab] = useState<'new' | 'decided'>('new')
  const [error, setError] = useState<string | null>(null)
  const [busyId, setBusyId] = useState<string | null>(null)

  useEffect(() => {
    if (role !== 'moderator') return
    loadQueue().catch((err) => setError(err instanceof ApiError ? err.message : 'Could not load the queue'))
  }, [role, loadQueue])

  if (role !== 'moderator') return <Navigate to="/me" replace />

  const onDecide = async (report: ModerationReport, decision: ReportDecision) => {
    if (decision === 'banned' && !confirm(`Ban ${report.reported.display_name}? They are logged out and cannot sign in again.`)) return
    setBusyId(report.id)
    setError(null)
    try {
      await decide(report.id, decision)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not save the decision')
      // Most likely another moderator was faster: show what is really in the queue now.
      void loadQueue().catch(() => undefined)
    } finally {
      setBusyId(null)
    }
  }

  const list = tab === 'new' ? queue : decided
  return (
    <div className="screen">
      <TopBar title="Reports" back="/me" kicker="Moderation" />
      <div className="screen-scroll" style={{ padding: '14px 18px 24px', display: 'grid', gap: 14, alignContent: 'start' }}>
        <div style={{ display: 'flex', gap: 8 }}>
          <Chip active={tab === 'new'} onClick={() => setTab('new')}>
            New · {queue.length}
          </Chip>
          <Chip active={tab === 'decided'} onClick={() => setTab('decided')}>
            Decided · {decided.length}
          </Chip>
        </div>

        {error && (
          <p role="alert" style={{ color: 'var(--blood)', fontWeight: 600, margin: 0 }}>
            {error}
          </p>
        )}
        {queueLoaded && list.length === 0 && (
          <Empty
            title={tab === 'new' ? 'Queue is clear' : 'No decisions yet'}
            hint={tab === 'new' ? 'No new reports. Every one that comes in lands here.' : 'Reports you decide on move here.'}
          />
        )}
        {list.map((r, i) => (
          <ReportCard
            key={r.id}
            report={r}
            alt={i % 2 === 1}
            busy={busyId === r.id}
            onDecide={tab === 'new' ? (decision) => void onDecide(r, decision) : undefined}
          />
        ))}
      </div>
    </div>
  )
}
