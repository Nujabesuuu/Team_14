import type { ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'

interface Props {
  title: ReactNode
  back?: boolean | string
  right?: ReactNode
  kicker?: string
}

/** Screen header: a red diagonal slab with an Anton title bleeding out of it. */
export function TopBar({ title, back, right, kicker }: Props) {
  const navigate = useNavigate()
  return (
    <header style={{ position: 'relative', padding: '14px 18px 10px', display: 'flex', alignItems: 'flex-end', gap: 12 }}>
      <div
        aria-hidden
        style={{
          position: 'absolute',
          left: -20,
          top: 0,
          width: '62%',
          height: '100%',
          background: 'var(--blood)',
          clipPath: 'polygon(0 0, 100% 0, 88% 100%, 0 100%)',
        }}
      />
      {back && (
        <button
          type="button"
          onClick={() => (typeof back === 'string' ? navigate(back) : navigate(-1))}
          aria-label="Back"
          style={{
            position: 'relative',
            background: 'var(--ink)',
            color: 'var(--paper)',
            border: 0,
            width: 38,
            height: 38,
            clipPath: 'var(--cut-chip)',
            fontFamily: 'var(--font-display)',
            fontSize: 22,
            cursor: 'pointer',
            flexShrink: 0,
          }}
        >
          ‹
        </button>
      )}
      <div style={{ position: 'relative', flex: 1, minWidth: 0 }}>
        {kicker && (
          <div className="cond" style={{ fontSize: 12, color: 'var(--chalk)', opacity: 0.9 }}>
            {kicker}
          </div>
        )}
        <h1
          className="display skew"
          style={{
            margin: 0,
            fontSize: 34,
            color: 'var(--chalk)',
            textShadow: '3px 3px 0 var(--ink)',
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}
        >
          {title}
        </h1>
      </div>
      {right && <div style={{ position: 'relative', flexShrink: 0 }}>{right}</div>}
    </header>
  )
}
