import { render } from '@testing-library/react'

import { AVATAR_KEYS, AVATAR_META, AVATARS } from '@/avatars'

describe('avatar set', () => {
  it('has exactly eight original masks with metadata', () => {
    expect(AVATAR_KEYS).toHaveLength(8)
    for (const key of AVATAR_KEYS) expect(AVATAR_META[key].name).toBeTruthy()
  })

  it.each(AVATAR_KEYS)('%s renders an accessible svg using the accent', (key) => {
    const Mask = AVATARS[key]
    const { container } = render(<Mask accent="#123456" size={40} />)
    const svg = container.querySelector('svg')
    expect(svg).toHaveAttribute('role', 'img')
    expect(svg?.getAttribute('width')).toBe('40')
    expect(container.innerHTML).toContain('#123456')
  })
})
