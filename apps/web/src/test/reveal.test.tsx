import { render, screen } from '@testing-library/react'

import { RevealPhoto } from '@/features/matches/RevealPhoto'
import { blurPx } from '@/lib/reveal'

describe('reveal', () => {
  it('maps stages to the same blur radii as the API', () => {
    expect([0, 1, 2, 3].map(blurPx)).toEqual([24, 12, 4, 0])
    expect(blurPx(42)).toBe(24)
  })

  it.each([
    [0, 'blur(24px) grayscale(1)'],
    [1, 'blur(12px) grayscale(0)'],
    [3, 'blur(0px) grayscale(0)'],
  ])('stage %i renders the photo with filter %s', (stage, filter) => {
    render(<RevealPhoto photoUrl="/media/x.jpg" stage={stage} avatar="operator" accent="#E60012" />)
    const img = screen.getByTestId('reveal-photo').querySelector('img')!
    expect(img.style.filter).toBe(filter)
  })

  it('falls back to the hero portrait when there is no photo', () => {
    render(<RevealPhoto photoUrl={null} stage={3} avatar="builder" accent="#F5C518" />)
    expect(screen.getByRole('img', { name: 'Builder portrait' })).toHaveAttribute('src', '/avatars/builder.jpg')
  })
})
