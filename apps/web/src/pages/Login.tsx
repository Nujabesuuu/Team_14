import { type FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { ApiError } from '@/api/client'
import { Field } from '@/design-system/Field'
import { PhantomButton } from '@/design-system/PhantomButton'
import { TopBar } from '@/design-system/TopBar'
import { useAuth } from '@/stores/auth'

export function Login() {
  const login = useAuth((s) => s.login)
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await login(email, password)
      navigate('/events', { replace: true })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="screen">
      <TopBar title="Welcome back" back="/welcome" />
      <form onSubmit={submit} className="screen-scroll" style={{ padding: '18px 22px 40px', display: 'grid', gap: 18, alignContent: 'start' }}>
        <Field label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" />
        <Field
          label="Password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          autoComplete="current-password"
          error={error}
        />
        <PhantomButton size="lg" block type="submit" disabled={busy}>
          {busy ? 'Entering…' : 'Enter'}
        </PhantomButton>
        <p className="muted" style={{ fontSize: 13, textAlign: 'center' }}>
          Demo accounts: <code>user01@teamate.dev</code> … <code>user12@teamate.dev</code> / <code>demo1234</code>
        </p>
      </form>
    </div>
  )
}
