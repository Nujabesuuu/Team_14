import type { MaskProps } from './index'

export function Nomad({ accent, size = 64 }: MaskProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" role="img" aria-label="Nomad mask">
      <path d="M22 30 L50 16 L78 30 L76 56 L50 66 L24 56 Z" fill="#F4F1EA" />
      <path d="M30 40 L44 38 L44 48 L32 48 Z" fill="#0A0A0A" />
      <path d="M56 38 L70 40 L68 48 L56 48 Z" fill="#0A0A0A" />
      <path d="M18 56 L82 56 L84 70 L60 92 L52 80 L40 92 L16 70 Z" fill={accent} />
      <path d="M18 56 L82 56 L80 64 L20 64 Z" fill="#0A0A0A" opacity="0.35" />
      <path d="M50 16 L50 26" stroke={accent} strokeWidth="4" strokeLinecap="round" />
    </svg>
  )
}
