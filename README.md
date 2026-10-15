# Deribit Price Tracker

Сервис раз в минуту получает с криптобиржи [Deribit](https://docs.deribit.com/) индексные цены `btc_usd` и `eth_usd`, сохраняет их в PostgreSQL и отдаёт через REST API на FastAPI.

Презентация проекта: [docs/Deribit_Price_Tracker.pdf](docs/Deribit_Price_Tracker.pdf)

## Возможности

- Периодический сбор цен: Celery beat раз в 60 секунд запускает задачу, которая получает цены через клиент на aiohttp и сохраняет тикер, цену и время в формате UNIX timestamp.
- REST API (только GET, обязательный query-параметр `ticker`): все данные по валюте, последняя цена, цены за период.
- Миграции схемы базы данных через Alembic.
- Запуск одной командой через Docker Compose.
- Unit-тесты на pytest, которым не нужны ни интернет, ни PostgreSQL.

## Технологии

| Назначение | Инструмент |
|---|---|
| Язык | Python 3.13 |
| API | FastAPI, Uvicorn |
| База данных | PostgreSQL 16, SQLAlchemy 2.0 (синхронный), psycopg 3 |
| Миграции | Alembic |
| Периодические задачи | Celery 5.4 (worker + beat), Redis 7 как брокер |
| HTTP-клиент | aiohttp |
| Настройки | pydantic-settings |
| Тесты | pytest, aioresponses, httpx |
| Контейнеры | Docker, Docker Compose |

## Быстрый старт (Docker Compose)

Требуется Docker с Docker Compose v2.

1. Склонируйте репозиторий:

```bash
   git clone https://gitlab.com/iskander-group1/deribit-price-tracker.git
   Или git clone https://github.com/isk0nka-dot/deribit-price-tracker
   cd deribit-price-tracker
```

2. Создайте файл настроек из шаблона:

```bash
   cp .env.example .env
```

   В Windows PowerShell: `copy .env.example .env`. При желании поменяйте пароль в `POSTGRES_PASSWORD`.

3. Запустите все сервисы:

```bash
   docker compose up -d --build
```

4. Проверьте состояние:

```bash
   docker compose ps -a
```

   Контейнеры `db` и `redis` должны быть `healthy`, `api`, `worker` и `beat` в статусе `running`, а `migrate` завершается с кодом `Exited (0)`: он один раз применяет миграции и больше не нужен.

5. Откройте документацию API: <http://localhost:8000/docs> (Swagger UI).

Первая цена появится примерно через минуту после запуска, потому что beat отправляет первую задачу через 60 секунд. До этого `GET /prices/latest` вернёт 404.

Полезные команды:

```bash
docker compose logs -f worker   # логи сбора цен
docker compose logs -f beat     # логи расписания
docker compose down             # остановить, данные в базе сохранятся
docker compose down -v          # остановить и удалить данные
```

### Если Deribit недоступен из вашей сети

Если основной адрес `www.deribit.com` не отвечает (в логах worker ошибки таймаута), используйте тестовую сеть Deribit с тем же API. В файле `.env` замените адрес:

```
DERIBIT_BASE_URL=https://test.deribit.com/api/v2
```

и перезапустите worker: `docker compose up -d --force-recreate worker`.

## Настройки

Все настройки читаются из переменных окружения (в Docker Compose из файла `.env`).

| Переменная | Значение в `.env.example` | Описание |
|---|---|---|
| `POSTGRES_USER` | `deribit` | пользователь PostgreSQL |
| `POSTGRES_PASSWORD` | `change_me` | пароль PostgreSQL |
| `POSTGRES_DB` | `deribit` | имя базы данных |
| `POSTGRES_HOST` | `localhost` | адрес базы; в Docker Compose автоматически заменяется на `db` |
| `POSTGRES_PORT` | `5432` | порт базы |
| `REDIS_URL` | `redis://localhost:6379/0` | брокер Celery; в Docker Compose заменяется на `redis://redis:6379/0` |
| `DERIBIT_BASE_URL` | `https://www.deribit.com/api/v2` | адрес API биржи |

Файл `.env` не попадает ни в репозиторий, ни в Docker-образ.

## API

Все методы: `GET`, параметр `ticker` обязателен. Допустимые значения: `btc_usd`, `eth_usd`.

| Метод | Описание | Параметры |
|---|---|---|
| `GET /prices` | все сохранённые данные по валюте, по возрастанию времени | `ticker` |
| `GET /prices/latest` | последняя сохранённая цена валюты | `ticker` |
| `GET /prices/by-date` | цены валюты за период | `ticker`, `date_from`, `date_to` |

`date_from` и `date_to` необязательны, это UNIX timestamp в секундах, границы включаются. Можно указать только одну границу или ни одной (тогда вернутся все записи).

Примеры:

```bash
curl "http://localhost:8000/prices?ticker=btc_usd"
curl "http://localhost:8000/prices/latest?ticker=eth_usd"
curl "http://localhost:8000/prices/by-date?ticker=btc_usd&date_from=1792000000&date_to=1792050000"
```

В Windows PowerShell используйте `curl.exe` вместо `curl`.

Пример ответа `/prices/latest`:

```json
{"ticker": "btc_usd", "price": 81075.4, "timestamp": 1792049243}
```

Остальные методы возвращают список таких объектов.

Коды ответов:

| Код | Когда |
|---|---|
| 200 | успех |
| 404 | `/prices/latest`: по этой валюте ещё нет данных |
| 422 | `ticker` не указан или не из списка допустимых; отрицательный timestamp; `date_from` позже `date_to` |

## Запуск без Docker для приложения

База и Redis при этом всё равно поднимаются через Docker Compose.

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1          # Linux/macOS: source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env                # PowerShell: copy .env.example .env

docker compose up -d db redis
alembic upgrade head
```

Затем в трёх отдельных терминалах с активированным окружением:

```bash
uvicorn app.main:create_app --factory --reload
celery -A app.tasks.worker:celery_app worker --loglevel=info    # на Windows добавьте --pool=solo
celery -A app.tasks.worker:celery_app beat --loglevel=info
```

## Тесты

```bash
pip install -r requirements-dev.txt
pytest -v
```

Тесты не требуют интернета и PostgreSQL:

- клиент Deribit проверяется с подменёнными HTTP-ответами (aioresponses): успех, ошибки HTTP, обрыв соединения, таймаут, неожиданный формат ответа;
- сервис сбора цен проверяется с фейковым клиентом и фейковым репозиторием, время подставляется через параметр `clock`;
- репозиторий, сервис запросов и все три эндпоинта проверяются на временной базе SQLite.

## Структура проекта

```
app/
├── api/
│   ├── routers.py          # эндпоинты
│   ├── schemas.py          # схема ответа
│   └── dependencies.py     # создание сессии и сервисов для запроса
├── clients/deribit.py      # DeribitClient (aiohttp)
├── db/
│   ├── models.py           # модель Price
│   └── session.py          # класс Database
├── repositories/
│   └── price_repository.py # все запросы к БД
├── services/
│   ├── price_service.py        # сбор и сохранение цен
│   └── price_query_service.py  # логика чтения для API
├── tasks/
│   ├── fetch_prices.py     # PriceFetcher и регистрация Celery-задачи
│   ├── celery_app.py       # фабрика Celery-приложения и расписание
│   └── worker.py           # точка входа Celery
├── config.py               # настройки
├── tickers.py              # перечисление поддерживаемых валют
└── main.py                 # фабрика FastAPI-приложения
migrations/                 # миграции Alembic
tests/                      # unit-тесты
Dockerfile
docker-compose.yaml
```

## Как это работает

```
Celery beat ──каждые 60 с──► Redis ──► Celery worker
                                          │
                  PriceFetcher ──► PriceCollectionService ──► DeribitClient ──► Deribit API
                                          │
                                          ▼
                                    PriceRepository ──► PostgreSQL
                                                              ▲
Клиент ──► FastAPI ──► PriceQueryService ──► PriceRepository ─┘
```

## Design decisions

**Слои и ответственность.** Код разделён на роутеры (знают про HTTP), сервисы (предметные правила), репозиторий (весь SQL) и клиент биржи (только запрос цены). Верхний слой зависит от нижнего, но не наоборот. Клиент Deribit ничего не знает про базу и время, а репозиторий ничего не знает про HTTP, поэтому каждый слой тестируется отдельно.

**Нет глобальных переменных и скрытых зависимостей.** Все зависимости передаются через конструкторы (`DeribitClient(base_url, session)`, `PriceCollectionService(client, repository, tickers, clock)`). `Settings` и `Database` создаются только в точках входа: `create_app()` для FastAPI и `worker.py` для Celery. На уровне модулей остаются только объекты, которые фреймворки находят по имени: `celery_app` в `worker.py` (Celery ищет приложение по имени модуля) и `router` в `routers.py` (реестр маршрутов FastAPI). Остальное на уровне модулей это неизменяемые константы. Фабрика `create_app()` принимает готовый `Database`, что позволяет подставлять тестовую базу без хаков.

**Синхронная работа с БД, асинхронный клиент.** Celery-задачи синхронные, поэтому SQLAlchemy и драйвер psycopg используются в синхронном режиме, а эндпоинты FastAPI объявлены как обычные `def` (FastAPI выполняет их в пуле потоков). Клиент написан на aiohttp, как в необязательном требовании: задача запускает его через `asyncio.run`, а обе цены запрашиваются параллельно (`asyncio.gather`). HTTP-сессия создаётся на один цикл сбора и закрывается, при частоте раз в минуту это дёшево и ничего не остаётся висеть между запусками.

**Хранение данных.** Цена хранится как `NUMERIC(18, 8)`, а не `float`, чтобы не терять точность. Время хранится как `BIGINT` с UNIX timestamp, как требует задание. Составной индекс по `(ticker, timestamp)` ускоряет все три запроса API: фильтр по тикеру и сортировка или диапазон по времени. В JSON-ответе цена отдаётся числом, потому что так удобнее клиентам. Это осознанный компромисс: для точных вычислений на стороне клиента лучше было бы отдавать строку.

**Время записи.** Timestamp фиксируется сервисом после получения ответов биржи и одинаков для обеих валют одного цикла. Это время получения данных нашим сервисом, а не время, которое сообщает биржа.

**Целостность цикла сбора.** Обе цены сохраняются в одной транзакции. Если запрос по любой из валют не удался, не сохраняется ничего, и в этом цикле нет данных ни по одной валюте. Так в базе не появляются «половинные» циклы с цифрой по BTC и без цифры по ETH.

**Celery.** Расписание задано через Celery beat (интервал 60 секунд), а не через cron или цикл с `sleep`: частота настраивается в одном месте, worker и beat запускаются и масштабируются отдельно. Повторные попытки (retry) намеренно не добавлены: при сбое следующая попытка и так произойдёт через минуту, а ретраи могли бы создать дубли и сдвинуть метки времени. Результаты задач не хранятся (нужны только данные в PostgreSQL), поэтому отдельный result backend не нужен. Брокером выбран Redis как самый простой вариант.

**API.** Тикер описан перечислением (`Ticker`), поэтому валидация обязательного параметра и список допустимых значений в Swagger получаются автоматически, а список валют определён в одном месте для API и Celery. Даты принимаются как UNIX timestamp: это тот же формат, что в базе, без конвертаций и проблем с часовыми поясами. Нет данных у `/prices/latest` даёт 404, перевёрнутый период даёт 422 с понятным сообщением.

**Docker.** Один образ приложения используется всеми процессами (`api`, `worker`, `beat`, `migrate`), у каждого своя команда запуска. Контейнеров получилось больше двух из задания, потому что Celery требует брокера (Redis), а worker и beat по назначению отдельные процессы. Миграции вынесены в отдельный одноразовый сервис, остальные ждут его успешного завершения (`service_completed_successfully`), поэтому нет гонки при параллельном старте. Готовность базы и Redis проверяется healthcheck-ами, а не паузами. Процессы работают не от root, файл `.env` не попадает в образ. Порты PostgreSQL и Redis опубликованы только на `127.0.0.1`. Адрес и порт базы и адрес Redis в Compose переопределяются в `environment`, поэтому один и тот же `.env` подходит и для Docker, и для локального запуска.

**Настраиваемый адрес биржи.** `DERIBIT_BASE_URL` вынесен в настройки: по умолчанию боевой API, но при проблемах с доступом можно переключиться на тестовую сеть Deribit без изменения кода.

**Тесты.** Тесты не зависят от сети и внешних сервисов, поэтому быстрые и воспроизводимые. Бизнес-логика проверяется с фейками, которые подставляются через конструктор (включая функцию `clock`), без monkeypatch. Асинхронный код запускается через `asyncio.run`, без дополнительных плагинов. Тестовые зависимости вынесены в `requirements-dev.txt` и не попадают в образ приложения. Ограничение: тесты запросов идут на SQLite, а она ведёт себя не так, как PostgreSQL (например, хранит `Decimal` как число с плавающей точкой). Для логики запросов этого достаточно, но полную проверку на PostgreSQL дают запуск через Docker Compose и ручные запросы к API.

## Ограничения и что можно улучшить

- `GET /prices` возвращает все записи без пагинации, как этого требует задание. Данные накапливаются (две записи в минуту), поэтому для продакшена нужны `limit`/`offset` или курсор и политика хранения старых данных.
- Нет повторных попыток запроса к бирже, метрик, алертов и настройки формата логов.
- Нет аутентификации и ограничения частоты запросов к API.
- У контейнера `api` нет healthcheck.
- Нет CI-пайплайна (запуск тестов при каждом коммите).
