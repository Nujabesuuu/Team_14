import type { CSSProperties, HTMLAttributes, ReactNode } from 'react'

interface Props extends HTMLAttributes<HTMLDivElement> {
  tone?: 'paper' | 'ink' | 'blood'
  alt?: boolean
  /** Extra offset border in the accent color, like a misregistered print. */
  ghost?: boolean
  children: ReactNode
}

const tones: Record<NonNullable<Props['tone']>, CSSProperties> = {
  paper: { background: 'var(--paper)', color: 'var(--ink)' },
  ink: { background: 'var(--ink-2)', color: 'var(--paper)', boxShadow: 'inset 0 0 0 2px var(--ash-2)' },
  blood: { background: 'var(--blood)', color: 'var(--chalk)' },
}

/** A cut-corner card. Content sits inside a polygon; the outer wrapper carries the ghost border. */
export function Panel({ tone = 'paper', alt, ghost, children, style, ...rest }: Props) {
  const cut = alt ? 'var(--cut-card-alt)' : 'var(--cut-card)'
  return (
    <div {...rest} style={{ position: 'relative', ...style }}>
      {ghost && (
        <div
          aria-hidden
          style={{
            position: 'absolute',
            inset: 0,
            transform: 'translate(5px, 5px)',
            background: tone === 'blood' ? 'var(--paper)' : 'var(--blood)',
            clipPath: cut,
          }}
        />
      )}
      <div style={{ position: 'relative', clipPath: cut, padding: '18px 20px', ...tones[tone] }}>{children}</div>
    </div>
  )
}
