# API

Базовий шлях: `/api/v1`. Інтерактивна документація OpenAPI: **http://localhost:8000/docs** (Swagger UI) та `/redoc`.

Автентифікація — `Authorization: Bearer <JWT>` (HS256, 7 днів). Помилки — JSON `{ "code": "EVENT_FULL", "detail": "This event is full" }`; `code` стабільний і призначений для клієнта, `detail` — для людини.

## Ендпоінти

| Метод | Шлях | Що робить | Коди помилок |
|---|---|---|---|
| POST | `/auth/register` | Реєстрація → токен + акаунт; створює порожній профіль | `EMAIL_TAKEN` 409, `TOO_YOUNG` 422 |
| POST | `/auth/login` | Вхід → токен | `INVALID_CREDENTIALS` 401 |
| GET | `/me` | Акаунт + профіль (Game DNA, режими, ігри, `onboarded`) | `UNAUTHORIZED` 401 |
| PUT | `/me` | Часткове оновлення профілю | `DATING_REQUIRES_18`, `UNKNOWN_GAME` 422 |
| POST | `/me/photo` | multipart `file` (jpeg/png/webp ≤ 5 МБ) → `{photo_url}` | `UNSUPPORTED_PHOTO`, `PHOTO_TOO_LARGE` 422 |
| POST | `/me/premium` | `{enabled}` — імітація підписки Teamate+ | |
| GET | `/games` | Список ігор (`is_chill` — дозволені для Game Date) | |
| GET | `/events` | Стрічка; фільтри `game_id`, `kind`, `status`, `mine=true`. Приховує Game Date для тих, хто не в режимі dating або < 18, і івенти заблокованих | |
| POST | `/events` | Створити; `game_date` → 2 слоти, лише chill-гра, host у dating | `GAME_DATE_REQUIRES_CHILL_GAME`, `GAME_DATE_REQUIRES_DATING_MODE` 422 |
| GET | `/events/{id}` | Деталі з учасниками, `is_host`, `is_participant` | `EVENT_NOT_FOUND` 404 |
| POST | `/events/{id}/join` | Приєднатись (лише `open`) | `EVENT_FULL`, `EVENT_NOT_OPEN`, `ALREADY_JOINED` 409; `EVENT_NOT_VISIBLE`, `BLOCKED` 403 |
| POST | `/events/{id}/leave` | Вийти (до старту; host не може) | `HOST_CANNOT_LEAVE`, `EVENT_STARTED` 409 |
| POST | `/events/{id}/start` · `/finish` · `/cancel` | Переходи станів (лише host) | `HOST_ONLY` 403, `INVALID_TRANSITION` 409 |
| GET | `/events/{id}/feedback` | Кого з учасників ще не оцінено | `EVENT_NOT_FINISHED` 409, `NOT_PARTICIPANT` 403 |
| POST | `/events/{id}/feedback` | `{to_user_id, answer}` → `{match_created, match_id}` | `ALREADY_RATED` 409, `NOT_A_TEAMMATE` 422 |
| GET | `/discover?mode=` | До 20 профілів у режимі, відсортованих за сумісністю; `rights_left` | `MODE_NOT_ENABLED` 422 |
| POST | `/swipes` | `{to_user_id, direction}` → `{match_created, match_id, rights_left}` | `SWIPE_LIMIT` 429, `ALREADY_SWIPED` 409, `NO_SHARED_MODE` 422 |
| POST | `/swipes/undo` | Скасувати останній свайп (преміум) | `PREMIUM_REQUIRED` 402 |
| GET | `/likes/incoming` | Хто лайкнув мене (преміум) | `PREMIUM_REQUIRED` 402 |
| GET | `/matches` | Мої метчі з reveal-станом, сумісністю, останнім повідомленням | |
| GET | `/matches/{id}` | Один метч | `NOT_YOUR_MATCH` 403 |
| POST | `/matches/{id}/reveal/consent` | Моя згода на розкриття; якщо обидва — стадія 3 | |
| POST | `/matches/{id}/reveal/early-request` | Запит на раннє розкриття (преміум) | `PREMIUM_REQUIRED` 402 |
| POST | `/matches/{id}/reveal/early-accept` | Прийняти запит → стадія 3 для обох | `NO_EARLY_REQUEST` 409 |
| GET | `/conversations/{id}/messages?before=&limit=` | Історія (до 100, за замовчуванням 50), хронологічно | `NOT_YOUR_CONVERSATION`, `BLOCKED` 403 |
| POST | `/conversations/{id}/messages` | HTTP-фолбек для відправки | `EMPTY_MESSAGE`, `MESSAGE_TOO_LONG` 422 |
| POST | `/blocks` | `{user_id}` — заблокувати | `CANNOT_BLOCK_SELF` 422 |
| GET | `/health` | `{status: "ok"}` | |

## WebSocket `/api/v1/ws?token=<JWT>`

Одне з'єднання на користувача (клієнт може мати кілька — усі отримають події). Невалідний токен → закриття з кодом `4401`.

**Клієнт → сервер**

```json
{ "type": "message.send", "conversation_id": "…", "body": "gg" }
{ "type": "ping" }
```

**Сервер → клієнт**

| `type` | Коли | Payload |
|---|---|---|
| `message.new` | Нове повідомлення в будь-якій моїй розмові | `message` |
| `match.new` | Створено метч (після гри або взаємний лайк) | `match` (у форматі `GET /matches/{id}`) |
| `reveal.updated` | Хтось дав згоду / запит / прийняв, або стадія 2 після спільного івенту | `match` або лише `match_id` |
| `event.updated` | Будь-яка зміна івенту, у якому я учасник | `event` |
| `pong` | Відповідь на `ping` | |
| `error` | `UNKNOWN_TYPE`, `BAD_CONVERSATION_ID`, або код з REST | `code`, `detail` |
