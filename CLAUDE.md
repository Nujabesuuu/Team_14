# CLAUDE.md — правила для ШІ-асистента в репозиторії Teamate

Цей файл читає ШІ-асистент (Claude Code, Cursor, Copilot) перед будь-якою роботою в репозиторії. Людям він теж корисний як коротка шпаргалка.

## Проєкт

**Teamate** — мобільний застосунок для знайомств між геймерами 18+. Знайомство через спільну гру, а не фото:
івент → спільна гра → таємне «Зіграємо ще?» → метч → чат → поступове розкриття фото за згодою обох.

Команда з 4 людей, навчальний проєкт, нульовий бюджет, запуск локально. MVP — 19 історій у [docs/requirements.md](docs/requirements.md).

## Стек

| Шар | Технології | Папка |
|---|---|---|
| UI | React 19, TypeScript (strict), Vite, React Router 7, Zustand, framer-motion; Android через Capacitor | `apps/web` |
| API | Python 3.12+, FastAPI, Pydantic 2, WebSocket | `apps/api` |
| Дані | SQLAlchemy 2 async; SQLite локально, PostgreSQL 16 у Docker | `apps/api/app/models` |
| Тести | pytest + httpx (API), Vitest + Testing Library (web) | `apps/*/tests`, `apps/web/src/test` |

## Команди

```bash
python dev.py                       # усе разом: залежності, seed, API :8000 + web :5173
docker compose up --build           # альтернатива з PostgreSQL

# API (з apps/api; на Windows .venv/Scripts/ замість .venv/bin/)
.venv/bin/uvicorn app.main:app --reload --port 8000
.venv/bin/python -m app.seed                          # демо-дані, ідемпотентно
.venv/bin/ruff check app tests && .venv/bin/ruff format --check app tests
.venv/bin/pytest -q

# Web (з apps/web)
npm run dev
npm run typecheck && npm run lint && npm test && npm run build
```

Перевірка каркаса: `GET http://localhost:8000/api/v1/health`, `GET http://localhost:8000/api/v1/health/db`, сторінка http://localhost:5173/status.

## Де що лежить

```
apps/api/app/
  domain/      чисті правила без I/O: машина станів івенту, метч, стадії фото, сумісність
  services/    транзакції, перевірка прав, виклик domain, розсилка WS-подій
  routers/     тонкі HTTP-обгортки: схема Pydantic → сервіс → схема відповіді
  schemas/     Pydantic-моделі запитів і відповідей
  models/      SQLAlchemy-таблиці
  core/        config, db, security (JWT), errors (ApiError і обробники)
  ws/hub.py    WebSocket-хаб у пам'яті
apps/web/src/
  pages/       екрани (один файл — один маршрут з app/App.tsx)
  features/    складові екранів за фічами
  design-system/  Phantom UI: токени і примітиви (PhantomButton, Panel, Chip, TopBar…)
  stores/      Zustand: auth, events, matches, chat
  api/         client.ts (fetch + JWT), types.ts, ws.ts
docs/
  requirements.md         історії MVP і критерії приймання (Given-When-Then)
  technical-analysis.md   сутності, стани, бізнес-правила BR-xx, заборони NEVER-xx
  contracts/              data-schema.md, api.md, errors.md, openapi.json
  adr/                    архітектурні рішення
prompts/                  промпти кожної контрольної точки
```

## Як працювати з задачею

