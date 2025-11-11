# Message_AutoSend

### Django-приложение для управления рассылками: получатели, сообщения, кампании и отчёты.
#### Поддерживает серверное и клиентское кеширование (Redis), подробное логирование, а также автоматическую отправку по расписанию через django-apscheduler.

Минимальные версии: Python 3.12+, Django 5.2+, PostgreSQL 14+, Redis 6+.

Содержание

Структура проекта

Быстрый старт

Установка зависимостей

Настройка окружения и переменные

Инициализация БД

Запуск приложения

Кеширование

Логирование

Автоматическая отправка по расписанию

PowerShell/Batch скрипты

Кастомные Django-команды

Функционал приложений

clients

messages_app

mailings

users

Полезные команды

Траблшутинг

Структура проекта
Message_AutoSend/
├─ config/
│  ├─ settings.py
│  ├─ urls.py
│  ├─ wsgi.py
│  └─ asgi.py
├─ common/
│  ├─ __init__.py
│  ├─ middleware.py          # CurrentRequestMiddleware (request_id, user email)
│  ├─ mixins.py              # ClientCacheMixin (Cache-Control/Last-Modified)
│  ├─ request_storage.py     # thread-local хранение request
│  └─ logging_filters.py     # RequestContextFilter (request_id, user_email)
├─ clients/
│  ├─ models.py              # Recipient(owner, email, full_name, comment, ...)
│  ├─ views.py, urls.py, forms.py, admin.py, templates/clients/
│  └─ migrations/
├─ messages_app/
│  ├─ models.py              # Message(owner, subject, body, timestamps)
│  ├─ views.py, urls.py, forms.py, admin.py, templates/messages_app/
│  └─ migrations/
├─ mailings/
│  ├─ models.py              # Mailing(owner, message, recipients m2m, status, ...)
│  │                         # MailingLog, MailingAttempt, AttemptStatus Enum
│  ├─ services.py            # send_mailing() с логированием и аудитом
│  ├─ views.py               # списки, детали, отчёты, ручной запуск
│  ├─ urls.py, forms.py, admin.py, templates/mailings/
│  ├─ management/
│  │  └─ commands/
│  │     ├─ run_scheduler.py         # запуск APScheduler (встроенный планировщик)
│  │     ├─ send_due_mailings.py     # отправка рассылок «которые пора»
│  │     ├─ send_mailing.py          # отправка конкретной рассылки по id
│  │     ├─ seed_demo.py             # демо-данные
│  │     └─ seed_managers.py         # создание менеджерских аккаунтов/прав
│  └─ migrations/
├─ templates/
│  ├─ base.html
│  └─ ... (общие шаблоны)
├─ static/
├─ logs/
│  ├─ app/
│  │  ├─ app_info.log
│  │  ├─ app_errors.log
│  │  └─ app_sql.log
│  └─ scheduler/
│     ├─ run_YYYYMMDD.log
│     └─ jobs_YYYYMMDD.log
├─ scripts/
│  ├─ run_scheduler.ps1
│  ├─ stop_scheduler.ps1
│  ├─ tick_send_due_mailings.ps1
│  ├─ run_scheduler.bat
│  ├─ stop_scheduler.bat
│  └─ tick_send_due_mailings.bat
├─ manage.py
├─ pyproject.toml / poetry.lock (если используете Poetry)
└─ requirements.txt (если используете pip)

Быстрый старт
Установка зависимостей

Вариант A: Poetry (рекомендовано)

# из корня проекта
poetry env use 3.13
poetry install
poetry run python --version


Вариант B: venv + pip

py -3.13 -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt

Настройка окружения и переменные

Создайте .env в корне или настройте переменные окружения:

# Django
DEBUG=True
SECRET_KEY=replace-me

ALLOWED_HOSTS=localhost,127.0.0.1

# Database (PostgreSQL)
DB_NAME=message_autosend
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=127.0.0.1
DB_PORT=5432

