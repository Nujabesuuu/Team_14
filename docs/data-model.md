# Модель даних

Усі первинні ключі — UUID, час — UTC. Схема створюється через `Base.metadata.create_all` під час старту API (для MVP; далі — Alembic).

```mermaid
erDiagram
  users ||--|| profiles : has
  profiles ||--o{ profile_games : plays
  games ||--o{ profile_games : ""
  users ||--o{ events : hosts
  games ||--o{ events : ""
  events ||--o{ event_participants : has
  users ||--o{ event_participants : joins
  events ||--o{ post_game_feedback : collects
  users ||--o{ swipes : from
  users ||--o{ matches : "user_a / user_b"
  matches ||--|| conversations : opens
  matches ||--|{ photo_reveals : "one per user"
  conversations ||--o{ messages : has
  users ||--o{ blocks : blocker

  users {
    uuid id PK
    string email UK
    string password_hash
    string display_name
    date birth_date
    bool is_premium
  }
  profiles {
    uuid user_id PK
    text bio
    enum avatar_key
    string accent_color
    string photo_url
    json modes
    enum role
    enum playstyle
    enum comms
    json schedule
    int toxicity_tolerance
  }
  games {
    uuid id PK
    string name
    string slug UK
    bool is_chill
    string cover_color
  }
  events {
    uuid id PK
    uuid host_id FK
    uuid game_id FK
    enum kind
    string title
    datetime starts_at
    int max_slots
    enum status
  }
  post_game_feedback {
    uuid event_id FK
    uuid from_user_id FK
    uuid to_user_id FK
    enum answer
  }
  swipes {
    uuid from_user_id FK
    uuid to_user_id FK
    enum direction
    datetime created_at
  }
  matches {
    uuid id PK
    uuid user_a_id FK
    uuid user_b_id FK
    enum source
  }
  photo_reveals {
    uuid match_id PK
    uuid user_id PK
    int stage
    bool consent_next
    bool early_request
  }
  messages {
    uuid id PK
    uuid conversation_id FK
    uuid sender_id FK
    text body
    datetime created_at
  }
```

## Ключові рішення

- **`matches.user_a_id < user_b_id`** (`canonical_pair`) + unique-констрейнт — пара не може мати два метчі, звідки б вони не прийшли (після гри чи взаємний лайк).
- **`photo_reveals` — по одному рядку на кожного учасника метчу.** `stage` описує, наскільки чітко *мій* профіль показаний співрозмовнику. Кожен користувач контролює тільки своє фото ([ADR-0003](adr/0003-per-user-reveal.md)).
- **`post_game_feedback` унікальний по (event, from, to)** — оцінити тіммейта можна один раз; відповідь приватна, поки не стане взаємним *closer*.
- **`profiles.modes` та `schedule` — JSON-масиви**, а не окремі таблиці: це невеликі списки enum-значень, які читаються завжди цілком.
- **`blocks` симетричний у логіці:** `blocked_ids(user)` повертає і тих, кого заблокував користувач, і тих, хто заблокував його.

## Enum-и

| Enum | Значення |
|---|---|
| `EventStatus` | `open`, `full`, `in_progress`, `finished`, `cancelled` |
| `EventKind` | `squad`, `game_date` |
| `FeedbackAnswer` | `again`, `closer`, `no` |
| `SwipeDirection` | `left`, `right` |
| `MatchSource` | `post_game`, `mutual_like` |
| `Mode` | `duo`, `friends`, `dating` |
| `Role` | `support`, `carry`, `flex`, `tank`, `igl` |
| `Playstyle` | `casual`, `competitive` |
| `Comms` | `voice`, `text`, `both` |
| `AvatarKey` | `raven`, `jester`, `kitsune`, `marionette`, `sentinel`, `vesper`, `nomad`, `oracle` |
