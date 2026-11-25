import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

import type { Event, PendingFeedback, PublicUser } from '@/api/types'
import { afterGame, formatLeft } from '@/lib/afterGame'
import { EventDetail } from '@/pages/EventDetail'
import { Feedback } from '@/pages/Feedback'
import { useEvents } from '@/stores/events'

const jsonResponse = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })

const person = (id: string, display_name: string): PublicUser => ({
  id,
  display_name,
  age: 24,
  avatar_key: 'duelist',
  accent_color: '#E60012',
  photo_url: null,
  is_premium: false,
})
const olena = person('u-olena', 'Olena')
const maks = person('u-maks', 'Maks')

const START = Date.parse('2026-11-20T21:00:00Z')
const MIN = 60_000
const HOUR = 60 * MIN

/** A finished event Olena took part in; times are offsets from START. */
const finished = (over: Partial<Event> = {}, playedMs = 45 * MIN): Event => ({
  id: 'e1',
  host: olena,
  game: { id: 'g1', name: 'Overcooked 2', slug: 'overcooked-2', is_chill: true } as Event['game'],
  kind: 'squad',
  title: 'Overcooked 2 for two',
  starts_at: new Date(START).toISOString(),
  max_slots: 2,
  status: 'finished',
  participants: [olena, maks],
  is_host: true,
  is_participant: true,
  created_at: new Date(START - HOUR).toISOString(),
  started_at: new Date(START).toISOString(),
  finished_at: new Date(START + playedMs).toISOString(),
  counted_at: null,
  confirmations: 0,
  confirmed_by_me: false,
  feedback_closes_at: null,
  ...over,
})

const counted = (countedAt: number) =>
  finished({
    counted_at: new Date(countedAt).toISOString(),
    feedback_closes_at: new Date(countedAt + 24 * HOUR).toISOString(),
    confirmations: 2,
    confirmed_by_me: true,
  })

describe('US-07: what a participant sees after the game', () => {
  it.each([
    ['14 min 59 s', 14 * MIN + 59_000, 'too_short'],
    ['15 min', 15 * MIN, 'confirm'],
    ['45 min', 45 * MIN, 'confirm'],
  ])('a game of %s → %s', (_, played, kind) => {
    expect(afterGame(finished({}, played), START + HOUR).kind).toBe(kind)
  })

  it('after my confirmation it waits for the second one instead of offering "play again?"', () => {
    expect(afterGame(finished({ confirmed_by_me: true, confirmations: 1 }), START + HOUR)).toEqual({
      kind: 'waiting',
      confirmations: 1,
    })
  })

  it('an event finished before US-07 (no start time) is never counted', () => {
    expect(afterGame(finished({ started_at: null }), START + HOUR).kind).toBe('too_short')
  })

  it('people outside the event and unfinished events get nothing', () => {
    expect(afterGame(finished({ is_participant: false }), START + HOUR).kind).toBe('none')
    expect(afterGame(finished({ status: 'in_progress', finished_at: null }), START + HOUR).kind).toBe('none')
  })
})

describe('US-11: 24 hours to answer "play again?"', () => {
  const countedAt = START + HOUR

  it.each([
    ['23 h 59 min after counting', 23 * HOUR + 59 * MIN, 'play_again'],
    ['exactly 24 h 0 min', 24 * HOUR, 'expired'],
    ['24 h 1 min', 24 * HOUR + MIN, 'expired'],
  ])('%s → %s', (_, after, kind) => {
    expect(afterGame(counted(countedAt), countedAt + after).kind).toBe(kind)
  })

  it('shows the time left in hours and minutes', () => {
    expect(formatLeft(23 * HOUR + 59 * MIN + 30_000)).toBe('23h 59m')
    expect(formatLeft(12 * MIN)).toBe('12m')
    expect(formatLeft(-5)).toBe('0m')
  })
})

/** Answers by method and path, so the order of parallel requests does not matter. */
const routes = (table: Record<string, () => Response>) =>
  vi.fn((url: string, init?: RequestInit) => {
    const key = `${init?.method ?? 'GET'} ${new URL(url, 'http://x').pathname.replace('/api/v1', '')}`
    const reply = table[key]
    if (!reply) throw new Error(`unexpected request ${key}`)
    return Promise.resolve(reply())
  })

