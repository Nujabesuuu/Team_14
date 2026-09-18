import { type FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { ApiError } from '@/api/client'
import { Field } from '@/design-system/Field'
import { PhantomButton } from '@/design-system/PhantomButton'
import { TopBar } from '@/design-system/TopBar'
import { useAuth } from '@/stores/auth'

export function Register() {
  const register = useAuth((s) => s.register)
  const navigate = useNavigate()
  const [form, setForm] = useState({ display_name: '', email: '', password: '', birth_date: '' })
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await register(form)
      navigate('/onboarding/dna', { replace: true })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="screen">
      <TopBar title="New player" back="/welcome" kicker="Step 0 / 3" />
      <form onSubmit={submit} className="screen-scroll" style={{ padding: '18px 22px 40px', display: 'grid', gap: 18, alignContent: 'start' }}>
        <Field
          label="Nickname"
          value={form.display_name}
          onChange={(e) => setForm({ ...form, display_name: e.target.value })}
          minLength={2}
          maxLength={40}
          required
          autoComplete="nickname"
        />
        <Field
          label="Email"
          type="email"
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
          required
          autoComplete="email"
        />
        <Field
          label="Password"
          type="password"
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
          minLength={8}
          required
          hint="8+ characters"
          autoComplete="new-password"
        />
        <Field
          label="Birth date"
          type="date"
          value={form.birth_date}
          onChange={(e) => setForm({ ...form, birth_date: e.target.value })}
          required
          hint="Dating mode unlocks at 18. Nobody else sees this."
          error={error}
        />
        <PhantomButton size="lg" block type="submit" disabled={busy}>
          {busy ? 'Creating…' : 'Continue'}
        </PhantomButton>
      </form>
    </div>
  )
}
