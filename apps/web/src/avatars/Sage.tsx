import type { MaskProps } from './index'

export function Sage({ accent, size = 64 }: MaskProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" role="img" aria-label="Sage mask">
      <path d="M26 20 Q50 4 74 20 L78 60 L50 90 L22 60 Z" fill="#F4F1EA" />
      <path d="M50 8 Q30 14 26 20 L22 60 L50 90 Z" fill="#0A0A0A" opacity="0.85" />
      <path d="M62 30 A14 14 0 1 0 62 58 A11 11 0 1 1 62 30 Z" fill={accent} />
      <path d="M30 48 L42 44 L40 54 Z" fill="#F4F1EA" />
      <path d="M56 70 L70 66 L66 76 Z" fill="#0A0A0A" />
      <circle cx="34" cy="70" r="3" fill={accent} />
    </svg>
  )
}
