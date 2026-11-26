# Privacy Policy / Политика конфиденциальности — EMS Reporter

**Last updated / Дата обновления:** 2026-11-26

## English

**EMS Reporter** is an open-source desktop application designed to help players automate report preparation and optionally upload screenshots to their own Google Drive.

### 1. Data We Access
When you choose to sign in with Google, EMS Reporter requests only the minimal Google Drive permission:
- `https://www.googleapis.com/auth/drive.file` — access **only** to folders and files created by EMS Reporter itself. The application cannot view, modify, or delete any other files on your Google Drive.
- Basic profile email (`userinfo.email`) — used solely to display which Google account is currently signed in inside the application window.

### 2. How Data Is Stored and Used
- **Local storage only:** Your OAuth access/refresh token is stored exclusively on your local computer (encrypted via Windows DPAPI in `%LOCALAPPDATA%\EMS_Reporter`) and is never transmitted to the developer or any third-party servers.
- **No analytics or tracking:** EMS Reporter does not collect telemetry, analytics, or personal data.
- **Direct communication:** All Google Drive API requests go directly from your computer to Google servers.

### 3. Revoking Access
You can sign out inside the application at any time or revoke access in your Google Account settings: [Google Account Permissions](https://myaccount.google.com/permissions).

### 4. Contact
Repository: https://github.com/Zefous/EMS-Reporter

---

## Русский

**EMS Reporter** — десктопное приложение с открытым исходным кодом для автоматизации отчётов и (по желанию пользователя) выгрузки скриншотов на собственный Google Диск.

### 1. Какие данные запрашиваются
При входе через Google программа запрашивает только минимально необходимые права:
- `https://www.googleapis.com/auth/drive.file` — доступ **только** к тем папкам и файлам, которые создала сама программа EMS Reporter. Приложение не имеет доступа к остальным файлам на вашем Google Диске.
- Email профиля (`userinfo.email`) — используется исключительно для отображения текущего аккаунта в окне программы.

### 2. Хранение и передача данных
- **Только локальное хранение:** токен авторизации сохраняется исключительно на вашем компьютере (в зашифрованном виде через Windows DPAPI в `%LOCALAPPDATA%\EMS_Reporter`) и никогда не отправляется разработчику или третьим лицам.
- **Без телеметрии:** программа не собирает статистику, аналитику или персональные данные.
- **Прямое соединение:** все запросы к Google Drive API идут напрямую с вашего компьютера на серверы Google.

### 3. Отзыв доступа
Вы можете выйти из аккаунта в окне программы или в любой момент отозвать доступ в настройках Google-аккаунта: [Разрешения аккаунта Google](https://myaccount.google.com/permissions).

### 4. Контакты
Репозиторий проекта: https://github.com/Zefous/EMS-Reporter
