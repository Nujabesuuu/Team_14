import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import type { EventKind } from '@/api/types'
import { Chip } from '@/design-system/Chip'
import { Empty } from '@/design-system/Empty'
import { PhantomButton } from '@/design-system/PhantomButton'
import { TopBar } from '@/design-system/TopBar'
import { EventCard } from '@/features/events/EventCard'
import { useAuth } from '@/stores/auth'
import { useEvents } from '@/stores/events'

type Filter = 'all' | EventKind | 'mine'

export function Events() {
  const navigate = useNavigate()
  const me = useAuth((s) => s.me)
  const { feed, mine, loaded, loadFeed, loadMine } = useEvents()
  const [filter, setFilter] = useState<Filter>('all')
  const dating = me?.profile.modes.includes('dating')

  useEffect(() => {
    void loadFeed()
    void loadMine()
  }, [loadFeed, loadMine])

  const list = filter === 'mine' ? mine : filter === 'all' ? feed : feed.filter((e) => e.kind === filter)

  return (
    <div className="screen">
      <TopBar
        title="Events"
        kicker={`Hey ${me?.user.display_name ?? ''}`}
        right={
          <PhantomButton size="sm" onClick={() => navigate('/events/new')}>
            + Host
          </PhantomButton>
        }
      />
      <div style={{ display: 'flex', gap: 8, padding: '8px 18px 12px', overflowX: 'auto' }}>
        <Chip active={filter === 'all'} onClick={() => setFilter('all')}>
          All
        </Chip>
        <Chip active={filter === 'squad'} onClick={() => setFilter('squad')}>
          Squad
        </Chip>
        {dating && (
          <Chip active={filter === 'game_date'} onClick={() => setFilter('game_date')} tone="gold">
            Game dates
          </Chip>
        )}
        <Chip active={filter === 'mine'} onClick={() => setFilter('mine')}>
          Mine
        </Chip>
      </div>
      <div className="screen-scroll" style={{ padding: '4px 18px 24px', display: 'grid', gap: 16, alignContent: 'start' }}>
        {loaded && list.length === 0 && (
          <Empty
            title="Nobody's queued"
            hint="Host the first event tonight. Somebody is always looking for a duo."
            action={<PhantomButton onClick={() => navigate('/events/new')}>Host an event</PhantomButton>}
          />
        )}
        {list.map((e, i) => (
          <EventCard key={e.id} event={e} index={i} />
        ))}
      </div>
    </div>
  )
}
