# Контракт: єдиний формат помилок

> **КТ4, крок 3.** Будь-яка помилка API, зокрема валідація, неіснуючий маршрут і непередбачений збій сервера, повертається в одному форматі. Рішення: [ADR-0009](../adr/0009-rest-api-error-envelope.md). Реалізація: `apps/api/app/core/errors.py`, тести: `apps/api/tests/api/test_health.py`.

## Формат

```json
{
  "code": "EVENT_FULL",
  "detail": "This event is full"
}
```

| Поле | Тип | Обов'язкове | Призначення |
|---|---|---|---|
| `code` | string, `UPPER_SNAKE_CASE` | так | Стабільний машинний код. Клієнт розгалужується **лише** за ним. Перейменування коду — зміна контракту |
| `detail` | string | так | Пояснення англійською для людини і логів. Клієнт може показати, але не розбирає |
| `fields` | `[{field, message}]` | лише для `VALIDATION_ERROR` | Які поля запиту невалідні |

Приклад валідації:

```json
{
  "code": "VALIDATION_ERROR",
  "detail": "email: Field required; password: Field required",
  "fields": [
    { "field": "email", "message": "Field required" },
    { "field": "password", "message": "Field required" }
  ]
}
```

WebSocket повертає ті самі коди в повідомленні `{ "type": "error", "code": "...", "detail": "..." }`.

## Значення HTTP-статусів

| Статус | Коли | Що робить клієнт |
|---|---|---|
| `400` | Некоректний запит на рівні протоколу | Показує загальну помилку |
| `401` | Немає токена, токен невалідний або протух, неправильний пароль | Скидає токен, веде на `/welcome` (`setUnauthorizedHandler`) |
| `402` | Функція лише для Teamate+ | Показує пропозицію Teamate+ |
| `403` | Токен є, але дія заборонена саме цій людині | Показує «недоступно» без подробиць |
| `404` | Ресурсу немає (або його існування не можна розкривати, як для фото) | Показує «не знайдено» |
| `409` | Конфлікт стану: вже зроблено, не той статус івенту | Оновлює дані з сервера |
| `422` | Порушено бізнес-правило або валідацію | Показує повідомлення біля дії або поля |
| `429` | Ліміт (денні лайки) | Показує, коли ліміт оновиться |
| `500` | Непередбачений збій (`INTERNAL_ERROR`); деталі лише в лозі сервера | Показує «щось пішло не так» |
| `503` | Недоступна залежність (`DB_UNAVAILABLE`) | Показує на `/status` |

## Каталог кодів

✅ сервер уже повертає · 🆕 додається разом з історією на КТ5.

### Загальні (будь-який ендпоінт)

| Код | Статус | Коли | |
|---|---|---|---|
| `VALIDATION_ERROR` | 422 | Тіло, параметри або шлях не відповідають схемі | ✅ |
| `UNAUTHORIZED` | 401 | Немає токена, він невалідний, або акаунта вже немає | ✅ |
| `NOT_FOUND` | 404 | Неіснуючий маршрут | ✅ |
| `METHOD_NOT_ALLOWED` | 405 | Метод не підтримується маршрутом | ✅ |
| `INTERNAL_ERROR` | 500 | Будь-який необроблений виняток | ✅ |
| `DB_UNAVAILABLE` | 503 | `GET /health/db` не зміг виконати запит до БД | ✅ |
| `ACCOUNT_BANNED` | 403 | Акаунт заблоковано модератором (US-10) | 🆕 |

### Акаунт і профіль

| Код | Статус | Історія | |
|---|---|---|---|
| `EMAIL_TAKEN` | 409 | US-01 | ✅ |
| `TOO_YOUNG` | 422 | US-01: молодше 18 (зараз поріг 13, G-01) | ✅ |
| `INVALID_CREDENTIALS` | 401 | US-01 | ✅ |
| `UNKNOWN_GAME` | 422 | US-02, US-19 | ✅ |
| `DATING_REQUIRES_18` | 422 | US-03 | ✅ |
| `UNSUPPORTED_PHOTO` | 422 | US-04: не jpeg/png/webp | ✅ |
| `PHOTO_TOO_LARGE` | 422 | US-04: більше 5 МБ | ✅ |
| `PHOTO_NOT_FOUND` | 404 | US-04, US-16: фото немає або глядачу не можна знати, що воно є | 🆕 |
| `PREMIUM_REQUIRED` | 402 | Teamate+ (Post-MVP) | ✅ |

### Івенти і гра

