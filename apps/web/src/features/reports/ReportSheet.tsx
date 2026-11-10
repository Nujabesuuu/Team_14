import { type FormEvent, type KeyboardEvent as ReactKeyboardEvent, useEffect, useId, useRef, useState } from 'react'

import { ApiError } from '@/api/client'
import type { PublicUser, ReportContext, ReportReason } from '@/api/types'
import { Chip } from '@/design-system/Chip'
import { TextArea } from '@/design-system/Field'
import { Panel } from '@/design-system/Panel'
import { PhantomButton } from '@/design-system/PhantomButton'
import { Stamp } from '@/design-system/Stamp'
import { MAX_COMMENT, REPORT_REASONS } from '@/lib/reports'
import { useReports } from '@/stores/reports'

interface Props {
  target: PublicUser
  context: ReportContext
  /** Event, conversation or match id, depending on `context`. */
  contextId: string
  onClose: () => void
}

const WHERE: Record<ReportContext, string> = {
  event: 'About this event',
  chat: 'About this chat',
  photo: 'About their photo',
}

/**
 * "Report" bottom sheet (US-09). Lives inside a `.screen`, so it covers the phone frame only.
 * The reason is required; the person reported never learns who sent it.
 */
export function ReportSheet({ target, context, contextId, onClose }: Props) {
  const submitReport = useReports((s) => s.submit)
  const titleId = useId()
  const [reason, setReason] = useState<ReportReason | null>(null)
  const [comment, setComment] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [sent, setSent] = useState(false)

  const dialogRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  // Modal focus: move it into the sheet on open and hand it back to the opener on close.
  useEffect(() => {
    const opener = document.activeElement
    dialogRef.current?.focus()
    return () => {
      if (opener instanceof HTMLElement) opener.focus()
    }
  }, [])

  /** Keeps Tab inside the sheet, so the chat behind it cannot be reached from the keyboard. */
  const trapFocus = (e: ReactKeyboardEvent<HTMLDivElement>) => {
    if (e.key !== 'Tab' || !dialogRef.current) return
    const focusable = dialogRef.current.querySelectorAll<HTMLElement>('button:not([disabled]), textarea')
    const first = focusable[0]
    const last = focusable[focusable.length - 1]
    if (!first || !last) return
    const active = document.activeElement
    if (e.shiftKey && (active === first || active === dialogRef.current)) {
      e.preventDefault()
      last.focus()
    } else if (!e.shiftKey && active === last) {
      e.preventDefault()
      first.focus()
    }
  }

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    if (!reason || busy) return
    setBusy(true)
    setError(null)
    try {
      await submitReport({
        reported_id: target.id,
        context,
        context_id: contextId,
        reason,
        comment: comment.trim() || undefined,
      })
      setSent(true)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not send the report')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div
      ref={dialogRef}
      role="dialog"
      aria-modal="true"
      aria-labelledby={titleId}
      tabIndex={-1}
      onKeyDown={trapFocus}
      style={{
        outline: 'none',
        position: 'absolute',
        inset: 0,
        zIndex: 20,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'flex-end',
        padding: '0 12px calc(14px + var(--safe-bottom))',
        background: 'rgba(10, 10, 10, 0.78)',
      }}
    >
      <Panel tone="ink" ghost className="deal-in">
        {sent ? (
          <div style={{ display: 'grid', gap: 14, justifyItems: 'start' }}>
            <Stamp text="Sent" tone="paper" style={{ fontSize: 30 }} />
            <div id={titleId} className="display skew" style={{ fontSize: 26 }}>
              Report sent
            </div>
            <p style={{ margin: 0, fontSize: 14 }}>
              The Teamate team reads every report by hand. {target.display_name} will not know it came from you.
              Track it in Me → My reports.
            </p>
            <PhantomButton block onClick={onClose}>
              Done
            </PhantomButton>
          </div>
        ) : (
          <form onSubmit={submit} style={{ display: 'grid', gap: 14 }}>
            <div>
              <div className="cond" style={{ fontSize: 12, color: 'var(--blood)' }}>
                {WHERE[context]}
              </div>
              <div id={titleId} className="display skew" style={{ fontSize: 28, marginTop: 4 }}>
                Report {target.display_name}
              </div>
            </div>

            <div role="group" aria-label="Reason" style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {REPORT_REASONS.map((r) => (
                <Chip key={r.value} active={reason === r.value} onClick={() => setReason(r.value)}>
                  {r.label}
                </Chip>
              ))}
            </div>

            <TextArea
              label="What happened"
              hint={`Optional. ${comment.length}/${MAX_COMMENT}`}
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              maxLength={MAX_COMMENT}
              rows={3}
              style={{ minHeight: 72 }}
            />

            {error && (
              <p role="alert" style={{ color: 'var(--blood)', fontWeight: 600, margin: 0 }}>
                {error}
              </p>
            )}

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <PhantomButton type="button" variant="ghost" block onClick={onClose}>
                Cancel
              </PhantomButton>
              <PhantomButton type="submit" block disabled={!reason || busy}>
                {busy ? 'Sending' : 'Send report'}
              </PhantomButton>
            </div>
            {!reason && (
              <p className="muted" style={{ margin: 0, fontSize: 13 }}>
                Pick a reason to send.
              </p>
            )}
          </form>
        )}
      </Panel>
    </div>
  )
}
