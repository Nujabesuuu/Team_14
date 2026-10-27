# Контракт: API (REST + WebSocket)

> **КТ4, крок 3.** Специфікація взаємодії клієнта і сервера під 19 історій MVP: шляхи, методи, вхідні дані, відповіді, коди успіху й помилок.
> Машинна версія того, що вже реалізовано: [openapi.json](openapi.json) (експорт з `GET /openapi.json`), інтерактивно — http://localhost:8000/docs.
> Формат помилок і повний каталог кодів: [errors.md](errors.md). Схема даних: [data-schema.md](data-schema.md).
> Статус: ✅ реалізовано й покрито тестами · 🆕 контракт зафіксовано, реалізація разом з історією на КТ5 · ✏️ ендпоінт є, контракт змінюється.

## Домовленості

| Що | Правило |
|---|---|
| Базовий шлях | `/api/v1` (у dev клієнт ходить через проксі Vite: `http://localhost:5173/api/v1`) |
| Формат | JSON, `Content-Type: application/json`; завантаження фото — `multipart/form-data` |
| Автентифікація | `Authorization: Bearer <JWT>` на всіх ендпоінтах, крім `/health*`, `/auth/*`, `/games`. Без токена → `401 UNAUTHORIZED` ([ADR-0008](../adr/0008-jwt-auth.md)) |
| Ідентифікатори | UUID рядком: `"3f2b…"` |
| Час | ISO 8601 з часовим поясом: `"2026-10-30T18:00:00Z"` |
| Помилки | Завжди `{ "code": "...", "detail": "..." }` ([ADR-0009](../adr/0009-rest-api-error-envelope.md)) |
| Успіх | `200` — читання й дії над ресурсом, `201` — створено, `204` — без тіла |
| Публічний користувач | Об'єкт `PublicUser` — те, що інші бачать про людину. Без email, дати народження і (🆕) без URL фото |

### Спільні об'єкти

```jsonc
// PublicUser
{ "id": "uuid", "display_name": "Nika", "age": 22, "avatar_key": "duelist",
  "accent_color": "#E60012", "is_premium": false,
  "photo_url": "/media/…",       // ✅ зараз; ✏️ прибирається (ADR-0010)
  "has_photo": true,             // 🆕
  "photo_stage": 0 }             // 🆕 0–3: на якій стадії глядач бачить це фото

// Event
{ "id": "uuid", "host": PublicUser, "game": Game, "kind": "squad", "title": "Duo to Diamond tonight",
  "starts_at": "…", "max_slots": 2, "status": "open", "participants": [PublicUser],
  "is_host": true, "is_participant": true, "created_at": "…",
  "is_official": false,           // 🆕 Teamate Night
  "started_at": null, "finished_at": null, "counted_at": null,   // 🆕
  "confirmations": 0, "confirmed_by_me": false,                 // 🆕
  "feedback_closes_at": null }                                  // 🆕 counted_at + 24 год

// Match
{ "id": "uuid", "other": PublicUser, "source": "post_game", "conversation_id": "uuid",
  "reveal": { "my_stage": 1, "their_stage": 1, "my_consent": false, "their_consent": false,
              "early_request_from_me": false, "early_request_from_them": false },
  "compatibility": 41, "last_message": Message | null, "created_at": "…",
  "opener_hint": "You just played Overcooked 2 together. Rematch?" }   // 🆕 null після першого повідомлення
```

---

## Службові (Walking Skeleton)

| Метод | Шлях | Auth | Відповідь 200 | Помилки | Статус |
|---|---|---|---|---|---|
| GET | `/health` | — | `{"status": "ok"}` | | ✅ |
| GET | `/health/db` | — | `{"status": "ok", "database": "sqlite" \| "postgresql"}` — виконано `SELECT 1` | `503 DB_UNAVAILABLE` | ✅ |

## Крок 1. Профіль без фото

### US-01 · Реєстрація 18+ і вхід

