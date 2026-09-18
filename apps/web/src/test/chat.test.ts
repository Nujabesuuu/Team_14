import type { Message } from '@/api/types'
import { mergeMessages, useChat } from '@/stores/chat'

const msg = (id: string, at: string): Message => ({
  id,
  conversation_id: 'c1',
  sender_id: 'u1',
  body: id,
  created_at: at,
})

describe('chat store', () => {
  it('merges by id and keeps chronological order', () => {
    const merged = mergeMessages(
      [msg('b', '2026-01-01T00:00:02Z'), msg('a', '2026-01-01T00:00:01Z')],
      [msg('b', '2026-01-01T00:00:02Z'), msg('c', '2026-01-01T00:00:03Z')],
    )
    expect(merged.map((m) => m.id)).toEqual(['a', 'b', 'c'])
  })

  it('receive() appends a live message to the right thread without duplicates', () => {
    const { receive } = useChat.getState()
    receive(msg('x', '2026-01-01T00:00:01Z'))
    receive(msg('x', '2026-01-01T00:00:01Z'))
    receive(msg('y', '2026-01-01T00:00:00Z'))
    expect(useChat.getState().threads.c1.messages.map((m) => m.id)).toEqual(['y', 'x'])
  })
})
