/** Mirrors apps/api/app/domain/reveal.py — keep the two in sync. */
export const REVEAL_BLUR: Record<number, number> = { 0: 24, 1: 12, 2: 4, 3: 0 }

export function blurPx(stage: number): number {
  return REVEAL_BLUR[stage] ?? REVEAL_BLUR[0]
}

export const REVEAL_LABEL: Record<number, string> = {
  0: 'Stranger',
  1: 'Matched',
  2: 'Played together',
  3: 'Revealed',
}
