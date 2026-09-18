import { render, screen } from '@testing-library/react'

import { AVATAR_KEYS, AVATAR_META, avatarSrc } from '@/avatars'
import { Avatar } from '@/design-system/Avatar'

describe('avatar set', () => {
  it('has exactly eight archetypes with metadata', () => {
    expect(AVATAR_KEYS).toHaveLength(8)
    for (const key of AVATAR_KEYS) {
      expect(AVATAR_META[key].name).toBeTruthy()
      expect(avatarSrc(key)).toBe(`/avatars/${key}.jpg`)
    }
  })

  it('renders the portrait with an accessible name and the accent ring', () => {
    render(<Avatar avatar="sage" accent="#3AA46B" size={40} />)
    const img = screen.getByRole('img', { name: 'Sage portrait' })
    expect(img).toHaveAttribute('src', '/avatars/sage.jpg')
    expect(screen.getByTestId('avatar').style.boxShadow).toContain('#3AA46B')
  })
})
