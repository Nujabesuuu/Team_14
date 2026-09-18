import type { InputHTMLAttributes, ReactNode, TextareaHTMLAttributes } from 'react'

interface BaseProps {
  label: string
  hint?: string
  error?: string | null
}

const labelStyle = {
  display: 'inline-block',
  padding: '3px 10px',
  background: 'var(--paper)',
  color: 'var(--ink)',
  clipPath: 'var(--cut-tag)',
  fontFamily: 'var(--font-cond)',
  fontWeight: 800,
  fontSize: 13,
  letterSpacing: '0.1em',
  textTransform: 'uppercase' as const,
  marginBottom: 6,
}

const controlStyle = {
  width: '100%',
  padding: '12px 14px',
  background: 'var(--ink-2)',
  color: 'var(--paper)',
  border: '2px solid var(--ash-2)',
  borderLeft: '6px solid var(--blood)',
  outline: 'none',
  fontSize: 16,
}

function Wrap({ label, hint, error, children }: BaseProps & { children: ReactNode }) {
  return (
    <label style={{ display: 'block' }}>
      <span style={labelStyle}>{label}</span>
      {children}
      {(error || hint) && (
        <span
          style={{
            display: 'block',
            marginTop: 6,
            fontSize: 13,
            color: error ? 'var(--blood)' : 'var(--muted)',
            fontWeight: error ? 600 : 400,
          }}
        >
          {error ?? hint}
        </span>
      )}
    </label>
  )
}

export function Field({ label, hint, error, style, ...rest }: BaseProps & InputHTMLAttributes<HTMLInputElement>) {
  return (
    <Wrap label={label} hint={hint} error={error}>
      <input {...rest} style={{ ...controlStyle, borderColor: error ? 'var(--blood)' : undefined, ...style }} />
    </Wrap>
  )
}

export function TextArea({
  label,
  hint,
  error,
  style,
  ...rest
}: BaseProps & TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <Wrap label={label} hint={hint} error={error}>
      <textarea {...rest} style={{ ...controlStyle, resize: 'vertical', minHeight: 90, ...style }} />
    </Wrap>
  )
}