| Метод | Шлях | Тіло запиту | Успіх | Помилки | Статус |
|---|---|---|---|---|---|
| POST | `/auth/register` | `{email, password (8–128), display_name (2–40), birth_date: "YYYY-MM-DD"}` | `201 {access_token, token_type: "bearer", user: Account}`; створює порожній профіль | `409 EMAIL_TAKEN`, `422 TOO_YOUNG` (✏️ поріг 13 → 18), `422 VALIDATION_ERROR` | ✅ |
| POST | `/auth/login` | `{email, password}` | `200 {access_token, token_type, user}` | `401 INVALID_CREDENTIALS`, 🆕 `403 ACCOUNT_BANNED` | ✅ |
| GET | `/me` | — | `200 {user: Account, profile: Profile}` | `401 UNAUTHORIZED` | ✅ |

`Account = {id, email, display_name, age, is_premium}` — бачить лише власник.

### US-02, US-18, US-03 · Ігрова ДНК, маска, «Побачення»

| Метод | Шлях | Тіло запиту | Успіх | Помилки | Статус |
|---|---|---|---|---|---|
| GET | `/games` | — | `200 [Game]`, `Game = {id, name, slug, is_chill, cover_color}` | | ✅ |
| PUT | `/me` | Часткове оновлення: `{bio?, avatar_key?, accent_color?, modes?: Mode[], role?, playstyle?, comms?, schedule?, toxicity_tolerance? (1–5), timezone?, games?: [{game_id, rank?}], display_name?}` | `200 {user, profile}`; `profile.onboarded` стає `true` після ≥ 1 гри, ролі й режиму | `422 UNKNOWN_GAME`, `422 DATING_REQUIRES_18`, `422 VALIDATION_ERROR` | ✅ |

### US-04 · Приховане фото

| Метод | Шлях | Тіло запиту | Успіх | Помилки | Статус |
|---|---|---|---|---|---|
| POST | `/me/photo` | multipart `file`: jpeg/png/webp ≤ 5 МБ | `200 {photo_url}` ✏️ → `200 {has_photo: true}`; сервер видаляє EXIF і робить розмиті копії | `422 UNSUPPORTED_PHOTO`, `422 PHOTO_TOO_LARGE` | ✅ ✏️ |
| GET | `/photos/{user_id}` | — | `200 image/jpeg`, `Cache-Control: private, no-store`. Власник — оригінал; метч — копія своєї стадії | `404 PHOTO_NOT_FOUND` для незнайомця, заблокованого, або якщо фото немає (не розкриваємо факт існування) | 🆕 |

## Крок 2. Знаходить гру

### US-05 · Стрічка івентів (разом з Teamate Nights)

| Метод | Шлях | Параметри | Успіх | Помилки | Статус |
|---|---|---|---|---|---|
| GET | `/events` | `game_id?`, `kind?`, `status?`, `mine?=true` | `200 [Event]`: спершу сьогоднішні, далі найближчі; без минулих; без івентів людей, з якими є блокування; Game Date лише для 18+ з «Побаченням». 🆕 `is_official` івенти позначені | | ✅ |
| GET | `/events/{id}` | — | `200 Event` | `404 EVENT_NOT_FOUND` | ✅ |

### US-19 · Створити івент

| Метод | Шлях | Тіло запиту | Успіх | Помилки | Статус |
|---|---|---|---|---|---|
| POST | `/events` | `{game_id, kind?: "squad" \| "game_date", title (3–80), starts_at, max_slots? (2–10)}` | `201 Event`; хост — перший учасник | `422 UNKNOWN_GAME`, `422 GAME_DATE_REQUIRES_CHILL_GAME`, `422 GAME_DATE_REQUIRES_DATING_MODE`, 🆕 `422 STARTS_IN_PAST`, `422 VALIDATION_ERROR` | ✅ |

### US-06 · Приєднатися