| Код | Статус | Історія | |
|---|---|---|---|
| `EVENT_NOT_FOUND` | 404 | US-05 | ✅ |
| `EVENT_NOT_VISIBLE` | 403 | US-06, US-08 | ✅ |
| `EVENT_FULL` | 409 | US-06 | ✅ |
| `EVENT_NOT_OPEN` | 409 | US-06 | ✅ |
| `ALREADY_JOINED` | 409 | US-06 | ✅ |
| `HOST_CANNOT_LEAVE` | 409 | US-19 | ✅ |
| `EVENT_STARTED` | 409 | US-06 | ✅ |
| `NOT_PARTICIPANT` | 409 (вихід) / 403 (фідбек, підтвердження) | US-06, US-07, US-11 | ✅ |
| `HOST_ONLY` | 403 | US-07 | ✅ |
| `INVALID_TRANSITION` | 409 | US-07 | ✅ |
| `GAME_DATE_REQUIRES_CHILL_GAME` | 422 | Game Date | ✅ |
| `GAME_DATE_REQUIRES_DATING_MODE` | 422 | Game Date | ✅ |
| `STARTS_IN_PAST` | 422 | US-19 | 🆕 |
| `EVENT_NOT_FINISHED` | 409 | US-07, US-11 | ✅ |
| `ALREADY_CONFIRMED` | 409 | US-07 | 🆕 |
| `GAME_NOT_COUNTED` | 409 | US-07, US-11: гра < 15 хв або < 2 підтверджень | 🆕 |

### «Зіграємо ще?», свайпи, метчі

| Код | Статус | Історія | |
|---|---|---|---|
| `NOT_A_TEAMMATE` | 422 | US-11 | ✅ |
| `ALREADY_RATED` | 409 | US-11 | ✅ |
| `FEEDBACK_WINDOW_CLOSED` | 409 | US-11: минуло 24 год | 🆕 |
| `CLOSER_REQUIRES_DATING` | 422 | US-11, US-12: «Побачення» вимкнено хоча б в одного | 🆕 |
| `MODE_NOT_ENABLED` | 422 | US-13 | ✅ |
| `NO_SHARED_MODE` | 422 | US-13 | ✅ |
| `CANNOT_SWIPE_SELF` | 422 | US-13 | ✅ |
| `ALREADY_SWIPED` | 409 | US-13 | ✅ |
| `SWIPE_LIMIT` | 429 | US-13: 21-й лайк за добу | ✅ |
| `USER_NOT_FOUND` | 404 | US-13, US-09 | ✅ |
| `NOTHING_TO_UNDO` | 404 | Teamate+ | ✅ |
| `MATCH_NOT_FOUND` | 404 | US-12 | ✅ |
| `NOT_YOUR_MATCH` | 403 | US-12, US-17 | ✅ |
| `NO_EARLY_REQUEST` | 409 | Teamate+ | ✅ |

### Чат, блокування, скарги

| Код | Статус | Історія | |
|---|---|---|---|
| `CONVERSATION_NOT_FOUND` | 404 | US-14 | ✅ |
| `NOT_YOUR_CONVERSATION` | 403 | US-14 | ✅ |
| `BLOCKED` | 403 | US-08, US-14 | ✅ |
| `EMPTY_MESSAGE` | 422 | US-14 | ✅ |
| `MESSAGE_TOO_LONG` | 422 | US-14: понад 2000 символів | ✅ |
| `CANNOT_BLOCK_SELF` | 422 | US-08 | ✅ |
| `CANNOT_REPORT_SELF` | 422 | US-09 | 🆕 |
| `MODERATOR_ONLY` | 403 | US-10 | 🆕 |
| `REPORT_NOT_FOUND` | 404 | US-10 | 🆕 |
| `REPORT_ALREADY_DECIDED` | 409 | US-10 | 🆕 |

### WebSocket

| Код | Коли | |
|---|---|---|
| `UNKNOWN_TYPE` | Невідомий `type` у повідомленні клієнта | ✅ |
| `BAD_CONVERSATION_ID` | `conversation_id` не UUID | ✅ |
| будь-який REST-код | Наприклад, `BLOCKED` при відправці в закритий чат | ✅ |
| close `4401` | Невалідний токен при підключенні | ✅ |

## Правила для коду

1. Сервіс кидає лише `ApiError(status, code, detail)` або хелпери з `app/core/errors.py`. Голий `HTTPException` заборонено.
2. Новий код спершу додається в цей каталог, потім у сервер, тест і клієнт.
3. Помилка, що стосується безпеки (блокування, чуже фото), не розкриває причину: `EVENT_NOT_VISIBLE`, `PHOTO_NOT_FOUND`.
4. `detail` не містить персональних даних (email, дату народження) і внутрішніх деталей (SQL, стек викликів).
