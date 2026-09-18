import { accentPalette, tokens } from '@/design-system/tokens'

describe('design tokens', () => {
  it('exposes the Phantom UI palette', () => {
    expect(tokens.blood).toBe('#E60012')
    expect(tokens.ink).toBe('#0A0A0A')
    expect(tokens.paper).toBe('#F4F1EA')
    expect(tokens.gold).toBe('#F5C518')
  })

  it('offers 8 accent colors, one per mask', () => {
    expect(accentPalette).toHaveLength(8)
    expect(new Set(accentPalette).size).toBe(8)
  })
})
