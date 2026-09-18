# Teamate MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the full Teamate MVP — mobile-first React client + FastAPI backend + PostgreSQL/SQLite — demonstrating the loop event → played → "play again?" → match → chat → photo reveal, plus swipes, modes, Game Date and premium status.

**Architecture:** Monorepo `apps/api` (FastAPI, async SQLAlchemy, pure-Python domain rules under `app/domain`, WebSocket hub) and `apps/web` (React 18 + TS + Vite, Zustand stores, Motion animations, "Phantom UI" design system, Capacitor-ready). Domain rules are pure functions tested without a DB; API routes are thin and call services that persist state.

**Tech Stack:** Python 3.12+, FastAPI, SQLAlchemy 2 async, aiosqlite/asyncpg, Pydantic 2, python-jose, passlib[bcrypt], pytest, httpx · React 18, TypeScript, Vite, React Router 6, Zustand, framer-motion, Tailwind 3, Vitest, Capacitor 6 · Docker Compose, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-18-teamate-mvp-design.md`

## Global Constraints

- Code, identifiers, comments, commit messages: **English**. Docs in `docs/`: Ukrainian.
- No AI attribution in commits (no `Co-authored-by`, no "Claude").
- Palette tokens: `--ink #0A0A0A`, `--paper #F4F1EA`, `--blood #E60012`, `--blood-deep #9B000C`, `--ash #2A2A2A`, `--chalk #FFFFFF`, `--gold #F5C518` (gold only for premium).
- Fonts: Anton (display), Barlow / Barlow Condensed (UI).
- Avatars are original SVG masks with keys: `raven, jester, kitsune, marionette, sentinel, vesper, nomad, oracle`.
- Mobile-first viewport 390×844, max content width 480 px.
- Dating mode requires age ≥ 18. Free swipe limit: 20 right-swipes per UTC day.
- JWT stored in `sessionStorage`.
- Reveal stages 0–3 are per user (each user reveals their own photo).
- Event status enum: `open | full | in_progress | finished | cancelled`. Event kind: `squad | game_date`.

---

## File map

```
apps/api/
  pyproject.toml
  app/__init__.py
  app/main.py                  # FastAPI app factory, routers, CORS, startup create_all
  app/core/config.py           # Settings (DATABASE_URL, JWT_SECRET, MEDIA_DIR, CORS_ORIGINS)
  app/core/security.py         # hash/verify password, create/decode JWT
  app/core/db.py               # engine, session factory, Base, get_session dependency
  app/core/deps.py             # current_user dependency
  app/core/errors.py           # ApiError(code, status, detail) + handler
  app/models/*.py              # SQLAlchemy models (user, profile, game, event, feedback, swipe, match, reveal, chat, block)
  app/schemas/*.py             # Pydantic schemas per domain
  app/domain/events.py         # pure: transitions, can_join, can_leave, visibility
  app/domain/matching.py       # pure: feedback→match decision, swipe→match, daily limit
  app/domain/reveal.py         # pure: stage rules, effective_stage
  app/domain/compatibility.py  # pure: score(dna_a, dna_b) -> int
  app/services/*.py            # DB-backed services per domain
  app/routers/*.py             # auth, me, games, events, feedback, discover, swipes, matches, reveal, chat, blocks, ws
  app/ws/hub.py                # ConnectionHub: connect/disconnect/send_to_user
  app/seed.py                  # python -m app.seed
  tests/conftest.py            # app + in-memory sqlite + client + user factory
  tests/domain/test_*.py
  tests/api/test_*.py
apps/web/
  package.json, vite.config.ts, tsconfig.json, tailwind.config.ts, postcss.config.js, index.html, capacitor.config.ts
  src/main.tsx, src/app/router.tsx, src/app/PhoneFrame.tsx
  src/design-system/tokens.css, global.css
  src/design-system/{PhantomButton,Panel,Chip,Wipe,Halftone,Field,TopBar,TabBar}.tsx
  src/avatars/{index.ts, Raven.tsx ... Oracle.tsx}
  src/api/client.ts, src/api/types.ts, src/api/ws.ts
  src/stores/{auth,profile,events,matches,chat}.ts
  src/pages/*.tsx
  src/features/{onboarding,events,feedback,discover,matches,chat,profile}/...
  src/test/*.test.ts(x)
docker-compose.yml, apps/api/Dockerfile, apps/web/Dockerfile
.github/workflows/ci.yml
docs/{architecture,api,data-model,design-system,demo,android,ai-log}.md, docs/adr/000{1,2,3}-*.md
```

