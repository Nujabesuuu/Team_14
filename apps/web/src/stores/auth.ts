import { create } from 'zustand'

import { api, setUnauthorizedHandler, tokenStore, wsUrl } from '@/api/client'
import { realtime } from '@/api/ws'
import type { Me, ProfileUpdate, TokenResponse } from '@/api/types'

interface AuthState {
  token: string | null
  me: Me | null
  loading: boolean
  bootstrap: () => Promise<void>
  register: (input: { email: string; password: string; display_name: string; birth_date: string }) => Promise<void>
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  refreshMe: () => Promise<Me>
  updateProfile: (patch: ProfileUpdate) => Promise<Me>
  uploadPhoto: (file: File) => Promise<void>
  setPremium: (enabled: boolean) => Promise<void>
}

export const useAuth = create<AuthState>((set, get) => {
  const acceptToken = async (res: TokenResponse) => {
    tokenStore.set(res.access_token)
    set({ token: res.access_token })
    realtime.connect(wsUrl(res.access_token))
    await get().refreshMe()
  }

  setUnauthorizedHandler(() => {
    realtime.disconnect()
    set({ token: null, me: null })
  })

  return {
    token: tokenStore.get(),
    me: null,
    loading: true,

    async bootstrap() {
      const token = tokenStore.get()
      if (!token) {
        set({ loading: false })
        return
      }
      try {
        realtime.connect(wsUrl(token))
        await get().refreshMe()
      } catch {
        tokenStore.set(null)
        set({ token: null, me: null })
      } finally {
        set({ loading: false })
      }
    },

    async register(input) {
      await acceptToken(await api.post<TokenResponse>('/auth/register', input))
    },

    async login(email, password) {
      await acceptToken(await api.post<TokenResponse>('/auth/login', { email, password }))
    },

    logout() {
      tokenStore.set(null)
      realtime.disconnect()
      set({ token: null, me: null })
    },

    async refreshMe() {
      const me = await api.get<Me>('/me')
      set({ me })
      return me
    },

    async updateProfile(patch) {
      const me = await api.put<Me>('/me', patch)
      set({ me })
      return me
    },

    async uploadPhoto(file) {
      const form = new FormData()
      form.append('file', file)
      await api.post('/me/photo', form)
      await get().refreshMe()
    },

    async setPremium(enabled) {
      const me = await api.post<Me>('/me/premium', { enabled })
      set({ me })
    },
  }
})
