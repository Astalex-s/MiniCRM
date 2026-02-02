# Веб-интерфейс CRM (React + Vite)

## Требования: Node.js

Если в терминале вы видите **`npm is not recognized`**:

1. **Установите Node.js** (LTS): https://nodejs.org/ — при установке отметьте опцию «Add to PATH».
2. **Закройте и заново откройте терминал** (или перезапустите Cursor/IDE), чтобы подхватился PATH.
3. Проверьте: `node -v` и `npm -v` — должны вывести версии.

Если Node уже установлен, но команда не находится — откройте терминал из меню **Node.js** в Пуске или добавьте в PATH папку установки Node (например, `C:\Program Files\nodejs\`).

## Запуск

1. **Бэкенд** (в отдельном терминале):
   ```bash
   cd D:\MyStudy\ZEROCODER\PROJECTS\EXCELIO
   uvicorn crm.main:app --reload
   ```

2. **Фронтенд**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   Откроется http://localhost:5173

Или из корня проекта одной командой (запускает только фронтенд и браузер):
```bash
python crm.py
```

## Сборка для продакшена

```bash
cd frontend
npm run build
```
Статика будет в `frontend/dist/`. Раздавать через nginx или FastAPI StaticFiles, указав API на тот же хост или отдельный URL.
