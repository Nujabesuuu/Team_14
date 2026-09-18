import { RealtimeClient } from '@/api/ws'

describe('RealtimeClient', () => {
  it('dispatches events to handlers registered for that type only', () => {
    const client = new RealtimeClient()
    const onMessage = vi.fn()
    const onMatch = vi.fn()
    client.on('message.new', onMessage)
    client.on('match.new', onMatch)

    const message = { id: 'm1', conversation_id: 'c1', sender_id: 'u1', body: 'gg', created_at: '2026-01-01T00:00:00Z' }
    client.dispatch({ type: 'message.new', message })

    expect(onMessage).toHaveBeenCalledWith({ type: 'message.new', message })
    expect(onMatch).not.toHaveBeenCalled()
  })

  it('unsubscribes', () => {
    const client = new RealtimeClient()
    const handler = vi.fn()
    const off = client.on('pong', handler)
    off()
    client.dispatch({ type: 'pong' })
    expect(handler).not.toHaveBeenCalled()
  })

  it('reports send() as false when no socket is open', () => {
    expect(new RealtimeClient().send({ type: 'ping' })).toBe(false)
  })
})
