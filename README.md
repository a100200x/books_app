# Books App - REST API для управления библиотекой книг

## Описание проекта

Books App - веб-приложение  REST API для управления библиотекой книг с системой аутентификации и авторизации. Приложение предоставляет полный набор CRUD операций для управления книгами и продавцами, с защитой доступа через JWT токены.

### Основные возможности

- Управление книгами (создание, чтение, обновление, удаление)
- Регистрация и аутентификация продавцов
- Связывание книг с продавцами
- Безопасный доступ через JWT токены с временем жизни
- Автоматическая документация API через Swagger UI
- Поддержка асинхронных операций с базой данных
- Полный набор интеграционных тестов

## Технологический стек

- **Backend**: Python 3.x с FastAPI
- **База данных**: PostgreSQL 14\+
- **ORM**: SQLAlchemy 2.0 (асинхронный)
- **Аутентификация**: JWT с bcrypt для хеширования паролей
- **Контейнеризация**: Docker и Docker Compose
- **Тестирование**: pytest с pytest-asyncio
- **Валидация данных**: Pydantic 2.x
- **Документация API**: автоматическая генерация через OpenAPI 3.0

## Требования

- Python 3.10 или выше
- PostgreSQL 14 или выше
- Docker и Docker Compose (опционально, для локальной разработки)
- pip (менеджер пакетов Python)

## Установка и настройка

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd books-app
```

### 2. Создание виртуального окружения

```bash
python -m venv venv
source venv/bin/activate  # Для Linux/Mac
# или
venv\Scripts\activate     # Для Windows
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Настройка переменных окружения

Создайте файл `.env` в корне проекта на основе примера:

```bash
cp .env_example .env
```

Отредактируйте файл `.env`:

```env
# Настройки PostgreSQL
DB_USERNAME=postgres_user
DB_PASSWORD=postgres_pass
DB_HOST=127.0.0.1
DB_PORT=5445
DB_NAME=fastapi_project_db

# Настройки JWT
SECRET_KEY=SECRETKEY # change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**Важно**: В продакшн-среде измените `SECRET_KEY` на надежную случайную строку.

## Запуск приложения

### Способ 1: С использованием Docker (рекомендуется)

#### Запуск базы данных PostgreSQL

```bash
docker-compose up -d db
```

#### Запуск приложения

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Способ 2: Без Docker

#### Установка и настройка PostgreSQL

1. Установите PostgreSQL 14\+
2. Создайте базу данных:

   ```sql
   CREATE DATABASE fastapi_project_db;
   CREATE USER postgres_user WITH PASSWORD 'postgres_pass';
   GRANT ALL PRIVILEGES ON DATABASE fastapi_project_db TO postgres_user;
   ```

#### Запуск приложения

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Проверка работоспособности

После запуска приложение будет доступно по адресам:

- **API**: <http://localhost:8000>
- **Документация Swagger UI**: <http://localhost:8000/docs>
- **Документация ReDoc**: <http://localhost:8000/redoc>

## Использование API

### Аутентификация

#### Получение JWT токена

**Endpoint**: `POST /api/v1/token/`

**Формат OAuth2**:

```bash
curl -X POST "http://localhost:8000/api/v1/token/" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=yourpassword"
```

**Формат JSON**:

```bash
curl -X POST "http://localhost:8000/api/v1/token/token_json" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "yourpassword"}'
```

**Ответ**:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

#### Использование токена

Добавьте заголовок к запросам, требующим авторизации:

```
Authorization: Bearer <your_jwt_token>
```

### Управление книгами

#### Создание книги (требует авторизации)

**Endpoint**: `POST /api/v1/books/`

```bash
curl -X POST "http://localhost:8000/api/v1/books/" \
  -H "Authorization: Bearer <your_jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Clean Architecture",
    "author": "Robert Martin",
    "count_pages": 300,
    "year": 2025
  }'
```

#### Получение списка книг

**Endpoint**: `GET /api/v1/books/`

```bash
curl -X GET "http://localhost:8000/api/v1/books/"
```

#### Получение конкретной книги

**Endpoint**: `GET /api/v1/books/{book_id}`

```bash
curl -X GET "http://localhost:8000/api/v1/books/1"
```

#### Обновление книги (требует авторизации, только владелец)

**Endpoint**: `PUT /api/v1/books/{book_id}`

```bash
curl -X PUT "http://localhost:8000/api/v1/books/1" \
  -H "Authorization: Bearer <your_jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "id": 1,
    "title": "Clean Code",
    "author": "Robert Martin",
    "pages": 310,
    "year": 2022,
    "seller_id": 1
  }'
```

#### Частичное обновление книги

**Endpoint**: `PATCH /api/v1/books/{book_id}`

```bash
curl -X PATCH "http://localhost:8000/api/v1/books/1" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Title",
    "pages": 350
  }'
```

#### Удаление книги

**Endpoint**: `DELETE /api/v1/books/{book_id}`

```bash
curl -X DELETE "http://localhost:8000/api/v1/books/1"
```

### Управление продавцами

#### Регистрация продавца

**Endpoint**: `POST /api/v1/seller/`

```bash
curl -X POST "http://localhost:8000/api/v1/seller/" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "e_mail": "john.doe@example.com",
    "password": "securepassword123"
  }'
```

#### Получение списка продавцов

**Endpoint**: `GET /api/v1/seller/`

```bash
curl -X GET "http://localhost:8000/api/v1/seller/"
```

#### Получение данных продавца с книгами (требует авторизации)

**Endpoint**: `GET /api/v1/seller/{seller_id}`

```bash
curl -X GET "http://localhost:8000/api/v1/seller/1" \
  -H "Authorization: Bearer <your_jwt_token>"