---

## Phase A — Backend core

### Task 1: API scaffold, config, DB, health

**Files:** Create `apps/api/pyproject.toml`, `app/main.py`, `app/core/{config,db,errors}.py`, `tests/conftest.py`, `tests/api/test_health.py`, `apps/api/.env.example`, `apps/api/.gitignore` (media/, .venv, *.db).

**Interfaces produced:** `create_app() -> FastAPI`; `get_session()` async dependency yielding `AsyncSession`; `Base` declarative; `ApiError(status: int, code: str, detail: str)`; `settings.database_url` default `sqlite+aiosqlite:///./teamate.db`.

- [ ] Write `tests/api/test_health.py`:
```python
import pytest
@pytest.mark.anyio
async def test_health(client):
    r = await client.get("/api/v1/health")
    assert r.status_code == 200 and r.json() == {"status": "ok"}
```
- [ ] `conftest.py`: override `DATABASE_URL=sqlite+aiosqlite://` (in-memory, `StaticPool`), fixture `client` using `httpx.AsyncClient(transport=ASGITransport(app))`, create tables per test.
- [ ] Implement scaffold; run `pytest`; commit `feat(api): scaffold FastAPI app with config, db and health endpoint`.

### Task 2: Models

**Files:** Create `app/models/{__init__,user,profile,game,event,feedback,swipe,match,reveal,chat,block}.py`.

**Produces:** Tables per spec §4. Enums: `EventStatus`, `EventKind`, `FeedbackAnswer(again|closer|no)`, `SwipeDirection`, `MatchSource`, `AvatarKey`, `Mode(duo|friends|dating)`, `Role(support|carry|flex|tank|igl)`, `Playstyle(casual|competitive)`, `Comms(voice|text|both)`. `Profile.modes` and `Profile.schedule` stored as JSON lists. Helper `canonical_pair(a, b) -> tuple[UUID, UUID]` in `app/models/match.py`.

- [ ] Test: `tests/api/test_models.py` creates a user+profile, an event with participant, asserts `create_all` works and relationships load.
- [ ] Implement; run; commit `feat(api): add SQLAlchemy models`.

### Task 3: Auth

**Files:** `app/core/security.py`, `app/core/deps.py`, `app/schemas/auth.py`, `app/services/auth.py`, `app/routers/auth.py`, `tests/api/test_auth.py`.

**Produces:** `POST /auth/register {email,password,display_name,birth_date} -> {access_token, user}`; `POST /auth/login`; `current_user: User` dependency (401 `UNAUTHORIZED`); `User.age` property; conftest fixture `make_user(email=..., birth_date=..., premium=False) -> (user, headers)`.

- [ ] Tests: register returns token; duplicate email → 409 `EMAIL_TAKEN`; login wrong password → 401; `GET /me` without token → 401; register also creates empty Profile.
- [ ] Implement (bcrypt via passlib, HS256 JWT, exp 7 days); commit `feat(api): auth with JWT`.

### Task 4: Profile, games, photo, premium toggle

**Files:** `app/schemas/profile.py`, `app/services/profile.py`, `app/routers/{me,games}.py`, `tests/api/test_profile.py`.

**Produces:** `GET /me` → `{user:{id,email,display_name,age,is_premium}, profile:{bio,avatar_key,accent_color,photo_url,modes,role,playstyle,comms,schedule,toxicity_tolerance,timezone,games:[{id,name,rank}]}}`; `PUT /me` partial update (`games` as list of `{game_id, rank}`); `POST /me/photo` multipart → `{photo_url}` saved under `MEDIA_DIR`, served at `/media/...`; `POST /me/premium {enabled}`; `GET /games`.

- [ ] Tests: PUT updates DNA and games; enabling `dating` mode with age 17 → 422 `DATING_REQUIRES_18`; photo upload returns url and file exists; premium toggle flips flag.
- [ ] Implement; commit `feat(api): profile, games and premium toggle`.

### Task 5: Pure domain rules (TDD)

**Files:** `app/domain/{events,matching,reveal,compatibility}.py`, `tests/domain/test_{events,matching,reveal,compatibility}.py`.

