/** Typed mirror of tokens.css for places that need raw values (SVG, canvas, Motion). */
export const tokens = {
  ink: '#0A0A0A',
  paper: '#F4F1EA',
  blood: '#E60012',
  bloodDeep: '#9B000C',
  ash: '#2A2A2A',
  chalk: '#FFFFFF',
  gold: '#F5C518',
} as const

export const accentPalette = [
  '#E60012',
  '#1E90FF',
  '#9B59B6',
  '#2ECC71',
  '#F5C518',
  '#FF6B35',
  '#E91E63',
  '#00BCD4',
] as const

export type Accent = (typeof accentPalette)[number] | string
