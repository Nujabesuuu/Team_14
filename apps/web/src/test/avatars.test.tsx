import { render, screen } from '@testing-library/react'

import { AVATAR_KEYS, AVATAR_META, hasPortrait, MASKS, PORTRAIT_KEYS } from '@/avatars'
import { Avatar } from '@/design-system/Avatar'

describe('avatar set', () => {
  it('has exactly eight archetypes, each with a mask and metadata', () => {
    expect(AVATAR_KEYS).toHaveLength(8)
    for (const key of AVATAR_KEYS) {
      expect(AVATAR_META[key].name).toBeTruthy()
      expect(MASKS[key]).toBeTypeOf('function')
    }
  })

  // Portraits are optional artwork: while none are shipped, only the mask fallback is testable.
  it.skipIf(PORTRAIT_KEYS.size === 0)('renders the generated portrait for archetypes that have one', () => {
    const key = [...PORTRAIT_KEYS][0]
    render(<Avatar avatar={key} accent="#E60012" size={40} />)
    expect(screen.getByRole('img', { name: `${AVATAR_META[key].name} portrait` })).toHaveAttribute('src', `/avatars/${key}.jpg`)
  })

  it('falls back to the svg mask otherwise', () => {
    const key = AVATAR_KEYS.find((k) => !hasPortrait(k))!
    const { container } = render(<Avatar avatar={key} accent="#123456" size={40} />)
    const svg = container.querySelector('svg')
    expect(svg).toHaveAttribute('aria-label', `${AVATAR_META[key].name} mask`)
    expect(container.innerHTML).toContain('#123456')
  })
})