| Метод | Шлях | Успіх | Помилки | Статус |
|---|---|---|---|---|
| POST | `/events/{id}/join` | `200 Event`; учасникам надсилається WS `event.updated` | `409 EVENT_FULL`, `409 EVENT_NOT_OPEN`, `409 ALREADY_JOINED`, `403 EVENT_NOT_VISIBLE`, `403 BLOCKED` ✏️ → `403 EVENT_NOT_VISIBLE` (заблокований не має дізнатися причину, NEVER-05), `404 EVENT_NOT_FOUND` | ✅ ✏️ |
| POST | `/events/{id}/leave` | `200 Event` | `409 HOST_CANNOT_LEAVE`, `409 EVENT_STARTED`, `409 NOT_PARTICIPANT` | ✅ |

## Крок 3. Грає разом

### US-07 · Старт, завершення і підтвердження гри

| Метод | Шлях | Тіло | Успіх | Помилки | Статус |
|---|---|---|---|---|---|
| POST | `/events/{id}/start` | — | `200 Event`, `status = in_progress`, 🆕 `started_at` | `403 HOST_ONLY`, `409 INVALID_TRANSITION` | ✅ |
| POST | `/events/{id}/finish` | — | `200 Event`, `status = finished`, 🆕 `finished_at`. Якщо хост не завершив, сервер вважає івент завершеним через 3 год після старту | `403 HOST_ONLY`, `409 INVALID_TRANSITION` | ✅ |
| POST | `/events/{id}/cancel` | — | `200 Event`, `status = cancelled` | `403 HOST_ONLY`, `409 INVALID_TRANSITION` | ✅ |
| POST | `/events/{id}/confirm` | — | `200 Event` з `confirmations`, `confirmed_by_me = true`; коли ≥ 2 підтвердження і гра тривала ≥ 15 хв — `counted_at` заповнюється, учасникам WS `event.updated` | `403 NOT_PARTICIPANT`, `409 EVENT_NOT_FINISHED`, `409 ALREADY_CONFIRMED` | 🆕 |

### US-08 · Заблокувати

| Метод | Шлях | Тіло | Успіх | Помилки | Статус |
|---|---|---|---|---|---|
| POST | `/blocks` | `{user_id}` | `204`; 🆕 якщо обоє записані на майбутній івент — заблокованого виписують | `422 CANNOT_BLOCK_SELF`. Повторне блокування ідемпотентне — теж `204` | ✅ |

### US-09 · Поскаржитись

| Метод | Шлях | Тіло | Успіх | Помилки | Статус |
|---|---|---|---|---|---|
| POST | `/reports` | `{reported_id, context: "event" \| "chat" \| "photo", context_id, reason: ReportReason, comment? (≤ 500)}` | `201 {id, status: "new", created_at}` | `422 CANNOT_REPORT_SELF`, `404 USER_NOT_FOUND`, `422 VALIDATION_ERROR` (нема причини) | 🆕 |
| GET | `/reports/mine` | — | `200 [{id, reported: PublicUser, context, reason, status, created_at, decided_at}]` — скаржник бачить, що скаргу розглянуто | | 🆕 |

### US-10 · Рішення модератора

| Метод | Шлях | Тіло / параметри | Успіх | Помилки | Статус |
|---|---|---|---|---|---|
| GET | `/moderation/reports` | `status?=new` | `200 [{id, reporter: PublicUser, reported: PublicUser, context, context_id, reason, comment, status, created_at}]` | `403 MODERATOR_ONLY` | 🆕 |
| POST | `/moderation/reports/{id}/decision` | `{decision: "dismissed" \| "warned" \| "banned"}` | `200 Report` з `moderator_id`, `decided_at`; при `banned` заповнюється `users.banned_at` | `403 MODERATOR_ONLY`, `404 REPORT_NOT_FOUND`, `409 REPORT_ALREADY_DECIDED` | 🆕 |

## Крок 4. Таємно обирає «ближче»

### US-11, US-12 · «Зіграємо ще?» і метч

