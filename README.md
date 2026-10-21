# Sky Habit — трекер привычек

---

**Habit tracker backend on Django REST Framework with JWT.**  

Backend-сервис представляет собой Django REST Framework и включает JWT-аутентификацию, работу с привычками, Telegram-уведомления и фоновые задачи Celery. Архитектура включает три основных приложения: habits для управления привычками и местами их выполнения, users для регистрации и аутентификации пользователей, и telegram_bot для отправки напоминаний через Telegram. Используется PostgreSQL для основной базы данных, Redis для кеширования и асинхронных задач через Celery, а также реализована система пагинации и ограничения доступа к ресурсам. Приложение настроено на работу с CORS и включает валидацию бизнес-логики на уровне моделей и сериализаторов. Также реализованы тесты, хотя часть из них завершается с ошибками.

## Стек

- Python 3.13
- Django и Django REST Framework
- PostgreSQL
- Redis
- Celery и Celery Beat
- Docker и Docker Compose
- Nginx и Gunicorn
- Poetry
- GitHub Actions: CI/CD

## Возможности

- Регистрация и аутентификация пользователей через JWT
- CRUD для привычек
- Публичные и приватные привычки
- Приятные привычки, связанные привычки и вознаграждения
- Валидация правил создания привычек
- Периодические уведомления через Celery Beat
- Уведомления в Telegram
- Swagger/OpenAPI-документация API
- Автоматические тесты, линтеры и типизация
- Автоматический деплой на удалённую VM после успешного CI

## Локальный запуск

### 1. Клонируйте репозиторий

```bash
git clone <URL_ВАШЕГО_РЕПОЗИТОРИЯ>
cd sky_habit
```

### 2. Установите зависимости

```bash
poetry install
```

### 3. Создайте `.env`

Скопируйте шаблон:

```bash
cp .env.example .env
```

Пример минимальной локальной конфигурации:

```env
DEBUG=True
SECRET_KEY=local-secret-key

ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=

DB_NAME=sky_habit
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5433

DB_HOST_PORT=5433
REDIS_HOST_PORT=6380

CELERY_BROKER_URL=redis://localhost:6380/0
CELERY_RESULT_BACKEND=redis://localhost:6380/0

TELEGRAM_BOT_TOKEN=
```

Файл `.env` не должен попадать в Git.

### 4. Запустите приложение в Docker

```bash
docker compose up -d --build
```

Проверьте статус контейнеров:

```bash
docker compose ps
```

Остановить контейнеры:

```bash
docker compose down
```

Остановить контейнеры вместе с volumes базы данных:

```bash
docker compose down -v
```

> Команда с `-v` удаляет данные PostgreSQL. Используйте её только если данные больше не нужны.

## Сервисы Docker

| Сервис | Назначение | Внешний порт |
|---|---|---:|
| `web` | Nginx, внешний HTTP-вход | 80 |
| `backend` | Django + Gunicorn | 8000 только на localhost VM |
| `db` | PostgreSQL | 5433 только на localhost |
| `redis` | Брокер Celery и backend результатов | 6380 только на localhost |
| `celery` | Выполнение фоновых задач | — |
| `celery-beat` | Планирование периодических задач | — |

## Полезные команды

### Миграции

```bash
docker compose exec backend python manage.py makemigrations
docker compose exec backend python manage.py migrate
```

### Создание суперпользователя

```bash
docker compose exec backend python manage.py createsuperuser
```

### Логи контейнеров

```bash
docker compose logs -f backend
docker compose logs -f celery
docker compose logs -f celery-beat
docker compose logs -f web
```

### Проверка Django

```bash
docker compose exec backend python manage.py check
```

### Тесты и качество кода

```bash
poetry run pytest
poetry run flake8 .
poetry run black --check .
poetry run isort --check-only .
poetry run mypy .
```

## API

После запуска API доступен по адресу:

```text
http://localhost/
```

Административная панель:

```text
http://localhost/admin/
```

Swagger/OpenAPI-документация доступна по маршруту, настроенному в `config/urls.py`.

## Переменные окружения

