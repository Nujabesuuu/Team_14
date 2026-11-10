import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

import { api, setAccountBannedHandler, tokenStore } from '@/api/client'
import type { Me, ModerationReport, MyReport, PublicUser } from '@/api/types'
import { BANNED_CLOSE_CODE, RealtimeClient } from '@/api/ws'
import { ReportSheet } from '@/features/reports/ReportSheet'
import { Moderation } from '@/pages/Moderation'
import { useAuth } from '@/stores/auth'
import { useReports } from '@/stores/reports'

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
const dara = person('u-dara', 'Dara')
const maks = person('u-max', 'Max')

const myReport: MyReport = {
  id: 'r1',
  reported: maks,
  context: 'chat',
  reason: 'harassment',
  status: 'new',
  created_at: '2026-11-09T18:00:00Z',
  decided_at: null,
}
const queued: ModerationReport = {
  ...myReport,
  reporter: dara,
  context_id: 'c1',
  context_label: 'Chat between Dara and Max',
  comment: 'kept asking for my address',
  moderator: null,
}

const me = (role: Me['user']['role']): Me => ({
  user: { id: 'u-mod', email: 'mod@teamate.dev', display_name: 'Iryna', age: 28, is_premium: false, role },
  profile: {
    bio: '',
    avatar_key: 'strategist',
    accent_color: '#F4F1EA',
    photo_url: null,
    modes: ['friends'],
    role: 'igl',
    playstyle: 'casual',
    comms: 'both',
    schedule: [],
    toxicity_tolerance: 1,
    timezone: 'Europe/Kyiv',
    games: [],
    onboarded: true,
  },
})

beforeEach(() => {
  vi.restoreAllMocks()
  sessionStorage.clear()
  useReports.setState({ mine: [], mineLoaded: false, queue: [], decided: [], queueLoaded: false })
  useAuth.setState({ token: null, me: null, notice: null })
})

describe('report sheet (US-09)', () => {
  it('needs a reason, sends the report with its context and confirms it', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse(201, myReport))
    render(<ReportSheet target={maks} context="chat" contextId="c1" onClose={() => {}} />)

    const send = screen.getByRole('button', { name: 'Send report' })
    expect(send).toBeDisabled()
    fireEvent.click(screen.getByRole('button', { name: 'Harassment' }))
    fireEvent.change(screen.getByLabelText(/What happened/), { target: { value: '  kept asking for my address ' } })
    expect(send).toBeEnabled()
    fireEvent.click(send)

    expect(await screen.findByText('Report sent')).toBeInTheDocument()
    expect(screen.getByText(/Max will not know it came from you/)).toBeInTheDocument()
    const [url, init] = fetchMock.mock.calls[0]
    expect(String(url)).toMatch(/\/api\/v1\/reports$/)
    expect(JSON.parse((init as RequestInit).body as string)).toEqual({
      reported_id: 'u-max',
      context: 'chat',
      context_id: 'c1',
      reason: 'harassment',
      comment: 'kept asking for my address',
    })
    expect(useReports.getState().mine.map((r) => r.id)).toEqual(['r1'])
  })

  it('shows the server message when the report is refused and stays open', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      jsonResponse(409, { code: 'ALREADY_REPORTED', detail: 'You already reported this person here.' }),
    )
    render(<ReportSheet target={maks} context="event" contextId="e1" onClose={() => {}} />)
    fireEvent.click(screen.getByRole('button', { name: 'Spam' }))
    fireEvent.click(screen.getByRole('button', { name: 'Send report' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('You already reported this person here.')
    expect(screen.queryByText('Report sent')).not.toBeInTheDocument()
  })

  it('closes on Escape', () => {
    const onClose = vi.fn()
    render(<ReportSheet target={maks} context="photo" contextId="m1" onClose={onClose} />)
    fireEvent.keyDown(window, { key: 'Escape' })
    expect(onClose).toHaveBeenCalled()
  })

  it('takes focus when it opens, keeps Tab inside and returns focus to the opener', () => {
    const opener = document.createElement('button')
    document.body.append(opener)
    opener.focus()
    const { unmount } = render(<ReportSheet target={maks} context="chat" contextId="c1" onClose={() => {}} />)
    const dialog = screen.getByRole('dialog')
    expect(dialog).toHaveFocus()

    // "Send report" is disabled until a reason is picked, so Cancel is the last stop.
    const cancel = screen.getByRole('button', { name: 'Cancel' })
    cancel.focus()
    fireEvent.keyDown(cancel, { key: 'Tab' })
    expect(screen.getByRole('button', { name: 'Harassment' })).toHaveFocus()
    fireEvent.keyDown(screen.getByRole('button', { name: 'Harassment' }), { key: 'Tab', shiftKey: true })
    expect(cancel).toHaveFocus()

    unmount()
    expect(opener).toHaveFocus()
    opener.remove()
  })
})

