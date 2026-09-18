import { type FormEvent, useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { api } from '@/api/client'
import { Chip } from '@/design-system/Chip'
import { PhantomButton } from '@/design-system/PhantomButton'
import { MessageBubble } from '@/features/chat/MessageBubble'
import { RevealControls } from '@/features/matches/RevealControls'
import { RevealPhoto } from '@/features/matches/RevealPhoto'
import { useAuth } from '@/stores/auth'
import { useChat } from '@/stores/chat'
import { useMatches } from '@/stores/matches'

export function Chat() {
  const { conversationId = '' } = useParams()
  const navigate = useNavigate()
  const me = useAuth((s) => s.me)
  const match = useMatches((s) => s.list.find((m) => m.conversation_id === conversationId))
  const loadMatches = useMatches((s) => s.load)
  const thread = useChat((s) => s.threads[conversationId])
  const { loadHistory, send } = useChat()
  const [draft, setDraft] = useState('')
  const [showReveal, setShowReveal] = useState(false)
  const [blocked, setBlocked] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)
  const stickToBottom = useRef(true)

  useEffect(() => {
    if (!match) void loadMatches()
    void loadHistory(conversationId)
  }, [conversationId, match, loadMatches, loadHistory])

  const messages = thread?.messages ?? []
  useEffect(() => {
    if (stickToBottom.current && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages.length])

  const onScroll = () => {
    const el = scrollRef.current
    if (!el) return
    stickToBottom.current = el.scrollHeight - el.scrollTop - el.clientHeight < 80
    if (el.scrollTop < 40 && thread?.hasMore && !thread.loading && messages[0]) {
      const before = el.scrollHeight
      void loadHistory(conversationId, messages[0].created_at).then(() => {
        requestAnimationFrame(() => {
          el.scrollTop = el.scrollHeight - before
        })
      })
    }
  }

  const submit = (e: FormEvent) => {
    e.preventDefault()
    if (!draft.trim()) return
    stickToBottom.current = true
    void send(conversationId, draft)
    setDraft('')
  }

  const block = async () => {
    if (!match || !confirm(`Block ${match.other.display_name}? They disappear from everything.`)) return
    await api.post('/blocks', { user_id: match.other.id })
    setBlocked(true)
    navigate('/matches', { replace: true })
  }

  if (!match || !me) return <div className="screen" />
  const other = match.other

  return (
    <div className="screen">
      {/* Header: their photo at their stage, name, compatibility, reveal toggle */}
      <header style={{ position: 'relative', padding: '10px 14px 10px', display: 'flex', alignItems: 'center', gap: 12, background: 'var(--ink-2)' }}>
        <div aria-hidden style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: 6, background: other.accent_color }} />
        <button
          type="button"
          onClick={() => navigate('/matches')}
          aria-label="Back"
          style={{ background: 'transparent', border: 0, color: 'var(--paper)', fontSize: 28, fontFamily: 'var(--font-display)', cursor: 'pointer', padding: '0 4px' }}
        >
          ‹
        </button>
        <button type="button" onClick={() => setShowReveal((v) => !v)} style={{ background: 'transparent', border: 0, padding: 0, cursor: 'pointer' }} aria-label="Toggle reveal panel">
          <RevealPhoto photoUrl={other.photo_url} stage={match.reveal.their_stage} avatar={other.avatar_key} accent={other.accent_color} size={48} />
        </button>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div className="display" style={{ fontSize: 22, lineHeight: 1 }}>
            {other.display_name}
          </div>
          <div style={{ display: 'flex', gap: 6, marginTop: 4 }}>
            <Chip tone="blood" style={{ fontSize: 11, padding: '3px 8px' }}>
              {match.compatibility}% DNA
            </Chip>
            <Chip style={{ fontSize: 11, padding: '3px 8px' }} onClick={() => setShowReveal((v) => !v)}>
              Reveal {match.reveal.their_stage}/3
            </Chip>
          </div>
        </div>
        <PhantomButton size="sm" variant="ghost" onClick={block} disabled={blocked}>
          Block
        </PhantomButton>
      </header>

      {showReveal && (
        <div style={{ padding: '12px 16px', background: 'var(--paper)', color: 'var(--ink)', clipPath: 'polygon(0 0, 100% 0, 100% 90%, 0 100%)' }}>
          <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 10 }}>
            <RevealPhoto photoUrl={other.photo_url} stage={match.reveal.their_stage} avatar={other.avatar_key} accent={other.accent_color} size={72} />
            <div style={{ fontSize: 13 }}>
              <strong>How reveal works.</strong> Match → light blur. Play together again → almost clear. Both tap reveal → clear. You each control your own photo.
            </div>
          </div>
          <RevealControls match={match} />
        </div>
      )}

      <div ref={scrollRef} onScroll={onScroll} className="screen-scroll" style={{ padding: '6px 14px 14px' }}>
        {thread?.loading && messages.length === 0 && <div className="muted cond" style={{ textAlign: 'center', padding: 20 }}>Loading…</div>}
        {!thread?.loading && messages.length === 0 && (
          <div style={{ textAlign: 'center', padding: '40px 20px' }}>
            <div className="display skew" style={{ fontSize: 30, color: 'var(--ash-2)' }}>
              Say the first thing
            </div>
            <p className="muted" style={{ fontSize: 14 }}>
              You already played together. The awkward part is over.
            </p>
          </div>
        )}
        {messages.map((m, i) => {
          const mine = m.sender_id === me.user.id
          const first = i === 0 || messages[i - 1].sender_id !== m.sender_id
          return <MessageBubble key={m.id} message={m} mine={mine} author={mine ? null : other} first={first} />
        })}
      </div>

      <form
        onSubmit={submit}
        style={{
          display: 'flex',
          alignItems: 'stretch',
          background: 'var(--ink-2)',
          borderTop: '2px solid var(--ash)',
          paddingBottom: 'var(--safe-bottom)',
        }}
      >
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Type like you're on voice…"
          maxLength={2000}
          aria-label="Message"
          style={{ flex: 1, padding: '16px 16px', background: 'transparent', border: 0, outline: 'none', fontSize: 16, color: 'var(--paper)' }}
        />
        <button
          type="submit"
          disabled={!draft.trim()}
          className="display"
          style={{
            padding: '0 22px 0 30px',
            background: draft.trim() ? 'var(--blood)' : 'var(--ash)',
            color: 'var(--chalk)',
            border: 0,
            clipPath: 'polygon(28% 0, 100% 0, 100% 100%, 0 100%)',
            fontSize: 22,
            cursor: draft.trim() ? 'pointer' : 'default',
            transition: 'background var(--dur-fast)',
          }}
        >
          Send
        </button>
      </form>
    </div>
  )
}
