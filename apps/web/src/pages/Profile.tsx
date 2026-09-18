import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { ApiError, mediaUrl } from '@/api/client'
import type { Mode } from '@/api/types'
import { Avatar } from '@/design-system/Avatar'
import { Chip } from '@/design-system/Chip'
import { Panel } from '@/design-system/Panel'
import { PhantomButton } from '@/design-system/PhantomButton'
import { TopBar } from '@/design-system/TopBar'
import { ModeToggles } from '@/features/profile/ModeToggles'
import { useAuth } from '@/stores/auth'

export function Profile() {
  const navigate = useNavigate()
  const { me, updateProfile, uploadPhoto, setPremium, logout } = useAuth()
  const fileRef = useRef<HTMLInputElement>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  if (!me) return null
  const p = me.profile

  const setModes = async (modes: Mode[]) => {
    setError(null)
    try {
      await updateProfile({ modes })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not save')
    }
  }

  const onPhoto = async (file?: File) => {
    if (!file) return
    setBusy(true)
    setError(null)
    try {
      await uploadPhoto(file)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Upload failed')
    } finally {
      setBusy(false)
    }
  }

  const photo = mediaUrl(p.photo_url)

  return (
    <div className="screen">
      <TopBar title={me.user.display_name} kicker={me.user.is_premium ? 'Teamate+' : 'Free'} right={me.user.is_premium ? <Chip tone="gold">+</Chip> : undefined} />
      <div className="screen-scroll" style={{ padding: '14px 18px 24px', display: 'grid', gap: 18, alignContent: 'start' }}>
        <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
          <Avatar avatar={p.avatar_key} accent={p.accent_color} size={84} />
          <div
            style={{
              width: 84,
              height: 84,
              clipPath: 'var(--cut-card-alt)',
              background: photo ? `center/cover url(${photo})` : 'var(--ink-2)',
              border: photo ? undefined : '2px dashed var(--ash-2)',
              display: 'grid',
              placeItems: 'center',
              color: 'var(--ash-2)',
              fontSize: 11,
              fontFamily: 'var(--font-cond)',
              textTransform: 'uppercase',
            }}
          >
            {!photo && 'No photo'}
          </div>
          <div style={{ display: 'grid', gap: 8, flex: 1 }}>
            <PhantomButton size="sm" variant="paper" onClick={() => fileRef.current?.click()} disabled={busy}>
              {busy ? 'Uploading' : photo ? 'Change photo' : 'Add photo'}
            </PhantomButton>
            <PhantomButton size="sm" variant="ghost" onClick={() => navigate('/onboarding/avatar')}>
              Change hero
            </PhantomButton>
            <input ref={fileRef} type="file" accept="image/jpeg,image/png,image/webp" hidden onChange={(e) => onPhoto(e.target.files?.[0])} />
          </div>
        </div>
        <p className="muted" style={{ margin: 0, fontSize: 13 }}>
          Your photo is blurred for everyone by default. It only becomes clear for a match when <em>you</em> agree.
        </p>

        <Panel tone="paper">
          <div className="cond" style={{ fontSize: 12, color: 'var(--blood)' }}>
            Game DNA
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, margin: '8px 0' }}>
            {p.role && <Chip tone="blood">{p.role}</Chip>}
            {p.playstyle && <Chip tone="paper" style={{ borderColor: 'var(--ink)' }}>{p.playstyle}</Chip>}
            {p.comms && <Chip tone="paper" style={{ borderColor: 'var(--ink)' }}>{p.comms}</Chip>}
            {p.schedule.map((s) => (
              <Chip key={s} tone="paper" style={{ borderColor: 'var(--ash-2)', color: 'var(--ash-2)' }}>
                {s}
              </Chip>
            ))}
          </div>
          <div className="cond" style={{ fontSize: 13, color: 'var(--ash-2)' }}>
            {p.games.map((g) => g.name).join(' · ') || 'No games yet'}
          </div>
          {p.bio && <p style={{ margin: '10px 0 0', fontSize: 14 }}>{p.bio}</p>}
          <div style={{ marginTop: 12 }}>
            <PhantomButton size="sm" onClick={() => navigate('/onboarding/dna')}>
              Edit DNA
            </PhantomButton>
          </div>
        </Panel>

        <section>
          <div className="cond" style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 8 }}>
            Modes
          </div>
          <ModeToggles value={p.modes} onChange={setModes} age={me.user.age} />
        </section>

        <Panel tone="ink" ghost>
          <div className="display skew" style={{ fontSize: 26, color: 'var(--gold)' }}>
            Teamate+
          </div>
          <p style={{ fontSize: 13, margin: '6px 0 12px' }}>
            Incoming likes, unlimited swipes, undo, early reveal requests. Payments are out of scope for this build — the toggle simulates a subscription.
          </p>
          <PhantomButton size="sm" variant={me.user.is_premium ? 'ghost' : 'gold'} onClick={() => setPremium(!me.user.is_premium)}>
            {me.user.is_premium ? 'Deactivate (demo)' : 'Activate (demo)'}
          </PhantomButton>
        </Panel>

        {error && <p style={{ color: 'var(--blood)', fontWeight: 600, margin: 0 }}>{error}</p>}
        <PhantomButton variant="danger" block onClick={() => { logout(); navigate('/welcome', { replace: true }) }}>
          Log out
        </PhantomButton>
        <p className="muted" style={{ fontSize: 12, textAlign: 'center' }}>
          {me.user.email}
        </p>
      </div>
    </div>
  )
}
