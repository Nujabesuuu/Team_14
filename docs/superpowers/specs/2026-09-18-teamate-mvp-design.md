# Teamate MVP — дизайн-специфікація

Дата: 2026-09-18 · Статус: погоджено з тімлідом, готово до плану реалізації

Цей документ фіксує технічне рішення для першої повної версії Teamate (MVP з README). Він є артефактом для контрольних точок 3 (вимоги) та 4 (ескіз технічного рішення) і джерелом істини для реалізації.

---

## 1. Мета і межі

**Мета:** працюючий мобільний (mobile-first web + Android через Capacitor) застосунок, у якому можна наживо показати повний цикл продукту:

```
Реєстрація → Game DNA + аватар → Івент → «Зіграли» → «Зіграємо ще?» → Метч → Чат → Поступове розкриття фото
```

плюс свайпи профілів, режими Duo/Friends/Dating, Game Date, преміум-статус.

**Не входить у MVP (non-goals):** реальні платежі, селфі-верифікація, інтеграції зі Steam/Discord/Riot, push-сповіщення, серії ігор для пар, подвійні побачення, Teamate Nights як окрема сутність (їх імітують seed-івенти), модерація скарг (є лише block).

---

## 2. Стек і структура репозиторію

| Шар | Технологія | Обґрунтування |
|---|---|---|
| Frontend | React 18, TypeScript, Vite, React Router 6, Zustand, Motion (framer-motion), Tailwind 3 (утиліти) + CSS-модулі для дизайн-системи | Швидка збірка, повний контроль над візуалом, той самий код іде в Android |
| Mobile | Capacitor 6 | `npm run build && npx cap sync android` дає APK без переписування |
| Backend | Python 3.12+, FastAPI, SQLAlchemy 2 (async), Pydantic 2, python-jose (JWT), passlib[bcrypt], websockets | Тонкий API + доменна логіка, яку легко тестувати |
| БД | PostgreSQL 16 (Docker). Для локального запуску без Docker — SQLite через ту саму SQLAlchemy | Трирівнева архітектура; DevOps-робота для Максима |
| Тести | pytest + httpx (API, домен), Vitest + Testing Library (UI, стор) | Артефакт для контрольної точки 6 |
| CI | GitHub Actions: lint + тести обох застосунків на кожен PR | Артефакт для контрольної точки 7 і теми DevOps |

Монорепозиторій:

```
Team_14/
├── apps/
│   ├── web/                 # React-клієнт (+ android/ після cap add)
│   └── api/                 # FastAPI
├── docs/                    # документація (укр.), ADR, журнал ШІ
├── docker-compose.yml       # db + api + web
├── .github/workflows/ci.yml
└── README.md
```

Мова коду, коментарів, назв, commit-повідомлень — англійська. Документація в `docs/` — українська.

---

## 3. Дизайн-система «Phantom UI»

Референс — візуальна мова Persona 5 Royal, але не її асети. Оригінальні шрифти, форми й персонажі.

**Палітра (CSS-змінні):**
- `--ink` `#0A0A0A` — фон; `--paper` `#F4F1EA` — «папір» для карток; `--blood` `#E60012` — головний акцент; `--blood-deep` `#9B000C`; `--ash` `#2A2A2A`; `--chalk` `#FFFFFF`; `--gold` `#F5C518` — лише для преміуму.
- Правило: 70 % чорного, 20 % білого/паперу, 10 % червоного. Золото — тільки для Teamate+.

**Типографіка (Google Fonts):**
- Display: **Anton** — заголовки капсом, нахил `skew(-8deg)`, ліґатури вимкнені.
- UI/body: **Barlow** (400/600) і **Barlow Condensed** (700) для лейблів і чипів.