describe('US-11: the "play again?" screen', () => {
  beforeEach(() => vi.restoreAllMocks())

  const renderFeedback = () =>
    render(
      <MemoryRouter initialEntries={['/events/e1/feedback']}>
        <Routes>
          <Route path="/events/:id/feedback" element={<Feedback />} />
        </Routes>
      </MemoryRouter>,
    )

  const pending = (allowed: boolean): PendingFeedback => ({
    pending: [maks],
    done: [],
    closer_allowed: { [maks.id]: allowed },
  })
  const openWindow = () => counted(Date.now() - HOUR)

  it.each([
    [true, false],
    [false, true],
  ])('closer allowed by the server = %s → "Get closer" disabled = %s', async (allowed, disabled) => {
    vi.stubGlobal(
      'fetch',
      routes({
        'GET /events/e1/feedback': () => jsonResponse(200, pending(allowed)),
        'GET /events/e1': () => jsonResponse(200, openWindow()),
      }),
    )
    renderFeedback()
    const closer = await screen.findByRole('button', { name: 'Get closer' })
    expect(closer.hasAttribute('disabled')).toBe(disabled)
    expect(screen.queryByText('Available only when you both have Dating on.') !== null).toBe(disabled)
    expect(screen.getByRole('button', { name: 'Play again' })).toBeEnabled()
  })

  it('sends the answer for the teammate on screen and moves on', async () => {
    const fetchMock = routes({
      'GET /events/e1/feedback': () => jsonResponse(200, pending(true)),
      'GET /events/e1': () => jsonResponse(200, openWindow()),
      'POST /events/e1/feedback': () => jsonResponse(200, { match_created: false, match_id: null }),
    })
    vi.stubGlobal('fetch', fetchMock)
    renderFeedback()
    fireEvent.click(await screen.findByRole('button', { name: 'Get closer' }))
    await screen.findByText('All rated')
    const post = fetchMock.mock.calls.find(([, init]) => init?.method === 'POST')!
    expect(JSON.parse(post[1]!.body as string)).toEqual({ to_user_id: maks.id, answer: 'closer' })
  })

  it('a late answer shows "Time\'s up" from the error code, not from the text', async () => {
    vi.stubGlobal(
      'fetch',
      routes({
        'GET /events/e1/feedback': () => jsonResponse(200, pending(true)),
        'GET /events/e1': () => jsonResponse(200, openWindow()),
        'POST /events/e1/feedback': () => jsonResponse(409, { code: 'FEEDBACK_WINDOW_CLOSED', detail: 'any text' }),
      }),
    )
    renderFeedback()
    fireEvent.click(await screen.findByRole('button', { name: 'Play again' }))
    await screen.findByText("Time's up")
    expect(screen.queryByRole('button', { name: 'Get closer' })).not.toBeInTheDocument()
  })

  it('US-12 «Максим не відповів за 24 години»: opened late, it says "Time\'s up" with no answer buttons', async () => {
    vi.stubGlobal(
      'fetch',
      routes({
        'GET /events/e1/feedback': () => jsonResponse(200, pending(true)),
        'GET /events/e1': () => jsonResponse(200, counted(Date.now() - 24 * HOUR - MIN)),
      }),
    )
    renderFeedback()
    await screen.findByText("Time's up")
    expect(screen.queryByRole('button', { name: 'Get closer' })).not.toBeInTheDocument()
  })

  it('a game that was not counted has no questions at all', async () => {
    vi.stubGlobal(
      'fetch',
      routes({
        'GET /events/e1/feedback': () => jsonResponse(409, { code: 'GAME_NOT_COUNTED', detail: 'whatever' }),
        'GET /events/e1': () => jsonResponse(200, finished()),
      }),
    )
    renderFeedback()
    await waitFor(() => expect(screen.getByText('Not counted')).toBeInTheDocument())
    expect(screen.queryByRole('button', { name: 'Play again' })).not.toBeInTheDocument()
  })
})

describe('US-07: the lobby after the game', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    useEvents.setState({ byId: {}, feed: [], mine: [] })
  })

  it('"We played — confirm" sends the confirmation and shows what the server answered', async () => {
    const fetchMock = routes({
      'GET /events/e1': () => jsonResponse(200, finished()),
      'POST /events/e1/confirm': () => jsonResponse(200, finished({ confirmations: 1, confirmed_by_me: true })),
    })
    vi.stubGlobal('fetch', fetchMock)
    render(
      <MemoryRouter initialEntries={['/events/e1']}>
        <Routes>
          <Route path="/events/:id" element={<EventDetail />} />
        </Routes>
      </MemoryRouter>,
    )
    fireEvent.click(await screen.findByRole('button', { name: 'We played — confirm' }))
    await screen.findByText('Confirmed 1/2')
    expect(fetchMock.mock.calls.some(([, init]) => init?.method === 'POST')).toBe(true)
    expect(screen.queryByRole('button', { name: 'Play again?' })).not.toBeInTheDocument()
  })
})