| Метод | Шлях | Тіло | Успіх | Помилки | Статус |
|---|---|---|---|---|---|
| GET | `/events/{id}/feedback` | — | `200 {pending: [PublicUser], done: [uuid]}`; 🆕 `closer_allowed: {user_id: bool}` для кожного партнера | `403 NOT_PARTICIPANT`, `409 EVENT_NOT_FINISHED` ✏️ → `409 GAME_NOT_COUNTED` | ✅ ✏️ |
| POST | `/events/{id}/feedback` | `{to_user_id, answer: "again" \| "closer" \| "no"}` | `200 {match_created: bool, match_id: uuid \| null}`; при взаємному `closer` — WS `match.new` обом. Одностороння відповідь нікому не надсилається | `409 ALREADY_RATED`, `422 NOT_A_TEAMMATE`, 🆕 `409 FEEDBACK_WINDOW_CLOSED`, 🆕 `422 CLOSER_REQUIRES_DATING` | ✅ ✏️ |
| GET | `/matches` | — | `200 [Match]` | | ✅ |
| GET | `/matches/{id}` | — | `200 Match` | `403 NOT_YOUR_MATCH`, `404 MATCH_NOT_FOUND` | ✅ |

### US-13 · Свайпи

| Метод | Шлях | Тіло / параметри | Успіх | Помилки | Статус |
|---|---|---|---|---|---|
| GET | `/discover` | `mode = duo \| friends \| dating` | `200 {cards: [DiscoverCard] (≤ 20), rights_left: int \| null}`; `DiscoverCard = {user: PublicUser, bio, modes, role, playstyle, comms, schedule, games, compatibility}`; ✏️ фото не віддається (стадія 0 — лише маска) | `422 MODE_NOT_ENABLED` | ✅ ✏️ |
| POST | `/swipes` | `{to_user_id, direction: "left" \| "right"}` | `200 {match_created, match_id, rights_left}` | `429 SWIPE_LIMIT`, `409 ALREADY_SWIPED`, `422 NO_SHARED_MODE`, `422 CANNOT_SWIPE_SELF`, `403 BLOCKED`, `404 USER_NOT_FOUND` | ✅ |

## Крок 5. Пише першою

### US-14, US-15 · Чат і підказка першого повідомлення

| Метод | Шлях | Тіло / параметри | Успіх | Помилки | Статус |
|---|---|---|---|---|---|
| GET | `/conversations/{id}/messages` | `before?: datetime`, `limit? (1–100, за замовчуванням 50)` | `200 [Message]` хронологічно; `Message = {id, conversation_id, sender_id, body, created_at}` | `403 NOT_YOUR_CONVERSATION`, `403 BLOCKED`, `404 CONVERSATION_NOT_FOUND` | ✅ |
| POST | `/conversations/{id}/messages` | `{body}` (1–2000 після обрізання) | `201 Message`; обом WS `message.new`. Основний шлях — WS `message.send`, це HTTP-фолбек | `422 EMPTY_MESSAGE`, `422 MESSAGE_TOO_LONG`, `403 BLOCKED` | ✅ |
| — | `Match.opener_hint` | — | Рядок з назвою спільної гри (`post_game`) або спільної улюбленої гри з ДНК (`mutual_like`); `null` після першого повідомлення | | 🆕 |

## Крок 6. Показує фото

### US-16, US-17 · Стадії і згода

| Метод | Шлях | Успіх | Помилки | Статус |
|---|---|---|---|---|
| POST | `/matches/{id}/reveal/consent` | `200 Match`; якщо згода обох — `stage = 3` для обох; іншій стороні WS `reveal.updated` | `403 NOT_YOUR_MATCH`, `404 MATCH_NOT_FOUND` | ✅ |
| GET | `/photos/{user_id}` | Див. US-04: стадія 1 — сильне розмиття, 2 — легке, 3 — оригінал | `404 PHOTO_NOT_FOUND` | 🆕 |

Стадія 2 настає автоматично, коли пара з метчем отримує ще одну зараховану спільну гру (WS `reveal.updated`).

