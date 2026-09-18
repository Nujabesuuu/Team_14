import { NavLink } from 'react-router-dom'

const TABS = [
  { to: '/events', label: 'Events', glyph: 'E' },
  { to: '/discover', label: 'Discover', glyph: 'D' },
  { to: '/matches', label: 'Matches', glyph: 'M' },
  { to: '/me', label: 'Me', glyph: 'ME' },
]

/** Bottom navigation. The active tab gets a red notch that "cuts" upward into the screen. */
export function TabBar() {
  return (
    <nav
      style={{
        position: 'relative',
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        height: 'calc(var(--tab-h) + var(--safe-bottom))',
        paddingBottom: 'var(--safe-bottom)',
        background: 'var(--paper)',
        color: 'var(--ink)',
        clipPath: 'polygon(0 12%, 100% 0, 100% 100%, 0 100%)',
        flexShrink: 0,
      }}
    >
      {TABS.map((t) => (
        <NavLink
          key={t.to}
          to={t.to}
          style={({ isActive }) => ({
            position: 'relative',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 2,
            textDecoration: 'none',
            color: isActive ? 'var(--chalk)' : 'var(--ink)',
            background: isActive ? 'var(--blood)' : 'transparent',
            clipPath: isActive ? 'polygon(8% 0, 100% 6%, 92% 100%, 0 100%)' : undefined,
            transition: 'background var(--dur-fast)',
          })}
        >
          <span className="display" style={{ fontSize: 22, lineHeight: 1 }}>
            {t.glyph}
          </span>
          <span className="cond" style={{ fontSize: 11 }}>
            {t.label}
          </span>
        </NavLink>
      ))}
    </nav>
  )
}
