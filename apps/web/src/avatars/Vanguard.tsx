import type { MaskProps } from './index'

export function Vanguard({ accent, size = 64 }: MaskProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" role="img" aria-label="Vanguard mask">
      <path d="M20 22 L50 10 L80 22 L80 66 L50 92 L20 66 Z" fill="#F4F1EA" />
      <path d="M26 40 L74 40 L74 52 L26 52 Z" fill="#0A0A0A" />
      <path d="M30 43 L70 43 L70 49 L30 49 Z" fill={accent} />
      <path d="M50 10 L50 30 M44 30 L56 30" stroke="#0A0A0A" strokeWidth="3" />
      <path d="M36 64 L64 64 L60 72 L40 72 Z" fill="#0A0A0A" />
      <path d="M20 66 L32 72 L20 78 Z" fill={accent} />
      <path d="M80 66 L68 72 L80 78 Z" fill={accent} />
    </svg>
  )
}
