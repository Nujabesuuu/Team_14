/**
 * Minimal typed fetch wrapper. Tokens live in sessionStorage on purpose:
 * two browser tabs = two different demo accounts.
 */

const TOKEN_KEY = 'teamate.token'
const API_BASE = `${import.meta.env.VITE_API_URL ?? ''}/api/v1`

export class ApiError extends Error {
  status: number
  code: string

  constructor(status: number, code: string, detail: string) {
    super(detail)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

export const tokenStore = {
  get(): string | null {
    try {
      return sessionStorage.getItem(TOKEN_KEY)
    } catch {
      return null
    }
  },
  set(token: string | null) {
    try {
      if (token) sessionStorage.setItem(TOKEN_KEY, token)
      else sessionStorage.removeItem(TOKEN_KEY)
    } catch {
      /* private mode: session-only auth still works in memory */
    }
  },
}

let onUnauthorized: (() => void) | null = null
export function setUnauthorizedHandler(fn: () => void) {
  onUnauthorized = fn
}

async function request<T>(method: string, path: string, body?: unknown, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = { ...(init?.headers as Record<string, string>) }
  const token = tokenStore.get()
  if (token) headers.Authorization = `Bearer ${token}`

  let payload: BodyInit | undefined
  if (body instanceof FormData) {
    payload = body
  } else if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    payload = JSON.stringify(body)
  }

  const res = await fetch(`${API_BASE}${path}`, { ...init, method, headers, body: payload })
  if (res.status === 204) return undefined as T

  const text = await res.text()
  const data = text ? JSON.parse(text) : null
  if (!res.ok) {
    if (res.status === 401) {
      tokenStore.set(null)
      onUnauthorized?.()
    }
    const code = data?.code ?? (res.status === 422 ? 'VALIDATION_ERROR' : 'HTTP_ERROR')
    const detail =
      typeof data?.detail === 'string'
        ? data.detail
        : Array.isArray(data?.detail)
          ? data.detail.map((d: { msg: string }) => d.msg).join('; ')
          : res.statusText
    throw new ApiError(res.status, code, detail)
  }
  return data as T
}

export const api = {
  get: <T>(path: string) => request<T>('GET', path),
  post: <T>(path: string, body?: unknown) => request<T>('POST', path, body),
  put: <T>(path: string, body?: unknown) => request<T>('PUT', path, body),
  del: <T>(path: string) => request<T>('DELETE', path),
}

export function mediaUrl(path: string | null | undefined): string | undefined {
  if (!path) return undefined
  if (path.startsWith('http')) return path
  return `${import.meta.env.VITE_API_URL ?? ''}${path}`
}

export function wsUrl(token: string): string {
  const base = import.meta.env.VITE_API_URL || window.location.origin
  const url = new URL(`${base}/api/v1/ws`)
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
  url.searchParams.set('token', token)
  return url.toString()
}