```

#### Обновление данных продавца

**Endpoint**: `PUT /api/v1/seller/{seller_id}`

```bash
curl -X PUT "http://localhost:8000/api/v1/seller/1" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Smith",
    "e_mail": "john.smith@example.com"
  }'
```

#### Удаление продавца

**Endpoint**: `DELETE /api/v1/seller/{seller_id}`

```bash
curl -X DELETE "http://localhost:8000/api/v1/seller/1"
```
#### Проверка токена

Общий запрос curl для проверки токена:

   1 curl -X GET "http://localhost:8000/api/v1/some-protected-endpoint" \
   2   -H "Authorization: Bearer YOUR_TOKEN_HERE" \
   3   -H "Content-Type: application/json"


## Тестирование

### Запуск тестов

```bash
# Запуск всех тестов
pytest src/tests/

# Запуск тестов с подробным выводом
pytest src/tests/

# Запуск конкретного тестового файла
pytest src/tests/test_books.py -v

```

### Структура тестов

- `test_auth.py` - тесты аутентификации
- `test_books.py` - тесты операций с книгами
- `test_sellers.py` - тесты операций с продавцами
- `test_openapi_schema.py` - тесты схемы OpenAPI
- `conftest.py` - фикстуры для тестов

### Тестовая база данных

Тесты используют отдельную тестовую базу данных, указанную в настройках (`db_test_name`). Все изменения в тестовой БД автоматически откатываются после каждого теста.

## Структура проекта

```
books-app/
├── src/                    # Исходный код приложения
│   ├── configurations/     # Конфигурация приложения
│   │   ├── database.py    # Настройки БД и сессий
│   │   ├── security.py    # JWT и аутентификация
│   │   ├── settings.py    # Настройки из переменных окружения
│   │   └── security_test.py
│   ├── models/            # SQLAlchemy модели
│   │   ├── base.py       # Базовая модель
│   │   ├── books.py      # Модель книги
│   │   └── sellers.py    # Модель продавца
│   ├── schemas/          # Pydantic схемы для валидации
│   │   ├── books.py
│   │   ├── sellers.py
│   │   └── users.py
│   ├── services/         # Бизнес-логика
│   │   ├── books.py
│   │   └── sellers.py
│   ├── routers/          # Маршруты API
│   │   ├── v1/
│   │   │   ├── auth.py   # Аутентификация
│   │   │   ├── books.py  # Книги
│   │   │   └── sellers.py # Продавцы
│   │   └── __init__.py
│   ├── tests/           # Тесты
│   │   ├── test_auth.py
│   │   ├── test_books.py
│   │   ├── test_sellers.py
│   │   ├── test_openapi_schema.py
│   │   └── conftest.py
│   ├── main.py          # Точка входа
│   └── pytest.ini
├── docker/              # Docker конфигурация
│   └── postgres/
├── .vscode/            # Настройки VS Code
├── .env_example        # Пример переменных окружения
├── requirements.txt    # Зависимости Python
├── docker-compose.yml  # Docker Compose
├── api_tests.http     # HTTP тесты для REST Client
└── .gitignore
```

## Конфигурация

### Настройки базы данных

Настройки базы данных определяются в `src/configurations/settings.py` и загружаются из переменных окружения:

- `db_host` - хост PostgreSQL
- `db_port` - порт PostgreSQL
- `db_name` - имя базы данных
- `db_username` - имя пользователя
- `db_password` - пароль пользователя
- `db_test_name` - имя тестовой базы данных (по умолчанию: `fastapi_project_test_db`)

### Настройки безопасности

- `secret_key` - секретный ключ для подписи JWT токенов
- `algorithm` - алгоритм шифрования JWT (по умолчанию: HS256)
- `access_token_expire_minutes` - время жизни токена в минутах (по умолчанию: 30)

### Docker конфигурация

Docker Compose конфигурация включает:

- PostgreSQL 14 с предварительно настроенными пользователями
- Порт 5445, проброшенный на локальную машину
- Постоянное хранилище данных в `postgres_data/`

## Разработка

### Стиль кода

Проект следует стандартам PEP 8. Рекомендуется использовать:

```bash
# Проверка стиля кода
flake8 src/

# Форматирование кода
black src/
```

### Добавление новых функций

1. Создайте модель в `src/models/`
2. Добавьте схемы валидации в `src/schemas/`
3. Реализуйте бизнес-логику в `src/services/`
4. Добавьте маршруты в `src/routers/v1/`
5. Напишите тесты в `src/tests/`

### Миграции базы данных

Приложение использует автоматическое создание таблиц через SQLAlchemy. При изменении моделей необходимо:

1. Остановить приложение
2. Удалить старые таблицы (вручную или через миграции)
3. Перезапустить приложение для создания новых таблиц

**Внимание**: В продакшн-среде используйте систему миграций (например, Alembic).

## Устранение неполадок

### Проблемы с подключением к базе данных

1. Проверьте, запущена ли база данных:

   ```bash
   docker ps | grep postgres
   ```

2. Проверьте настройки подключения в `.env` файле

3. Проверьте доступность порта:

   ```bash
   nc -z localhost 5445
   ```

### Проблемы с аутентификацией

1. Убедитесь, что пользователь существует в базе данных
2. Проверьте правильность пароля
3. Убедитесь, что JWT токен не истек
4. Проверьте `SECRET_KEY` в настройках

### Проблемы с тестами

1. Убедитесь, что тестовая база данных доступна
2. Проверьте настройки в `src/configurations/settings.py`
3. Запустите тесты с флагом `-v` для подробного вывода


```
docker-compose up --build -d
```
```
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```
```
pytest src/tests
```