import type { MaskProps } from './index'

export function Operator({ accent, size = 64 }: MaskProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" role="img" aria-label="Operator mask">
      <path d="M18 34 L50 18 L82 34 L78 66 L50 82 L22 66 Z" fill="#F4F1EA" />
      <path d="M50 44 L74 52 L50 60 L44 52 Z" fill="#0A0A0A" />
      <path d="M50 44 L74 52 L50 60 Z" fill={accent} />
      <path d="M28 44 L44 40 L42 50 L30 52 Z" fill="#0A0A0A" />
      <path d="M56 40 L72 42 L70 48 L58 48 Z" fill="#0A0A0A" />
      <path d="M22 66 L50 82 L50 70 Z" fill={accent} opacity="0.9" />
    </svg>
  )
}
