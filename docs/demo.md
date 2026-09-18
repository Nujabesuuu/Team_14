# Сценарій демо

Показує повний цикл продукту за ~3 хвилини на двох пристроях (або двох вкладках браузера — токен зберігається в `sessionStorage`, тому вкладки не «бачать» одна одну).

## Підготовка

```bash
cd apps/api && .venv/bin/python -m app.seed   # 12 користувачів, 12 ігор, 8 івентів
```

Акаунти: `user01@teamate.dev` … `user12@teamate.dev`, пароль `demo1234`. `user02` (Danylo) — преміум.

| Вкладка | Хто | Роль у демо |
|---|---|---|
| A | `user01` Nika (kitsune) | Host івенту |
| B | `user02` Danylo (raven, Teamate+) | Гість |

## Кроки

1. **A → Events.** Показати стрічку скошених карток; відкрити «Duo to Diamond tonight» (host — Nika). Пояснити слоти 1/2.
2. **B → Events → та сама картка → Join squad.** На екрані A кількість учасників оновлюється миттєво (WebSocket `event.updated`), статус стає `FULL`.
3. **A → Start the game → We're done — finish.** A автоматично потрапляє на «Play again?». На екрані B кнопка Leave змінилась на «Play again?» без перезавантаження.
4. **A → Get closer.** Відповідь приватна: B нічого не бачить. Екран A: «All rated».
5. **B → Play again? → Get closer.** Обидва екрани одночасно перемикаються на червоний **IT'S A MATCH** (A — через `match.new`).
6. **B → Say something → написати повідомлення.** З'являється на A миттєво. Показати бульбашки-паралелограми, маску співрозмовника, `41% DNA`.
7. **A → тап по аватару в шапці чату → Reveal photos.** На B з'являється «Nika wants to reveal. Your call.» і (бо B преміум) «Ask to reveal now».
8. **B → Reveal photos.** Обидва бачать `REVEAL 3/3 · REVEALED`. Якщо у профілів є фото — блюр анімовано зникає.

## Додаткові гілки (якщо є час)

- **Discover:** перетягнути картку вправо/вліво, показати стемпи `LIKE`/`NOPE`, лічильник «N likes left today». Взаємний лайк теж дає метч (`source: mutual_like`).
- **Game Date:** у B (dating увімкнено) → Host → тип «Game date» → список звужується до chill-ігор, слотів завжди 2. Користувач без режиму dating цей івент не бачить.
- **Teamate+:** Me → Activate (demo) → у Discover з'являється Undo, у Matches → Likes — хто лайкнув.
- **Безпека:** Block у чаті → людина зникає зі стрічки, Discover і чату.

## Що сказати про ШІ

Див. [ai-log.md](ai-log.md): що згенеровано, що відкинуто, які дефекти знайдено вручну (нестабільна анімація в `AnimatePresence`, вкладені `<button>`, шлях до SQLite залежно від cwd).
