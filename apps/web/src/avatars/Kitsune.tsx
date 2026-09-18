import type { MaskProps } from './index'

export function Kitsune({ accent, size = 64 }: MaskProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" role="img" aria-label="Kitsune mask">
      <path d="M20 42 L14 10 L40 30 L60 30 L86 10 L80 42 L70 78 L50 90 L30 78 Z" fill="#F4F1EA" />
      <path d="M22 16 L36 32 L28 40 Z" fill={accent} />
      <path d="M78 16 L64 32 L72 40 Z" fill={accent} />
      <path d="M30 50 L44 46 L40 56 Z" fill="#0A0A0A" />
      <path d="M70 50 L56 46 L60 56 Z" fill="#0A0A0A" />
      <path d="M46 62 L54 62 L50 70 Z" fill={accent} />
      <path d="M36 72 L44 76 M56 76 L64 72" stroke={accent} strokeWidth="3" strokeLinecap="round" />
    </svg>
  )
}