**Форми й ефекти:**
- Картки й кнопки — не прямокутники, а поліґони через `clip-path` (зрізані кути, «рвана» діагональ).
- Фон — halftone-точки (`radial-gradient` патерн) + діагональні смуги в куті екрана.
- Переходи між екранами — «wipe» червоною діагональною плашкою (Motion `AnimatePresence`), 240 мс.
- Кнопка дії — білий текст на червоному поліґоні з чорним «двійником» зміщеним на 4 px (ефект друку).
- Чат: бульбашки — паралелограми з гострим «хвостом», чужі — на папері чорним текстом, свої — чорні з білим текстом і червоною облямівкою; аватар співрозмовника — круглий чип з чорною обводкою, що «виглядає» з-за бульбашки; поле вводу — чорна смуга зі скошеним червоним «SEND».
- Кожен екран має один «жест», який запам'ятовується: на матчі — червоний екран з двома аватарами, що врізаються з країв, і надпис `IT'S A MATCH` нахилом.

**Аватари:** 8 оригінальних SVG-персонажів «маска + силует + акцент», кодові імена: `raven`, `jester`, `kitsune`, `marionette`, `sentinel`, `vesper`, `nomad`, `oracle`. Реалізуються як React-компоненти з пропом `accent` (колір), використовуються в профілі, картках і чаті. Це не персонажі гри.

**Mobile-first:** макет 390×844, максимум ширини 480 px на десктопі (центрована «телефонна» рамка на темному фоні), безпечні зони під Capacitor.

---

## 4. Модель даних

Усі id — UUID. Часи — UTC.

| Сутність | Поля | Примітки |
|---|---|---|
| `users` | id, email (unique), password_hash, display_name, birth_date, is_premium (bool), created_at | `age` обчислюється; Dating доступний лише з 18 |
| `profiles` | user_id (PK/FK), bio, avatar_key (enum з 8), accent_color, photo_url (nullable), modes (array: duo/friends/dating), role, playstyle, comms, schedule (array), toxicity_tolerance, timezone | Game DNA = role/playstyle/comms/schedule/toxicity |
| `profile_games` | profile_id, game_id, rank (text, optional) | M:N |
| `games` | id, name, slug, is_chill (bool), cover_color | `is_chill=true` — доступні для Game Date |
| `events` | id, host_id, game_id, kind (`squad`/`game_date`), title, starts_at, max_slots, status (`open`/`full`/`in_progress`/`finished`/`cancelled`), created_at | `game_date`: max_slots=2, лише chill-ігри |
| `event_participants` | event_id, user_id, joined_at | host — теж учасник |
| `post_game_feedback` | event_id, from_user_id, to_user_id, answer (`again`/`closer`/`no`) | unique(event, from, to) |
| `swipes` | from_user_id, to_user_id, direction (`left`/`right`), created_at | unique(from, to) |
| `matches` | id, user_a_id, user_b_id, source (`post_game`/`mutual_like`), created_at | user_a < user_b (канонічний порядок), unique пара |
| `photo_reveals` | match_id, user_id, stage (0–3), consent_next (bool), early_request (bool) | по одному рядку на кожного учасника метчу |
| `conversations` | id, match_id (unique), created_at | створюється разом із метчем |
| `messages` | id, conversation_id, sender_id, body, created_at | |
| `blocks` | blocker_id, blocked_id | заблоковані не бачать одне одного ніде |

---

## 5. Доменні правила (те, що тестується юніт-тестами)

**Івент:**
- `open` → `full` (коли учасників = max_slots) → `in_progress` (host натискає Start) → `finished` (host натискає Finish). Host може `cancel` до `in_progress`.
- Приєднатись можна лише до `open`. Вийти — до `in_progress`. Host не може вийти.
- `game_date`: host обирає гру з `is_chill=true`, слотів 2, у хоста увімкнений режим `dating`.
- Учасник бачить івенти у режимі `dating` лише якщо сам увімкнув `dating` і йому 18+.

**Фідбек і метч:**
- Фідбек можливий тільки коли івент `finished`, лише щодо співучасників, один раз на пару.
- Відповіді приватні. Метч створюється в тій самій транзакції, коли з'являється друга відповідь `closer` для пари; джерело `post_game`.
- Свайп `right` обох → метч із джерелом `mutual_like`. Свайп можливий лише до профілів, що мають хоча б один спільний режим зі свайпером; у режимі `dating` — лише 18+.
- Безкоштовний ліміт — 20 свайпів `right` на добу; преміум — без ліміту, плюс `undo` останнього свайпу.
- Дублювання метчу неможливе: якщо пара вже має метч, другий шлях лише оновлює нічого.

**Reveal (фото):**
- Стадія 0 — усі бачать фото з сильним блюром (blur 24 px, grayscale). Це стан за замовчуванням для будь-кого без метчу.
- Стадія 1 — автоматично при метчі (blur 12 px).
- Стадія 2 — після того, як пара разом брала участь у `finished` івенті вже після метчу (blur 4 px).
- Стадія 3 — чисте фото, лише коли **обидва** натиснули «Reveal» (`consent_next=true` в обох). Стадії індивідуальні: кожен відкриває своє фото; я можу бачити тебе чіткіше лише якщо ти дав згоду.
- Преміум може надіслати `early_request`; якщо другий погоджується — обидва переходять на стадію 3. Без згоди нічого не змінюється.

**Сумісність (0–100):** детермінована формула в `api/app/domain/compatibility.py`: спільні ігри (до 35), playstyle збіг (15), comms збіг (10), перетин schedule (до 20), близькість toxicity_tolerance (10), комплементарність role (10; support+carry = повний бал). Показується на картках профілю і в чаті.

**Безпека доступу:** будь-який ресурс (чат, фідбек, reveal) доступний лише учасникам відповідного метчу/івенту; інакше 403. Заблоковані пари не бачать одне одного у свайпах, івентах, чаті.

---

## 6. API (FastAPI, префікс `/api/v1`)

| Метод | Шлях | Призначення |
|---|---|---|
| POST | `/auth/register` | email, password, display_name, birth_date → JWT |
| POST | `/auth/login` | → JWT (access, 7 днів; refresh поза MVP) |
| GET/PUT | `/me` | акаунт + профіль (Game DNA, modes, avatar, photo_url) |
| POST | `/me/photo` | multipart upload → зберігається в `apps/api/media/`, повертає url |
| POST | `/me/premium` | dev-перемикач преміуму (імітація оплати) |
| GET | `/games` | список ігор |
| GET/POST | `/events` | фільтри: game, kind, status; створення |
| GET | `/events/{id}` | деталі + учасники |
| POST | `/events/{id}/join` · `/leave` · `/start` · `/finish` · `/cancel` | переходи станів |
| GET | `/events/{id}/feedback` | кого ще треба оцінити |
| POST | `/events/{id}/feedback` | to_user_id, answer → { match_created: bool } |
| GET | `/discover` | стек профілів для свайпів (з compatibility) |
| POST | `/swipes` | to_user_id, direction → { match_created } |
| POST | `/swipes/undo` | преміум |
| GET | `/likes/incoming` | преміум: хто лайкнув |
| GET | `/matches` | список метчів з conversation_id, reveal-стадіями |
| POST | `/matches/{id}/reveal/consent` · `/reveal/early-request` · `/reveal/early-accept` | reveal |
| GET | `/conversations/{id}/messages?before=` | історія (50 за раз) |
| POST | `/blocks` | блокування |
| WS | `/ws?token=` | реальний час |

Помилки — RFC 7807-подібний JSON `{ "detail": "...", "code": "EVENT_NOT_OPEN" }`. OpenAPI-документація доступна на `/docs`.

**WebSocket-протокол** (JSON, одне з'єднання на користувача):
- клієнт → `{"type":"message.send","conversation_id":…,"body":…}`
- сервер → `{"type":"message.new", "message": {…}}`, `{"type":"match.new", "match": {…}}`, `{"type":"reveal.updated", …}`, `{"type":"event.updated", …}`
- Сервер тримає `dict[user_id, set[WebSocket]]` у пам'яті (одна репліка — достатньо для MVP; це зафіксовано як ризик).

---

## 7. Frontend

**Маршрути:** `/welcome` → `/register` `/login` → onboarding `/onboarding/dna` → `/onboarding/avatar` → `/onboarding/modes` → таби: `/events` (головна), `/discover` (свайпи), `/matches`, `/me`; плюс `/events/new`, `/events/:id`, `/events/:id/feedback`, `/chat/:conversationId`, `/match/:id` (екран «IT'S A MATCH»).

**Стан:** Zustand-стори `auth`, `profile`, `events`, `matches`, `chat`, `ws`. API-клієнт — тонка обгортка над `fetch` з JWT; WebSocket-клієнт з авто-реконектом.

**Структура `apps/web/src`:** `app/` (router, providers), `design-system/` (tokens.css, primitives: PhantomButton, Panel, Chip, Wipe, Halftone), `avatars/` (8 SVG), `features/<домен>/` (компоненти + хуки), `stores/`, `api/`, `pages/`.

**Ключові екрани:** Welcome (чорний, заголовок з червоним wipe), Onboarding DNA (карткові питання, одне на екран), вибір аватара (карусель масок), Events (стрічка скошених карток з часом, грою, слотами), Event detail (учасники, кнопки Join/Start/Finish за роллю), Feedback («Зіграємо ще?» — три великі кнопки на кожного співучасника), Match (червоний екран), Discover (стек карток з блюр-фото, DNA-чипами, % сумісності; свайп жестом через Motion drag), Matches (список з reveal-індикатором), Chat, Profile (редагування, преміум-перемикач, вихід).

---

## 8. Seed-дані та демо-сценарій

`python -m app.seed` створює 12 ігор, 12 користувачів (`user01@teamate.dev` … пароль `demo1234`), профілі з різною DNA, 6 відкритих івентів, кілька готових метчів і повідомлень, щоб екрани не були порожні.

Демо-сценарій (2 браузерні вкладки або телефон + ноутбук): `user01` створює івент «Duo Valorant tonight» → `user02` приєднується → host Start → Finish → обидва відповідають `closer` → на обох екранах екран метчу → чат → обидва натискають Reveal → фото проявляється. Описаний у `docs/demo.md`.

---

## 9. Тестування

- **Домен (pytest, без БД):** стан-машина івенту, взаємність метчу, ліміт свайпів, reveal-стадії, віковий гейт Dating, формула сумісності.
- **API (pytest + httpx, SQLite in-memory):** реєстрація/логін, 403 для чужого чату, повний happy-path івент → метч.
- **UI (Vitest):** стор `chat` (порядок повідомлень, реконект), компонент reveal (клас блюру за стадією), парсер WS-подій.
- Мета — не «відсоток покриття», а перевірка кожного правила з розділу 5.

---

## 10. DevOps

- `docker-compose.yml`: `db` (postgres:16, volume), `api` (uvicorn, hot reload), `web` (vite dev). Одна команда `docker compose up`.
- Без Docker: `apps/api` — `python -m venv && pip install -e . && uvicorn app.main:app`, `DATABASE_URL` за замовчуванням SQLite; `apps/web` — `npm i && npm run dev`.
- `.env.example` в обох застосунках; секрети не комітяться.
- CI: `ruff` + `pytest`; `eslint` + `tsc` + `vitest`. Android-збірка в CI — поза MVP (описана в `docs/android.md`).

---

## 11. Документація (`docs/`, українською)

`architecture.md` (діаграма, потоки), `api.md` (посилання на OpenAPI + пояснення), `data-model.md`, `design-system.md`, `demo.md`, `android.md` (Capacitor), `ai-log.md` (журнал використання ШІ: промпт → прийнято/відкинуто → чому — вимога курсу), `adr/` (рішення: FastAPI vs Spring, Capacitor vs React Native, reveal-модель).

---

## 12. Ризики

| Ризик | Як зменшуємо |
|---|---|
| WebSocket у пам'яті одного процесу | Достатньо для локального демо; для масштабу — Redis pub/sub (ADR) |
| Дві вкладки з одним localStorage перемішують JWT | Ключ токена містить `sessionStorage`, не `localStorage` → кожна вкладка = свій акаунт |
| Capacitor і файлові URL | API-адреса береться з `VITE_API_URL`; для Android — IP машини в LAN |
| Обсяг MVP за семестр | Пріоритет реалізації: ядро циклу → свайпи → преміум → Game Date → полірування |
