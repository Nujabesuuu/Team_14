import type { ReactNode } from 'react'

/** Empty state with a big skewed headline and a one-line hint. */
export function Empty({ title, hint, action }: { title: string; hint?: string; action?: ReactNode }) {
  return (
    <div style={{ padding: '48px 24px', textAlign: 'center' }}>
      <div className="display skew" style={{ fontSize: 44, color: 'var(--ash-2)', lineHeight: 0.9 }}>
        {title}
      </div>
      {hint && (
        <p className="muted" style={{ marginTop: 12, fontSize: 15 }}>
          {hint}
        </p>
      )}
      {action && <div style={{ marginTop: 20 }}>{action}</div>}
    </div>
  )
}