**Produces:**
```python
# events.py
def next_status_after_join(status, participants, max_slots) -> EventStatus
def can_join(status, participants, max_slots, is_participant) -> None | str  # error code
def can_leave(status, is_host) -> None | str
def can_transition(status, action: Literal["start","finish","cancel"], is_host) -> None | str
def event_visible(event_kind, viewer_modes, viewer_age) -> bool
# matching.py
def match_after_feedback(mine: FeedbackAnswer, theirs: FeedbackAnswer | None) -> bool
def match_after_swipe(mine: SwipeDirection, theirs: SwipeDirection | None) -> bool
def can_swipe(is_premium, rights_today: int, limit: int = 20) -> None | str
def share_mode(a_modes, b_modes) -> bool
# reveal.py
STAGES = (0, 1, 2, 3)
def stage_after_match() -> int  # 1
def stage_after_shared_event(current) -> int  # max(current, 2)
def stage_after_consent(current, my_consent, their_consent) -> int  # 3 if both else current
def blur_px(stage) -> int  # 24, 12, 4, 0
# compatibility.py
@dataclass GameDna: games:set[str]; role; playstyle; comms; schedule:set[str]; toxicity:int(1-5)
def score(a: GameDna, b: GameDna) -> int  # 0..100
```
- [ ] Write tests per spec §5 (state machine table, host cannot leave, game_date invisible to non-dating viewer or age<18, closer+closer → match, closer+again → no match, 20th right swipe ok / 21st blocked for free, premium unlimited, stage progression, `score` identical DNA → 100, disjoint → 0, support+carry role bonus).
- [ ] Implement; commit `feat(api): pure domain rules for events, matching, reveal, compatibility`.

### Task 6: Events API

**Files:** `app/schemas/event.py`, `app/services/events.py`, `app/routers/events.py`, `tests/api/test_events.py`.

**Produces:** `GET /events?game_id&kind&status` (filters out invisible per `event_visible` and blocked users); `POST /events {game_id,kind,title,starts_at,max_slots}` (game_date forces max_slots=2, requires chill game and host dating mode); `GET /events/{id}`; `POST /events/{id}/{join|leave|start|finish|cancel}`. Service method `finish_event(event_id)` returns list of participant pairs (used later for reveal stage 2). Every mutation calls `hub.send_to_users(participant_ids, {"type":"event.updated","event":...})`.

- [ ] Tests: create/join/full/start/finish happy path; join full → 409 `EVENT_FULL`; non-host start → 403; game_date with non-chill game → 422; dating event hidden from duo-only user.
- [ ] Implement; commit `feat(api): events lifecycle`.

### Task 7: Feedback → matches → conversations

**Files:** `app/schemas/{feedback,match}.py`, `app/services/{feedback,matches}.py`, `app/routers/{feedback,matches}.py`, `tests/api/test_feedback_match.py`.

**Produces:** `GET /events/{id}/feedback` → pending co-participants; `POST /events/{id}/feedback {to_user_id, answer}` → `{match_created, match_id?}`; service `create_match(session, a, b, source) -> Match` (idempotent; creates `Conversation` and two `PhotoReveal` rows stage 1; emits `match.new` to both). `GET /matches` → list `{id, other:{id,display_name,avatar_key,accent_color,photo_url}, conversation_id, my_stage, their_stage, my_consent, their_consent, early_request_from, compatibility, last_message}`.

- [ ] Tests: feedback before finished → 409 `EVENT_NOT_FINISHED`; non-participant → 403; closer+closer creates one match, second closer is idempotent; closer+again → none; match list shows reveal stage 1.
- [ ] Implement; commit `feat(api): post-game feedback and matches`.

### Task 8: Discover, swipes, likes

**Files:** `app/schemas/discover.py`, `app/services/discover.py`, `app/routers/{discover,swipes}.py`, `tests/api/test_swipes.py`.

**Produces:** `GET /discover?mode=` → up to 20 profiles not yet swiped, not self, not blocked, not matched, sharing the mode (dating → both 18+), each with `compatibility`; `POST /swipes {to_user_id,direction}` → `{match_created, match_id?, rights_left}`; `POST /swipes/undo` (premium only, deletes last swipe) ; `GET /likes/incoming` (premium only, 402 `PREMIUM_REQUIRED` otherwise).

- [ ] Tests: discover excludes swiped and non-shared-mode; mutual right creates match `mutual_like`; 21st right swipe → 429 `SWIPE_LIMIT`; undo without premium → 402.
- [ ] Implement; commit `feat(api): discover and swipes`.

### Task 9: Reveal endpoints

**Files:** `app/services/reveal.py`, `app/routers/reveal.py`, `tests/api/test_reveal.py`; modify `services/events.py::finish_event` to bump stage 2 for matched pairs.

