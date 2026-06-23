# Карта РК Шпаковского МО — Бэкенд

## Структура проекта

```
maprk/
├── app/
│   ├── api/            # HTTP endpoints
│   │   ├── auth.py     # Авторизация (логин)
│   │   └── rk.py       # CRUD для РК + экспорт
│   ├── models/
│   │   └── rk.py       # Модель БД
│   ├── schemas/
│   │   └── rk.py       # Валидация (Pydantic)
│   ├── services/
│   │   ├── rk_service.py      # Бизнес-логика
│   │   ├── export_service.py  # Генерация PDF/Word
│   │   └── upload_service.py  # Загрузка файлов
│   ├── utils/
│   │   └── auth.py     # JWT токены
│   ├── config.py       # Настройки
│   ├── database.py     # Подключение к БД
│   └── main.py         # Точка входа FastAPI
├── scripts/
│   └── import_existing.py  # Импорт 734 РК из JSON
├── static/uploads/     # Загруженные файлы
├── Dockerfile
├── railway.toml
├── requirements.txt
└── .env.example
```

## Быстрый старт (локально)

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 2. Настройка переменных окружения
```bash
cp .env.example .env
# Отредактируйте .env — укажите данные БД и секретный ключ
```

### 3. Запуск PostgreSQL (через Docker)
```bash
docker run -d \
  --name maprk-db \
  -e POSTGRES_DB=maprk \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  postgres:16
```

### 4. Запуск сервера
```bash
uvicorn app.main:app --reload --port 8000
```

### 5. Импорт существующих 734 РК
```bash
# Положите rk_final.json рядом со скриптом
python scripts/import_existing.py --json rk_final.json
```

Сервер запустится на http://localhost:8000
API документация: http://localhost:8000/api/docs

---

## Деплой на Railway (бесплатно)

### 1. Создайте аккаунт на railway.app

### 2. Установите Railway CLI
```bash
npm install -g @railway/cli
railway login
```

### 3. Инициализируйте проект
```bash
cd maprk
railway init
```

### 4. Добавьте PostgreSQL
В панели Railway: New → Database → PostgreSQL
Скопируйте `DATABASE_URL` из раздела Variables.

### 5. Установите переменные окружения
```bash
railway variables set SECRET_KEY=ваш-секретный-ключ
railway variables set ADMIN_USERNAME=admin
railway variables set ADMIN_PASSWORD=ваш-надёжный-пароль
railway variables set DATABASE_URL=postgresql+asyncpg://...
```

### 6. Деплой
```bash
railway up
```

Railway автоматически обнаружит `railway.toml` и запустит приложение.

### 7. Импорт данных на Railway
```bash
railway run python scripts/import_existing.py --json rk_final.json
```

---

## API Endpoints

### Публичные (без авторизации)
| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/api/rk/map` | Все РК для карты (лёгкий JSON) |
| GET | `/health` | Статус сервера |

### Для карты — GET /api/rk/map
Возвращает массив объектов:
```json
[
  {
    "id": 1, "rk_id": "Б1", "num": 1,
    "address": "г. Михайловск, ул. Батайская 11",
    "type_adv": "Наружная реклама", "type_rk": "Билборд",
    "size": "3*6*2", "area": "36",
    "lat": 45.1186961, "lon": 41.96081127,
    "note": "", "has_passport": true, "has_photo": false
  }
]
```

### Для админки (требуется Bearer токен)
| Метод | URL | Описание |
|-------|-----|----------|
| POST | `/api/auth/login` | Получить токен |
| GET | `/api/rk/` | Список РК (с фильтрами) |
| GET | `/api/rk/stats` | Статистика |
| GET | `/api/rk/{rk_id}` | Одна РК |
| POST | `/api/rk/` | Создать РК |
| PUT | `/api/rk/{pk}` | Обновить РК |
| DELETE | `/api/rk/{pk}` | Удалить РК |
| POST | `/api/rk/{pk}/photo` | Загрузить фото |
| POST | `/api/rk/{pk}/scheme` | Загрузить схему |
| GET | `/api/rk/export/pdf` | Скачать реестр PDF |
| GET | `/api/rk/export/docx` | Скачать реестр Word |
| GET | `/api/rk/{pk}/passport/pdf` | Паспорт одной РК |

### Авторизация
```bash
# Получить токен
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Использовать токен
curl http://localhost:8000/api/rk/ \
  -H "Authorization: Bearer ВАШ_ТОКЕН"
```

---

## Следующий шаг — Фронтенд

После деплоя бэкенда подключите фронтенд:
- Публичная карта использует `/api/rk/map`
- Админка использует все остальные endpoints с токеном