# Email (SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=True
SMTP_USER=your_account@gmail.com
SMTP_PASSWORD=app_password
DEFAULT_FROM_EMAIL=robot@yourdomain.com
SERVER_EMAIL=errors@yourdomain.com

# Redis cache
REDIS_URL=redis://127.0.0.1:6379/1


В settings.py уже прописаны:

CACHES с django.core.cache.backends.redis.RedisCache и LOCATION из REDIS_URL

MIDDLEWARE включает common.middleware.CurrentRequestMiddleware

LOGGING настроен на файловые обработчики в logs/

Убедитесь, что Redis запущен локально (127.0.0.1:6379) и база 1 доступна.

Инициализация БД
# Активируйте окружение (Poetry или venv), затем:
python manage.py migrate
python manage.py createsuperuser


Опционально — наполнить демо-данными:

python manage.py seed_demo
python manage.py seed_managers

Запуск приложения
# Poetry
poetry run python manage.py runserver

# Либо venv
python manage.py runserver


Открывайте: http://127.0.0.1:8000

Кеширование

Серверный кеш — Redis по адресу redis://127.0.0.1:6379/1.

Включён UpdateCacheMiddleware / FetchFromCacheMiddleware (если вы их добавили) и/или точечные декораторы/классы.

В отчётах используется явное кэширование запросов и ClientCacheMixin (см. common/mixins.py), который добавляет заголовки Cache-Control и Last-Modified для корректных 304 Not Modified.

Клиентское кеширование — контролируется заголовками, которые проставляет ClientCacheMixin:

Cache-Control: private, max-age=...

Last-Modified: ... (если доступна дата последнего изменения данных)

Промахи/попадания кеша можно видеть по косвенным признакам в логах и заголовках ответов.

Логирование

Логи пишутся в logs/:

logs/app/app_info.log — информационные события

logs/app/app_errors.log — ошибки/исключения

logs/app/app_sql.log — SQL (при DEBUG/отладочном режиме)

logs/scheduler/run_*.log, logs/scheduler/jobs_*.log — работа планировщика

В лог-записях доступны:

request_id — ID запроса (ставится в CurrentRequestMiddleware)

user_email — e-mail текущего пользователя или -

Примеры логирования в коде (уже добавлено в mailings/services.py):

import logging
log = logging.getLogger("mailings")

log.info("Start sending", extra={"mailing_id": mailing.id, "total": total, "dry_run": dry_run})
log.warning("Send returned 0", extra={"recipient": email})
log.exception("SMTP failed", extra={"recipient": email})

Автоматическая отправка по расписанию

Для фона используется django-apscheduler.
Стандартная схема:

Регистрация задач (jobs) внутри команды run_scheduler

Периодическая задача: каждые N минут вызывать send_due_mailings

Логи планировщика в logs/scheduler/

PowerShell/Batch скрипты

В папке scripts/ есть подготовленные скрипты для Windows.

PowerShell

run_scheduler.ps1 — старт планировщика:

# запуск из корня проекта
.\scripts\run_scheduler.ps1


Создаст (или переиспользует) лог logs\scheduler\run_YYYYMMDD.log.

stop_scheduler.ps1 — останавливает запущенный планировщик (по PID в pid-файле):

.\scripts\stop_scheduler.ps1


tick_send_due_mailings.ps1 — однократный «тик»: принудительно запустить отложенные рассылки «которые пора»:

.\scripts\tick_send_due_mailings.ps1


Если файл лога «занят другим процессом» — значит запущен ещё один экземпляр. Остановите старый через stop_scheduler.ps1.

Batch (cmd)

run_scheduler.bat

scripts\run_scheduler.bat


stop_scheduler.bat

scripts\stop_scheduler.bat


tick_send_due_mailings.bat

scripts\tick_send_due_mailings.bat


Все скрипты предполагают активированное окружение (Poetry или venv) или сами вызывают poetry run/.\.venv\Scripts\activate && ... внутри.

Кастомные Django-команды

Команды находятся в mailings/management/commands/:

run_scheduler.py
Запускает планировщик, регистрирует job’ы (например, send_due_mailings каждые X минут).

