import { createElement, type ButtonHTMLAttributes, type CSSProperties, type ReactNode } from 'react'

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  active?: boolean
  tone?: 'paper' | 'blood' | 'gold' | 'outline'
  children: ReactNode
}

const PALETTE = {
  paper: { bg: 'var(--paper)', fg: 'var(--ink)', border: 'var(--paper)' },
  blood: { bg: 'var(--blood)', fg: 'var(--chalk)', border: 'var(--blood)' },
  gold: { bg: 'var(--gold)', fg: 'var(--ink)', border: 'var(--gold)' },
  outline: { bg: 'transparent', fg: 'var(--paper)', border: 'var(--ash-2)' },
}

/**
 * Skewed tag/toggle. Renders a <button> when it has an onClick (selectable option),
 * otherwise a <span> so it can sit inside other buttons without invalid nesting.
 */
export function Chip({ active, tone = 'outline', children, style, onClick, ...rest }: Props) {
  const palette = PALETTE[active ? 'blood' : tone]
  const base: CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 6,
    padding: '6px 12px',
    background: palette.bg,
    color: palette.fg,
    border: `2px solid ${palette.border}`,
    clipPath: 'var(--cut-chip)',
    fontFamily: 'var(--font-cond)',
    fontWeight: 700,
    fontSize: 13,
    letterSpacing: '0.08em',
    textTransform: 'uppercase',
    lineHeight: 1,
    cursor: onClick ? 'pointer' : 'default',
    transition: 'background var(--dur-fast), color var(--dur-fast)',
    ...style,
  }
  if (onClick) {
    return createElement('button', { type: 'button', onClick, style: base, 'aria-pressed': active, ...rest }, children)
  }
  const { disabled: _disabled, ...spanRest } = rest
  return createElement('span', { style: base, ...(spanRest as object) }, children)
}
