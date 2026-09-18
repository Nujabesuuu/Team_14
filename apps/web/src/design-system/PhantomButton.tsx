import type { ButtonHTMLAttributes, ReactNode } from 'react'

type Variant = 'primary' | 'paper' | 'ghost' | 'gold' | 'danger'
type Size = 'sm' | 'md' | 'lg'

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
  block?: boolean
  children: ReactNode
}

const fill: Record<Variant, { bg: string; fg: string; shadow: string }> = {
  primary: { bg: 'var(--blood)', fg: 'var(--chalk)', shadow: 'var(--paper)' },
  paper: { bg: 'var(--paper)', fg: 'var(--ink)', shadow: 'var(--blood)' },
  ghost: { bg: 'transparent', fg: 'var(--paper)', shadow: 'transparent' },
  gold: { bg: 'var(--gold)', fg: 'var(--ink)', shadow: 'var(--paper)' },
  danger: { bg: 'var(--ink)', fg: 'var(--blood)', shadow: 'var(--blood)' },
}

const pad: Record<Size, string> = { sm: '8px 14px', md: '13px 22px', lg: '18px 28px' }
const font: Record<Size, string> = { sm: '15px', md: '18px', lg: '22px' }

/**
 * The signature CTA: a skewed polygon with an offset "misprint" shadow.
 * Ghost variant is a bare outlined label for secondary actions.
 */
export function PhantomButton({ variant = 'primary', size = 'md', block, children, style, disabled, ...rest }: Props) {
  const f = fill[variant]
  return (
    <button
      {...rest}
      disabled={disabled}
      style={{
        position: 'relative',
        display: block ? 'block' : 'inline-block',
        width: block ? '100%' : undefined,
        padding: 0,
        border: 0,
        background: 'transparent',
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.45 : 1,
        transition: `transform var(--dur-fast) var(--ease-snap), opacity var(--dur-fast)`,
        ...style,
      }}
      className="phantom-btn"
      onMouseDown={(e) => {
        e.currentTarget.style.transform = 'translate(2px, 2px)'
        rest.onMouseDown?.(e)
      }}
      onMouseUp={(e) => {
        e.currentTarget.style.transform = ''
        rest.onMouseUp?.(e)
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = ''
        rest.onMouseLeave?.(e)
      }}
    >
      {/* Content-sized wrapper so the shadow never inherits a stretched button height. */}
      <span style={{ position: 'relative', display: 'block' }}>
      {variant !== 'ghost' && (
        <span
          aria-hidden
          style={{
            position: 'absolute',
            inset: 0,
            transform: 'translate(4px, 4px)',
            background: f.shadow,
            clipPath: 'var(--cut-button)',
          }}
        />
      )}
      <span
        style={{
          position: 'relative',
          display: 'block',
          padding: pad[size],
          background: f.bg,
          color: f.fg,
          clipPath: variant === 'ghost' ? undefined : 'var(--cut-button)',
          border: variant === 'ghost' ? '2px solid var(--paper)' : undefined,
          fontFamily: 'var(--font-cond)',
          fontWeight: 800,
          fontSize: font[size],
          letterSpacing: '0.08em',
          textTransform: 'uppercase',
          lineHeight: 1,
          textAlign: 'center',
          whiteSpace: 'nowrap',
        }}
      >
        {children}
      </span>
      </span>
    </button>
  )
}
