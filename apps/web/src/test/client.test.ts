import { api, ApiError, setUnauthorizedHandler, tokenStore, wsUrl } from '@/api/client'

const jsonResponse = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })

describe('api client', () => {
  beforeEach(() => {
    sessionStorage.clear()
    vi.restoreAllMocks()
  })

  it('attaches the bearer token from sessionStorage', async () => {
    tokenStore.set('abc')
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse(200, { ok: true }))
    await api.get('/me')
    const init = fetchMock.mock.calls[0][1] as RequestInit
    expect((init.headers as Record<string, string>).Authorization).toBe('Bearer abc')
  })

  it('throws ApiError with the server code and clears the token on 401', async () => {
    tokenStore.set('expired')
    const onUnauthorized = vi.fn()
    setUnauthorizedHandler(onUnauthorized)
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse(401, { code: 'UNAUTHORIZED', detail: 'nope' }))

    await expect(api.get('/me')).rejects.toMatchObject({ status: 401, code: 'UNAUTHORIZED' })
    expect(tokenStore.get()).toBeNull()
    expect(onUnauthorized).toHaveBeenCalled()
  })

  it('flattens FastAPI validation errors into one message', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      jsonResponse(422, { detail: [{ msg: 'field required' }, { msg: 'too short' }] }),
    )
    const err = await api.post('/auth/register', {}).catch((e: unknown) => e)
    expect(err).toBeInstanceOf(ApiError)
    expect((err as ApiError).message).toBe('field required; too short')
  })

  it('builds a ws:// url carrying the token', () => {
    expect(wsUrl('t0k')).toMatch(/^ws:\/\/.*\/api\/v1\/ws\?token=t0k$/)
  })
})