python manage.py run_scheduler


send_due_mailings.py
Находит все рассылки, у которых наступило время отправки (start_at <= now, статус «Запущена» и т.д.), и вызывает отправку.

python manage.py send_due_mailings


send_mailing.py
Отправляет конкретную рассылку по идентификатору:

python manage.py send_mailing --id 123 [--dry-run]


seed_demo.py
Создаёт демо-данные: пользователей, получателей, сообщения, пару рассылок.

python manage.py seed_demo


seed_managers.py
Создаёт менеджерские учётки и даёт им права (например, mailings.view_all_mailings и, при необходимости, mailings.disable_mailing).

python manage.py seed_managers

Функционал приложений
clients

Recipient — получатель рассылок.

owner (FK на пользователя)

email, full_name, comment, timestamps

Список/деталь/создание/редактирование/удаление

Ограничения видимости: обычный пользователь видит только свои записи; менеджер/суперпользователь — всё (но изменять чужое нельзя, если не суперпользователь).

Шаблоны: templates/clients/...

messages_app

Message — текст письма.

owner, subject, body, timestamps

CRUD и детальная страница

Проверка прав редактирования (владелец/суперпользователь)

mailings

Mailing — кампания/рассылка.

owner, message (FK), recipients (M2M к Recipient), status, start_at, end_at, last_sent_at

Удобные вычисляемые поля и аннотации статистики: with_stats(), stats_dict()

MailingLog — построчный лог отправки по получателям.

mailing, recipient (строка email), status (SENT, ERROR, DRY_RUN), detail, triggered_by

MailingAttempt — агрегат попытки отправки (ручной/планировщик).

mailing, status (SUCCESS/FAIL), server_response, triggered_by

Отчёты и статистика:

/mailings/stats/ — общая статистика по кампаниям (видимость как у данных)

/mailings/reports/ — персональные отчёты за период (кешируются в Redis)

Ручной запуск из карточки рассылки (с dry-run для теста)

users

Кастомная модель пользователя users.User (e-mail как логин), профиль, страница профиля.

Права:

mailings.view_all_mailings — менеджер видит все рассылки/логи в списках и отчётах.

mailings.disable_mailing — может принудительно завершить рассылку.

Полезные команды
# Миграции
python manage.py makemigrations
python manage.py migrate

# Создание суперпользователя
python manage.py createsuperuser

# Демоданные / менеджеры
python manage.py seed_demo
python manage.py seed_managers

# Планировщик
python manage.py run_scheduler
python manage.py send_due_mailings
python manage.py send_mailing --id <MAILING_ID> [--dry-run]

# Проверка статуса
python manage.py showmigrations

Траблшутинг

ModuleNotFoundError: No module named 'redis'
Установите клиент: pip install redis (или poetry add redis).
Мы используем встроенный бэкенд django.core.cache.backends.redis.RedisCache (Django 5.2+).

AbstractConnection.__init__() got an unexpected keyword argument 'client_class'
Это конфликт опций старого django-redis vs нового redis-py. В проекте используется стандартный RedisCache из Django, без django-redis и без параметра CLIENT_CLASS. Убедитесь, что в CACHES нет CLIENT_CLASS. Должно быть так:

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.getenv("REDIS_URL", "redis://127.0.0.1:6379/1"),
        "OPTIONS": {
            "socket_connect_timeout": 2,
            "socket_timeout": 2,
        },
    }
}


TemplateDoesNotExist
Проверьте пути шаблонов, APP_DIRS=True, наличие файла в templates/<app>/..., а также что template_name во view совпадает.

Проблемы с миграциями owner_id
Если когда-то ветвились миграции, вылечить можно последовательным makemigrations --merge + ручная правка/упорядочивание миграций и повторный migrate. На проде — через --fake при необходимости.

Логи «заняты»
Значит уже запущен планировщик или другой процесс пишет в тот же лог. Остановите через stop_scheduler.ps1/.bat.Продолжайте писать — аудитория растёт!