## Поза MVP (вже є в прототипі, контракт не змінюється)

| Метод | Шлях | Що робить | Помилки |
|---|---|---|---|
| POST | `/me/premium` | `{enabled}` — імітація Teamate+ | |
| POST | `/swipes/undo` | `204`, скасувати останній свайп | `402 PREMIUM_REQUIRED`, `404 NOTHING_TO_UNDO` |
| GET | `/likes/incoming` | `200 [DiscoverCard]` — хто лайкнув (лише свайпи, не відповіді після гри) | `402 PREMIUM_REQUIRED` |
| POST | `/matches/{id}/reveal/early-request` | Запит на раннє розкриття | `402 PREMIUM_REQUIRED` |
| POST | `/matches/{id}/reveal/early-accept` | Прийняти запит → стадія 3 | `409 NO_EARLY_REQUEST` |

---

## WebSocket `/api/v1/ws?token=<JWT>`

Одне з'єднання на вкладку; усі з'єднання користувача отримують його події. Невалідний токен → закриття з кодом `4401`. Клієнт перепідключається з експоненційною затримкою ([ADR-0004](../adr/0004-in-memory-ws-hub.md)).

**Клієнт → сервер**

```json
{ "type": "message.send", "conversation_id": "uuid", "body": "gg" }
{ "type": "ping" }
```

**Сервер → клієнт**

| `type` | Коли | Payload | Історії |
|---|---|---|---|
| `message.new` | Нове повідомлення в моїй розмові | `message` | US-14 |
| `match.new` | Створено метч (взаємне `closer` або взаємний лайк) | `match` | US-12, US-13 |
| `reveal.updated` | Згода, ранній запит або стадія 2 після спільної гри | `match` | US-16, US-17 |
| `event.updated` | Будь-яка зміна івенту, де я учасник (зокрема 🆕 підтвердження і зарахування) | `event` | US-06, US-07 |
| `pong` | Відповідь на `ping` | — | |
| `error` | Невідомий тип, чужа розмова або помилка з REST | `code`, `detail` | |

---

## Трасування: історія → ендпоінти

| Історія | Ендпоінти | Готовність |
|---|---|---|
| US-01 | `POST /auth/register`, `POST /auth/login`, `GET /me` | ✅, ✏️ поріг 18 |
| US-02 | `GET /games`, `PUT /me` | ✅ |
| US-18 | `PUT /me {avatar_key}` | ✅, ✏️ default `duelist` |
| US-03 | `PUT /me {modes}` | ✅ |
| US-04 | `POST /me/photo`, `GET /photos/{user_id}` | ✏️ 🆕 |
| US-05 | `GET /events`, `GET /events/{id}` | ✅, 🆕 `is_official` |
| US-06 | `POST /events/{id}/join`, `/leave` | ✅ |
| US-19 | `POST /events` | ✅, 🆕 `STARTS_IN_PAST` |
| US-07 | `/start`, `/finish`, `/cancel`, `POST /events/{id}/confirm` | ✅ + 🆕 |
| US-08 | `POST /blocks` | ✅ |
| US-09 | `POST /reports`, `GET /reports/mine` | 🆕 |
| US-10 | `GET /moderation/reports`, `POST /moderation/reports/{id}/decision` | 🆕 |
| US-11 | `GET`, `POST /events/{id}/feedback` | ✅, 🆕 24 год і «Побачення» |
| US-12 | `POST /events/{id}/feedback` → `match.new`, `GET /matches` | ✅ |
| US-13 | `GET /discover`, `POST /swipes` | ✅, ✏️ без фото |
| US-14 | `GET`/`POST /conversations/{id}/messages`, WS `message.send` | ✅ |
| US-15 | `Match.opener_hint` | 🆕 |
| US-16 | `GET /photos/{user_id}`, WS `reveal.updated` | 🆕 |
| US-17 | `POST /matches/{id}/reveal/consent` | ✅ |
