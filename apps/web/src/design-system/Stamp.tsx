import type { CSSProperties } from 'react'

interface Props {
  text: string
  tone?: 'blood' | 'paper' | 'gold'
  style?: CSSProperties
}

/** Rotated rubber-stamp label ("LIKE", "NOPE", "MATCH"). */
export function Stamp({ text, tone = 'blood', style }: Props) {
  const color = { blood: 'var(--blood)', paper: 'var(--paper)', gold: 'var(--gold)' }[tone]
  return (
    <div
      className="display stamp-in"
      style={{
        display: 'inline-block',
        padding: '6px 16px',
        border: `5px solid ${color}`,
        color,
        fontSize: 40,
        letterSpacing: '0.04em',
        transform: 'rotate(-12deg)',
        background: 'rgba(10,10,10,0.55)',
        textShadow: '0 0 0 transparent',
        ...style,
      }}
    >
      {text}
    </div>
  )
}
