import type { ReactNode } from 'react'

import { TopBar } from '@/design-system/TopBar'

/** Shared chrome for the three onboarding steps: title, diagonal progress, scrollable body, sticky footer. */
export function OnboardingFrame({
  step,
  title,
  children,
  footer,
  back,
}: {
  step: 1 | 2 | 3
  title: string
  children: ReactNode
  footer: ReactNode
  back?: string
}) {
  return (
    <div className="screen">
      <TopBar title={title} kicker={`Step ${step} / 3`} back={back} />
      <div style={{ display: 'flex', gap: 4, padding: '0 18px' }}>
        {[1, 2, 3].map((s) => (
          <div
            key={s}
            style={{
              flex: 1,
              height: 8,
              background: s <= step ? 'var(--blood)' : 'var(--ash-2)',
              clipPath: 'var(--cut-button)',
            }}
          />
        ))}
      </div>
      <div className="screen-scroll" style={{ padding: '18px 22px 24px' }}>
        {children}
      </div>
      <div style={{ padding: '12px 22px calc(18px + var(--safe-bottom))', borderTop: '2px solid var(--ash)' }}>
        {footer}
      </div>
    </div>
  )
}

export function Question({ title, hint, children }: { title: string; hint?: string; children: ReactNode }) {
  return (
    <section style={{ marginBottom: 26 }}>
      <h2 className="display skew" style={{ fontSize: 26, margin: '0 0 4px', color: 'var(--paper)' }}>
        {title}
      </h2>
      {hint && (
        <p className="muted" style={{ margin: '0 0 12px', fontSize: 14 }}>
          {hint}
        </p>
      )}
      {children}
    </section>
  )
}
