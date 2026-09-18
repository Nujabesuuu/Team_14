import type { MaskProps } from './index'

export function Builder({ accent, size = 64 }: MaskProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" role="img" aria-label="Builder mask">
      <path d="M28 18 L72 18 L80 50 L72 82 L28 82 L20 50 Z" fill="#F4F1EA" />
      <circle cx="50" cy="34" r="9" fill="#0A0A0A" />
      <circle cx="50" cy="34" r="4" fill={accent} />
      <path d="M50 22 L50 10 M40 26 L34 18 M60 26 L66 18" stroke={accent} strokeWidth="2.5" strokeLinecap="round" />
      <path d="M30 54 L44 50 L42 60 Z" fill="#0A0A0A" />
      <path d="M70 54 L56 50 L58 60 Z" fill="#0A0A0A" />
      <path d="M38 72 L62 72" stroke="#0A0A0A" strokeWidth="3" />
      <path d="M20 50 L28 50 M72 50 L80 50" stroke={accent} strokeWidth="3" />
    </svg>
  )
}