**Produces:** `POST /matches/{id}/reveal/consent` (sets my consent; if both → both stage 3), `/reveal/early-request` (premium), `/reveal/early-accept` (sets both stage 3). Emits `reveal.updated` to both.

- [ ] Tests: consent by one keeps stage; by both → 3; finishing a shared event after match → 2; early-request without premium → 402.
- [ ] Implement; commit `feat(api): photo reveal`.

### Task 10: Chat REST + WebSocket hub

**Files:** `app/ws/hub.py`, `app/schemas/chat.py`, `app/services/chat.py`, `app/routers/{chat,ws}.py`, `tests/api/test_chat.py`.

**Produces:** `GET /conversations/{id}/messages?before=<iso>&limit=50`; `WS /api/v1/ws?token=` accepting `{"type":"message.send","conversation_id","body"}` and pushing `message.new`; `ConnectionHub.send_to_user(user_id, payload)` used by all services (best-effort, swallow closed sockets).

- [ ] Tests: history 403 for non-member; WS: two clients (starlette `TestClient` websocket) — A sends, B receives `message.new`; message persisted.
- [ ] Implement; commit `feat(api): chat with websocket hub`.

### Task 11: Blocks + seed

**Files:** `app/routers/blocks.py`, `app/services/blocks.py`, `app/seed.py`, `tests/api/test_blocks.py`.

- [ ] Tests: after block, discover and events hide the user; chat history returns 403.
- [ ] Seed: 12 games (Valorant, Dota 2, League of Legends, CS2, Apex Legends, Rocket League, Minecraft*, Among Us*, Overcooked 2*, GeoGuessr*, It Takes Two*, Stardew Valley*; `*`=chill), 12 users `user01..user12@teamate.dev` / `demo1234`, varied DNA & avatars, 6 open events, 2 finished events, 2 matches with messages. Idempotent (skips if users exist).
- [ ] Commit `feat(api): blocks and demo seed`.

## Phase B — Frontend

### Task 12: Web scaffold + design system

**Files:** Vite React-TS project in `apps/web`; `tokens.css`, `global.css` (fonts import, halftone background, phone frame); primitives `PhantomButton` (variants primary/ghost/paper, clip-path polygon, offset shadow), `Panel` (paper polygon card), `Chip`, `Field` (input with skew label), `TopBar`, `TabBar` (4 tabs with red active notch), `Wipe` (route transition), `Halftone`; `PhoneFrame`; `router.tsx` with placeholder pages; vitest config.

- [ ] Test `src/test/tokens.test.ts`: importing `tokens` exposes `blood === '#E60012'` (export tokens also as TS object `src/design-system/tokens.ts`).
- [ ] `npm run build` passes; commit `feat(web): scaffold with Phantom UI design system`.

### Task 13: Avatars

**Files:** `src/avatars/*.tsx`, `src/avatars/index.ts` exporting `AVATARS: Record<AvatarKey, FC<{accent:string; size?:number}>>` and `AVATAR_KEYS`.

- [ ] Test: `AVATAR_KEYS.length === 8`, each renders an `<svg>`.
- [ ] Draw 8 distinct masks (geometric: bird beak, jester bells, fox ears, puppet strings, visor, crescent hood, wanderer scarf, third-eye circle). Commit `feat(web): original avatar set`.

### Task 14: API client, auth store, WS client, auth pages

**Files:** `src/api/client.ts` (`api.get/post/put`, attaches JWT from `sessionStorage`, throws `ApiError{code,status}`), `src/api/types.ts` (mirrors schemas), `src/api/ws.ts` (`connect(token)`, `on(type, handler)`, auto-reconnect w/ backoff), `src/stores/auth.ts`, pages `Welcome`, `Register`, `Login`, `ProtectedRoute`.

- [ ] Test `client.test.ts`: attaches `Authorization`; 401 clears token. `ws.test.ts`: dispatches event to registered handler.
- [ ] Commit `feat(web): auth flow`.

### Task 15: Onboarding

**Files:** `src/features/onboarding/{DnaStep,AvatarStep,ModesStep}.tsx`, pages, `stores/profile.ts`.

- [ ] DNA: one question per screen (games multi-select chips, role, playstyle, comms, schedule chips, toxicity 1–5 slider), progress bar as red diagonal. Avatar: carousel + accent picker. Modes: three toggles; dating disabled with message if age<18. Redirect to `/events` after `PUT /me`.
- [ ] Commit `feat(web): onboarding`.

### Task 16: Events

