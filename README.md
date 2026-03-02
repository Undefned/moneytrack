# MoneyTrack 💰

**MoneyTrack** — это приложение для учёта личных финансов. Позволяет отслеживать доходы и расходы, анализировать траты по категориям и просматривать статистику.

## 📋 Возможности

- ✅ Регистрация и авторизация пользователей
- ✅ Управление категориями расходов/доходов
- ✅ Добавление доходов и расходов
- ✅ Фильтрация транзакций по периодам (неделя, месяц, год)
- ✅ Аналитика и статистика по категориям
- ✅ Временная шкала доходов/расходов

## 🛠 Технологии

| Компонент | Технологии |
|-----------|------------|
| **Frontend** | React, Vite, Tailwind CSS |
| **Backend** | FastAPI, Python, SQLAlchemy |
| **База данных** | PostgreSQL 15 |
| **Контейнеризация** | Docker, Docker Compose |

## 🚀 Быстрый старт

### Требования

- [Docker](https://www.docker.com/) и [Docker Compose](https://docs.docker.com/compose/)
- Или локально: Python 3.11+, Node.js 20+

### Запуск через Docker (рекомендуется)

```bash
# Клонировать репозиторий
git clone <repository-url>
cd moneytrack

# Запустить все сервисы
docker-compose up -d --build

# Проверить статус
docker-compose ps
```

**Сервисы будут доступны:**
- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend API: [http://localhost:8000](http://localhost:8000)
- Swagger документация: [http://localhost:8000/docs](http://localhost:8000/docs)
- PostgreSQL: `localhost:5433`

### Локальная разработка

#### Backend

```bash
cd backend

# Создать виртуальное окружение
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Установить зависимости
pip install -r requirements.txt

# Создать .env файл
cp .env.example .env
# Отредактировать .env (заменить SECRET_KEY)

# Запустить сервер
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend

# Установить зависимости
npm install

# Запустить dev-сервер
npm run dev
```

Frontend будет доступен на [http://localhost:5173](http://localhost:5173)

## 📁 Структура проекта

```
moneytrack/
├── backend/
│   ├── app/
│   │   ├── auth.py          # Аутентификация, JWT
│   │   ├── database.py      # Подключение к БД
│   │   ├── main.py          # FastAPI приложение
│   │   ├── models.py        # SQLAlchemy модели
│   │   ├── schemas.py       # Pydantic схемы
│   │   └── test_*.py        # Тесты
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## 🔐 Настройка безопасности

### Генерация SECRET_KEY

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Редактирование .env

Откройте `backend/.env` и установите:

```env
SECRET_KEY=ваш_секретный_ключ
DATABASE_URL=postgresql+psycopg2://postgres:postgres@db:5432/moneytrack
```

## 🧪 Тесты

```bash
cd backend

# Запустить все тесты
pytest -v

# Или через скрипт
python run_tests.bat -v      # Windows
./run_tests.sh -v            # Linux/Mac

# Запустить конкретный файл
pytest app/test_auth.py -v

# С покрытием
pytest --cov=app -v
```

## 📊 API Endpoints

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/register` | Регистрация пользователя |
| POST | `/token` | Получение JWT токена |
| GET | `/health` | Проверка статуса |
| GET | `/categories` | Список категорий |
| POST | `/categories` | Создать категорию |
| GET | `/transactions` | Список транзакций |
| POST | `/transactions` | Создать транзакцию |
| POST | `/income` | Добавить доход |
| POST | `/expense` | Добавить расход |
| GET | `/analytics` | Общая статистика |
| GET | `/analytics/categories` | Статистика по категориям |
| GET | `/analytics/timeline` | Временная шкала |

## 🐳 Docker команды

```bash
# Остановить все контейнеры
docker-compose down

# Пересобрать и запустить
docker-compose up -d --build

# Посмотреть логи
docker-compose logs -f

# Остановить и удалить volumes (данные БД)
docker-compose down -v
```

## 📝 Лицензия

MIT

---

**Разработано с ❤️ для учёта личных финансов**