describe('moderation queue (US-10)', () => {
  const renderQueue = () =>
    render(
      <MemoryRouter initialEntries={['/moderation']}>
        <Moderation />
      </MemoryRouter>,
    )

  it('shows who reported whom, where and why, and moves a decided report out of New', async () => {
    useAuth.setState({ token: 't', me: me('moderator') })
    const decided: ModerationReport = { ...queued, status: 'warned', decided_at: '2026-11-09T19:00:00Z', moderator: person('u-mod', 'Iryna') }
    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockImplementation(async (input) =>
        String(input).endsWith('/decision') ? jsonResponse(200, decided) : jsonResponse(200, [queued]),
      )
    renderQueue()

    expect(await screen.findByText('Chat between Dara and Max')).toBeInTheDocument()
    expect(screen.getByText('Dara')).toBeInTheDocument()
    expect(screen.getByText('Max')).toBeInTheDocument()
    expect(screen.getByText('Harassment')).toBeInTheDocument()
    expect(screen.getByText('kept asking for my address')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Warn' }))
    expect(await screen.findByText('Queue is clear')).toBeInTheDocument()
    const decision = fetchMock.mock.calls.find(([url]) => String(url).endsWith('/moderation/reports/r1/decision'))!
    expect(JSON.parse((decision[1] as RequestInit).body as string)).toEqual({ decision: 'warned' })

    fireEvent.click(screen.getByRole('button', { name: /Decided · 1/ }))
    expect(screen.getByText('Warning issued')).toBeInTheDocument()
    expect(screen.getByText(/by Iryna/)).toBeInTheDocument()
  })

  it('bans only after a second, explicit tap', async () => {
    useAuth.setState({ token: 't', me: me('moderator') })
    const banned: ModerationReport = { ...queued, status: 'banned', decided_at: '2026-11-09T19:00:00Z', moderator: person('u-mod', 'Iryna') }
    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockImplementation(async (input) =>
        String(input).endsWith('/decision') ? jsonResponse(200, banned) : jsonResponse(200, [queued]),
      )
    const sentDecision = () => fetchMock.mock.calls.some(([url]) => String(url).endsWith('/decision'))
    renderQueue()

    fireEvent.click(await screen.findByRole('button', { name: 'Ban' }))
    expect(screen.getByText(/Ban Max\? They are logged out at once/)).toBeInTheDocument()
    expect(sentDecision()).toBe(false)

    fireEvent.click(screen.getByRole('button', { name: 'Keep' }))
    expect(screen.getByRole('button', { name: 'Ban' })).toBeInTheDocument()
    expect(sentDecision()).toBe(false)

    fireEvent.click(screen.getByRole('button', { name: 'Ban' }))
    fireEvent.click(screen.getByRole('button', { name: 'Confirm ban' }))
    expect(await screen.findByText('Queue is clear')).toBeInTheDocument()
    const decision = fetchMock.mock.calls.find(([url]) => String(url).endsWith('/decision'))!
    expect(JSON.parse((decision[1] as RequestInit).body as string)).toEqual({ decision: 'banned' })
  })

  it('does not even ask the API when the viewer is not a moderator', () => {
    useAuth.setState({ token: 't', me: me('user') })
    const fetchMock = vi.spyOn(globalThis, 'fetch')
    renderQueue()
    expect(fetchMock).not.toHaveBeenCalled()
    expect(screen.queryByText('Reports')).not.toBeInTheDocument()
  })
})

describe('banned account', () => {
  it('ends the session on 403 ACCOUNT_BANNED but not on any other 403', async () => {
    const onBanned = vi.fn()
    setAccountBannedHandler(onBanned)
    tokenStore.set('abc')

    vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse(403, { code: 'MODERATOR_ONLY', detail: 'no' }))
    await expect(api.get('/moderation/reports')).rejects.toMatchObject({ status: 403, code: 'MODERATOR_ONLY' })
    expect(onBanned).not.toHaveBeenCalled()
    expect(tokenStore.get()).toBe('abc')

    vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse(403, { code: 'ACCOUNT_BANNED', detail: 'blocked' }))
    await expect(api.get('/me')).rejects.toMatchObject({ status: 403, code: 'ACCOUNT_BANNED' })
    expect(onBanned).toHaveBeenCalledOnce()
    expect(tokenStore.get()).toBeNull()
  })

  it('stops reconnecting when the server closes the socket with the ban code', () => {
    const sockets: { onclose: ((e: { code: number }) => void) | null; close: () => void }[] = []
    vi.stubGlobal(
      'WebSocket',
      class {
        onclose: ((e: { code: number }) => void) | null = null
        close() {}
        constructor() {
          sockets.push(this)
        }
      },
    )
    vi.useFakeTimers()
    try {
      const client = new RealtimeClient()
      const onBanned = vi.fn()
      client.onBanned = onBanned
      client.connect('ws://test/ws')

      sockets[0].onclose?.({ code: BANNED_CLOSE_CODE })
      vi.advanceTimersByTime(60_000)
      expect(onBanned).toHaveBeenCalledOnce()
      expect(sockets).toHaveLength(1)
    } finally {
      vi.useRealTimers()
      vi.unstubAllGlobals()
    }
  })

  it('clears the reports of the previous account when the session ends', async () => {
    useAuth.setState({ token: 't', me: me('moderator') })
    useReports.setState({ mine: [myReport], queue: [queued], queueLoaded: true, mineLoaded: true })
    useAuth.setState({ token: null, me: null })
    await waitFor(() => expect(useReports.getState().queue).toEqual([]))
    expect(useReports.getState().mine).toEqual([])
  })
})
