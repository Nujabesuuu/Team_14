import type { MaskProps } from './index'

export function Impostor({ accent, size = 64 }: MaskProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" role="img" aria-label="Impostor mask">
      <path d="M22 40 L14 16 L38 32 L50 14 L62 32 L86 16 L78 40 Z" fill={accent} />
      <circle cx="14" cy="16" r="5" fill="#F4F1EA" />
      <circle cx="86" cy="16" r="5" fill="#F4F1EA" />
      <circle cx="50" cy="14" r="5" fill="#F4F1EA" />
      <path d="M22 40 L78 40 L74 74 L50 88 L26 74 Z" fill="#F4F1EA" />
      <path d="M30 50 L44 48 L42 56 L32 57 Z" fill="#0A0A0A" />
      <path d="M56 48 L70 50 L68 57 L58 56 Z" fill="#0A0A0A" />
      <path d="M34 66 Q50 80 66 66 Q50 70 34 66 Z" fill="#0A0A0A" />
    </svg>
  )
}