| Переменная | Назначение |
|---|---|
| `DEBUG` | Режим Django: `True` локально, `False` в production |
| `SECRET_KEY` | Секретный ключ Django |
| `ALLOWED_HOSTS` | Список разрешённых хостов через запятую |
| `CSRF_TRUSTED_ORIGINS` | Доверенные origins для CSRF через запятую |
| `DB_NAME` | Имя базы PostgreSQL |
| `DB_USER` | Пользователь PostgreSQL |
| `DB_PASSWORD` | Пароль PostgreSQL |
| `DB_HOST` | Хост базы: `db` в Docker Compose |
| `DB_PORT` | Порт PostgreSQL внутри сети Docker: `5432` |
| `CELERY_BROKER_URL` | URL Redis для Celery |
| `CELERY_RESULT_BACKEND` | URL Redis для результатов Celery |
| `TELEGRAM_BOT_TOKEN` | Токен Telegram-бота |
| `DB_HOST_PORT` | Порт PostgreSQL на хосте для локальной разработки |
| `REDIS_HOST_PORT` | Порт Redis на хосте для локальной разработки |

## CI

Workflow находится в:

```text
.github/workflows/ci.yaml
```

При `push` и `pull_request` запускаются:

- Django system check
- Pytest
- Flake8
- Black
- isort
- mypy
- Docker Compose build

Для CI используются отдельные тестовые PostgreSQL и Redis, поэтому production-секреты для тестов не требуются.

## CD: автоматический деплой

Деплой запускается после успешного CI при push в ветку:

```text
feature/homework_35_3
```

GitHub Actions выполняет:

1. Подключение к VM по SSH.
2. Обновление кода через `git pull --ff-only`.
3. Создание защищённого `.env` на VM.
4. Сборку и запуск контейнеров:

```bash
docker compose up -d --build --remove-orphans
```

5. Применение миграций и сбор статики при старте backend-контейнера.

### GitHub Secrets

В GitHub необходимо создать следующие Repository Secrets:

| Secret | Назначение |
|---|---|
| `SERVER_HOST` | Публичный IP-адрес VM |
| `SERVER_PORT` | SSH-порт, обычно `22` |
| `SERVER_USER` | Пользователь VM |
| `SERVER_SSH_KEY` | Приватный deploy SSH-ключ без passphrase |
| `SECRET_KEY` | Production Django secret key |
| `DB_PASSWORD` | Production пароль PostgreSQL |
| `TELEGRAM_BOT_TOKEN` | Токен Telegram-бота |

Не добавляйте в Git:

- `.env`
- приватные SSH-ключи
- пароли PostgreSQL
- `SECRET_KEY`
- токены Telegram
- файлы `celerybeat-schedule-*`

### Подготовка VM

На VM должны быть установлены:

```bash
git
docker
docker compose
```

На VM должен существовать каталог проекта:

```text
~/apps/sky_habit
```

Public key, соответствующий `SERVER_SSH_KEY`, должен быть добавлен в:

```text
~/.ssh/authorized_keys
```

Пример проверки подключения:

```bash
ssh -o IdentitiesOnly=yes \
  -i ~/.ssh/sky_habit_github_deploy \
  -p 22 \
  admin_399745146@<SERVER_HOST> \
  'whoami && hostname'
```

## Production-проверка

После деплоя на VM:

```bash
cd ~/apps/sky_habit
docker compose ps
docker compose logs --tail=100 backend
```

Проверьте, что работают сервисы:

```text
db
redis
backend
web
celery
celery-beat
```

Проверьте приложение в браузере:

```text
http://<SERVER_HOST>/
http://<SERVER_HOST>/admin/
```

## Важное о публичном IP

Если VM использует динамический IP, он может измениться после остановки и повторного запуска VM. В таком случае нужно:

1. Обновить GitHub Secret `SERVER_HOST`.
2. Запустить новый deploy.
3. Проверить, что новый IP передан в `ALLOWED_HOSTS` и `CSRF_TRUSTED_ORIGINS`.

Для постоянного production-адреса рекомендуется использовать статический публичный IP.