**Files:** `stores/events.ts`, `features/events/{EventCard,EventForm,ParticipantRow}.tsx`, pages `Events`, `EventNew`, `EventDetail`.

- [ ] Feed with kind filter (Squad / Game Date), skewed cards, slots indicator; detail with role-aware buttons (Join/Leave; host: Start/Finish/Cancel); when `finished` → button "Rate teammates" → `/events/:id/feedback`. Subscribes to `event.updated`.
- [ ] Commit `feat(web): events`.

### Task 17: Feedback + match screen + matches list + reveal

**Files:** pages `Feedback`, `MatchCelebration`, `Matches`; `features/matches/{RevealPhoto,RevealControls}.tsx`; `stores/matches.ts`.

- [ ] Feedback: one co-participant at a time, three big polygon buttons (`PLAY AGAIN` / `GET CLOSER` / `NOPE`); on `match_created` navigate to `/match/:id`. Match screen: red, two avatars slam in from edges, `IT'S A MATCH`, "Open chat". `RevealPhoto` applies `filter: blur(${blurPx(stage)}px) grayscale(stage===0?1:0)`; controls: Reveal (consent) + premium early request/accept. Test: `RevealPhoto` stage→blur.
- [ ] Commit `feat(web): feedback, match and reveal`.

### Task 18: Chat

**Files:** `stores/chat.ts`, `features/chat/{MessageBubble,Composer,ChatHeader}.tsx`, page `Chat`.

- [ ] Persona-style bubbles (parallelogram + tail, avatar chip), compatibility % in header with `RevealPhoto` thumbnail, composer with skewed SEND, staggered entrance animation, scroll-to-bottom, history pagination on scroll top. Test: store appends and de-duplicates by id, sorts by created_at.
- [ ] Commit `feat(web): chat`.

### Task 19: Discover (swipes) + premium

**Files:** `features/discover/{SwipeCard,SwipeDeck}.tsx`, page `Discover`, `features/premium/PremiumBadge.tsx`, `pages/Likes`.

- [ ] Drag with Motion (`drag="x"`, threshold 120px, rotate), stamp overlay (`LIKE`/`NOPE`), card shows avatar, blurred photo, DNA chips, compatibility; mode selector (duo/friends/dating); `rights_left` counter; premium: undo button, Likes page with gold accents.
- [ ] Commit `feat(web): discover and premium`.

### Task 20: Profile page + polish

- [ ] Profile: editable DNA, photo upload, premium toggle (dev), block list absent (YAGNI), logout. Page-load stagger on Events; route wipe everywhere; empty states with copy. Commit `feat(web): profile and polish`.

## Phase C — Infra & docs

### Task 21: Docker, CI

- [ ] `apps/api/Dockerfile` (python:3.12-slim, uvicorn), `apps/web/Dockerfile` (node:22, vite dev), `docker-compose.yml` (postgres:16 + api + web, `DATABASE_URL=postgresql+asyncpg://…`), `.env.example` both; `.github/workflows/ci.yml` (jobs `api`: ruff+pytest; `web`: npm ci, tsc, eslint, vitest, build). Commit `chore: docker compose and CI`.

### Task 22: Capacitor

- [ ] `npm i @capacitor/core @capacitor/cli @capacitor/android`, `capacitor.config.ts` (`appId: dev.teamate.app`, `webDir: dist`, `server.cleartext: true`), `docs/android.md`. Do not commit `android/` build output beyond what `cap add` generates. Commit `feat(web): capacitor android config`.

### Task 23: Documentation

- [ ] `docs/architecture.md` (Mermaid diagram), `api.md`, `data-model.md` (Mermaid ER), `design-system.md`, `demo.md`, `ai-log.md`, `adr/0001-fastapi-over-spring.md`, `adr/0002-capacitor-over-react-native.md`, `adr/0003-per-user-reveal.md`; README: add "Запуск", "Структура", "Документація" sections, keep checkpoint-1 content. Commit `docs: architecture, api, demo and ADRs`.

---

## Self-review

- Spec coverage: §3 → T12–13; §4 → T2; §5 → T5 (+T6–9 wiring); §6 → T3–T11; §7 → T14–T20; §8 → T11 + docs/demo; §9 → tests in every task; §10 → T21; §11 → T23; §12 risks → ADRs + sessionStorage in T14.
- Types: `EventStatus`, `FeedbackAnswer`, `MatchSource`, `AvatarKey` used consistently; `create_match` from T7 reused in T8; `finish_event` from T6 modified in T9.
