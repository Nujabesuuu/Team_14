import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

import { Status } from '@/pages/Status'

const jsonResponse = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })

describe('walking-skeleton status page', () => {
  beforeEach(() => vi.restoreAllMocks())

  it('shows API and database as OK when both health checks answer', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) =>
      String(input).endsWith('/health/db')
        ? jsonResponse(200, { status: 'ok', database: 'sqlite' })
        : jsonResponse(200, { status: 'ok' }),
    )
    render(
      <MemoryRouter>
        <Status />
      </MemoryRouter>,
    )
    expect(await screen.findByText('sqlite → ok')).toBeInTheDocument()
    expect(await screen.findByText('GET /api/v1/health → ok')).toBeInTheDocument()
    expect(screen.getByText('Tonight’s events')).toBeInTheDocument()
  })

  it('shows the error code when the database is down', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) =>
      String(input).endsWith('/health/db')
        ? jsonResponse(503, { code: 'DB_UNAVAILABLE', detail: 'Database is not reachable' })
        : jsonResponse(200, { status: 'ok' }),
    )
    render(
      <MemoryRouter>
        <Status />
      </MemoryRouter>,
    )
    expect(await screen.findByText('503 DB_UNAVAILABLE')).toBeInTheDocument()
    expect(screen.getByText('DOWN')).toBeInTheDocument()
  })
})
