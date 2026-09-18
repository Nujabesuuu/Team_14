# Android через Capacitor

Клієнт написаний як mobile-first вебзастосунок, тому Android-збірка — це той самий `dist/`, загорнутий у WebView. Конфіг — `apps/web/capacitor.config.ts` (`appId: dev.teamate.app`).

## Передумови

- Android Studio з Android SDK (API 34+) і JDK 17.
- API, до якого телефон може достукатись по мережі (той самий Wi-Fi).

## Кроки

```bash
cd apps/web

# 1. Вказати адресу API (IP вашого ноутбука в локальній мережі, не localhost)
echo "VITE_API_URL=http://192.168.1.20:8000" > .env

# 2. Додати Android-проєкт (один раз; створює apps/web/android/)
npx cap add android

# 3. Зібрати веб і синхронізувати в Android
npm run cap:sync

# 4. Відкрити в Android Studio → Run на емуляторі або телефоні
npm run cap:open
```

`VITE_API_URL` використовується і для HTTP, і для WebSocket (`ws://…/api/v1/ws`). CORS на API вже дозволяє `capacitor://localhost` та `http://localhost`.

## Що врахувати

- `server.cleartext: true` у конфігу дозволяє HTTP без TLS — лише для локальної розробки.
- Папка `android/` у репозиторій не комітиться (див. `.gitignore`), бо це згенерований Gradle-проєкт. Для CI-збірки APK її треба або закомітити, або генерувати кроком `npx cap add android` у пайплайні.
- Безпечні зони (виріз/жест-бар) вже враховані через `env(safe-area-inset-*)` у `tokens.css`; в `index.html` стоїть `viewport-fit=cover`.
- Завантаження фото використовує стандартний `<input type="file">`, який у WebView відкриває системний вибір файлу/камеру.