1. Знайди історію (`US-xx`) у [docs/requirements.md](docs/requirements.md) і її сценарії Given-When-Then.
2. Знайди правила `BR-xx` і заборони `NEVER-xx` для цієї історії в [docs/technical-analysis.md](docs/technical-analysis.md#7-відповідність-історій-і-сутностей).
3. Звір поля й ендпоінти з [docs/contracts/](docs/contracts/). Якщо контракт треба змінити, спершу зміни документ і скажи про це, потім код.
4. Правило продукту → чиста функція в `app/domain/` + юніт-тест у `tests/domain/`. Доступ до БД і права → `app/services/` + API-тест у `tests/api/`.
5. Клієнт: тип у `src/api/types.ts` за контрактом, виклик через `api` з `src/api/client.ts`, стан у відповідному сторі.
6. Запусти всі перевірки з розділу «Команди» для обох застосунків. Візуальні зміни перевір у браузері.

## Правила кодогенерації

- **Пиши як сусідній код:** ті самі імена, рівень коментарів, структура файлів. Коментар пояснює «чому», а не «що».
- **Помилки — лише `ApiError(status, code, detail)`** з `app/core/errors.py`. Новий `code` спершу додай у [docs/contracts/errors.md](docs/contracts/errors.md). Клієнт розгалужується за `code`, а не за текстом.
- **Async SQLAlchemy:** кожен зв'язок, який читається в обробнику, має `lazy="selectin"`, інакше `MissingGreenlet`.
- **Публічні дані про людину — лише через `PublicUser`.** Ніколи не віддавай email, `birth_date`, `password_hash`.
- **Час — UTC** (`utcnow()` з `models/_base.py`), ідентифікатори — UUID.
- **WS-події** розсилай через `hub.send_to_user(s)` після `commit`, у форматі з [contracts/api.md](docs/contracts/api.md#websocket-apiv1wstokenjwt).
- **UI:** лише примітиви з `design-system/` і CSS-змінні з `tokens.css`; без вкладених `<button>`; поважай `prefers-reduced-motion`. Тексти інтерфейсу англійською.
- **Тести:** на кожне бізнес-правило — тест із граничним значенням (17 років 364 дні / 18 років; 14:59 / 15:00 хв; 24 год 0 хв).
- **Коміти:** Conventional Commits, як в історії репозиторію: `feat(api): …`, `fix(web): …`, `docs(cp4): …`, `test: …`.

## Заборони

- **Не вигадуй поля, таблиці, ендпоінти чи коди помилок.** Усе має бути в [docs/contracts/](docs/contracts/). Немає в контракті — спитай або запропонуй зміну контракту.
- **Не змінюй бізнес-правила «заодно».** Розбіжності з вимогами вже описані в [technical-analysis.md, розділ 6](docs/technical-analysis.md#6-знайдені-прогалини) і виправляються окремою задачею під конкретну історію.
- **Не послаблюй правила безпеки** (NEVER-01…NEVER-10): вік 18+, приховане фото, таємність односторонніх відповідей, блокування в обидва боки.
- **Не віддавай оригінал фото і `photo_url` незнайомцям** і не покладайся на CSS-розмиття як на захист ([ADR-0010](docs/adr/0010-private-photo-storage.md)).
- **Не додавай залежності й інфраструктуру** (Redis, Celery, S3, платні сервіси) без нового ADR. Бюджет нульовий, запуск має лишатися однією командою.
- **Не перевіряй правила лише на клієнті.** Сервер — єдине джерело правди.
- **Не використовуй голий `HTTPException`, `print`, `dangerouslySetInnerHTML`.**
- **Не коміть** `.env`, `teamate.db`, `media/`, `node_modules/`, `.venv/`, папку `android/` і реальні дані людей. У промпти — лише seed-дані.
- **Не вимикай і не пропускай тести**, щоб «зелений» CI. Падає тест — розбирайся з причиною.
- **Не пиши код, який не можеш пояснити на рев'ю.**

## Definition of Done

- [ ] Сценарії Given-When-Then історії проходять (автотест або ручна перевірка в браузері).
- [ ] `ruff check`, `ruff format --check`, `pytest`, `typecheck`, `lint`, `vitest`, `build` — без помилок.
- [ ] Контракти в `docs/contracts/` відповідають коду; `openapi.json` оновлено, якщо змінились ендпоінти.
- [ ] Значуще використання ШІ записано в [docs/ai-log.md](docs/ai-log.md).
