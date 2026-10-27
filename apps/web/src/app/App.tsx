import { useEffect } from 'react'
import { Navigate, Outlet, Route, Routes, useLocation, useNavigate } from 'react-router-dom'

import { useAuth } from '@/stores/auth'
import { useMatches } from '@/stores/matches'
import { TabBar } from '@/design-system/TabBar'
import { Wipe } from '@/design-system/Wipe'
import { Welcome } from '@/pages/Welcome'
import { Register } from '@/pages/Register'
import { Login } from '@/pages/Login'
import { OnboardingDna } from '@/pages/OnboardingDna'
import { OnboardingAvatar } from '@/pages/OnboardingAvatar'
import { OnboardingModes } from '@/pages/OnboardingModes'
import { Events } from '@/pages/Events'
import { EventNew } from '@/pages/EventNew'
import { EventDetail } from '@/pages/EventDetail'
import { Feedback } from '@/pages/Feedback'
import { MatchCelebration } from '@/pages/MatchCelebration'
import { Matches } from '@/pages/Matches'
import { Chat } from '@/pages/Chat'
import { Discover } from '@/pages/Discover'
import { Likes } from '@/pages/Likes'
import { Profile } from '@/pages/Profile'
import { Status } from '@/pages/Status'

function Splash() {
  return (
    <div className="screen" style={{ alignItems: 'center', justifyContent: 'center' }}>
      <div className="display skew" style={{ fontSize: 56, color: 'var(--blood)' }}>
        Teamate
      </div>
    </div>
  )
}

/** Requires a session; also funnels un-onboarded users into the DNA flow. */
function Protected({ needsOnboarding = true }: { needsOnboarding?: boolean }) {
  const { token, me, loading } = useAuth()
  const location = useLocation()
  if (loading) return <Splash />
  if (!token || !me) return <Navigate to="/welcome" replace state={{ from: location }} />
  if (needsOnboarding && !me.profile.onboarded && !location.pathname.startsWith('/onboarding')) {
    return <Navigate to="/onboarding/dna" replace />
  }
  return <Outlet />
}

function Public() {
  const { token, me, loading } = useAuth()
  if (loading) return <Splash />
  if (token && me) return <Navigate to={me.profile.onboarded ? '/events' : '/onboarding/dna'} replace />
  return <Outlet />
}

function WithTabs() {
  return (
    <>
      <Wipe>
        <Outlet />
      </Wipe>
      <TabBar />
    </>
  )
}

/** Any "match.new" pushed over the socket interrupts whatever screen is open. */
function MatchInterrupt() {
  const pending = useMatches((s) => s.pendingCelebration)
  const navigate = useNavigate()
  const location = useLocation()
  useEffect(() => {
    if (pending && !location.pathname.startsWith('/match/')) navigate(`/match/${pending.id}`)
  }, [pending, navigate, location.pathname])
  return null
}

export function App() {
  const bootstrap = useAuth((s) => s.bootstrap)
  useEffect(() => {
    void bootstrap()
  }, [bootstrap])

  return (
    <div className="stage">
      <div className="phone">
        <div className="halftone" />
        <MatchInterrupt />
        <Routes>
          <Route element={<Public />}>
            <Route path="/welcome" element={<Welcome />} />
            <Route path="/register" element={<Register />} />
            <Route path="/login" element={<Login />} />
          </Route>

          <Route element={<Protected needsOnboarding={false} />}>
            <Route path="/onboarding/dna" element={<OnboardingDna />} />
            <Route path="/onboarding/avatar" element={<OnboardingAvatar />} />
            <Route path="/onboarding/modes" element={<OnboardingModes />} />
          </Route>

          <Route element={<Protected />}>
            <Route element={<WithTabs />}>
              <Route path="/events" element={<Events />} />
              <Route path="/discover" element={<Discover />} />
              <Route path="/matches" element={<Matches />} />
              <Route path="/me" element={<Profile />} />
            </Route>
            <Route path="/events/new" element={<EventNew />} />
            <Route path="/events/:id" element={<EventDetail />} />
            <Route path="/events/:id/feedback" element={<Feedback />} />
            <Route path="/match/:id" element={<MatchCelebration />} />
            <Route path="/chat/:conversationId" element={<Chat />} />
            <Route path="/likes" element={<Likes />} />
          </Route>

          {/* Walking-skeleton check (KT4): public, works logged in or out. */}
          <Route path="/status" element={<Status />} />

          <Route path="*" element={<Navigate to="/events" replace />} />
        </Routes>
      </div>
    </div>
  )
}
