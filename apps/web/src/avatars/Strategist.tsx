import type { MaskProps } from './index'

export function Strategist({ accent, size = 64 }: MaskProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" role="img" aria-label="Strategist mask">
      <path d="M30 4 L30 22 M50 2 L50 20 M70 4 L70 22" stroke={accent} strokeWidth="2.5" />
      <path d="M24 26 L76 26 L74 70 L50 90 L26 70 Z" fill="#F4F1EA" />
      <path d="M24 26 L76 26 L70 34 L30 34 Z" fill="#0A0A0A" />
      <circle cx="38" cy="48" r="6" fill="#0A0A0A" />
      <circle cx="62" cy="48" r="6" fill="#0A0A0A" />
      <circle cx="38" cy="48" r="2.5" fill={accent} />
      <circle cx="62" cy="48" r="2.5" fill={accent} />
      <path d="M36 66 L64 66" stroke="#0A0A0A" strokeWidth="3" />
      <path d="M40 66 L40 76 M50 66 L50 80 M60 66 L60 76" stroke="#0A0A0A" strokeWidth="3" />
      <circle cx="30" cy="64" r="4" fill={accent} />
      <circle cx="70" cy="64" r="4" fill={accent} />
    </svg>
  )
}
