# Telegram Vacancy Collector Bot

Автоматический бот для сбора вакансий из 105 Telegram каналов и отправки их пользователям.

## Функциональность

- Автоматический сбор вакансий каждый день в 21:00 МСК
- Парсинг **105 Telegram каналов** (digital, медиа, creative, фриланс)
- **AI-фильтрация через GPT-4o-mini** — точное определение релевантных вакансий
- Позиции: Сценарист, Редактор (видео), Шеф-редактор (видеопродакшн)
- Сфера: реклама, кино, документалки, продакшены
- Дедупликация вакансий (SHA-256 хеш + fuzzy matching)
- Чистый минималистичный формат сообщений
- Поддержка нескольких получателей

## Архитектура

```
Render Background Worker
├── Telethon (чтение каналов через User Account)
├── OpenAI GPT-4o-mini (AI-фильтрация вакансий)
├── python-telegram-bot (отправка уведомлений)
├── PostgreSQL (хранение вакансий)
└── APScheduler (запуск в 21:00 МСК)
```

## Формат вывода

Чистый минималистичный формат с группировкой по типу позиции:

```
📝 СЦЕНАРИСТЫ:

Сценарист рекламных роликов — BBDO
https://t.me/channel/123

Сценарист — Студия "Пилот"
https://t.me/jobs/456

🎬 РЕДАКТОРЫ:

Видеоредактор — Yellow Panda
https://t.me/work/789

Монтажёр — Кинокомпания "Среда"
https://t.me/vacancy/101

👔 ШЕФ-РЕДАКТОРЫ:

Шеф-редактор видеопродакшена — Media Production
https://t.me/hiring/202
```

- Ссылки без превью для компактности
- Группировка по категориям
- Чистые названия (AI извлекает суть из сырого текста)

## Установка и настройка

### 1. Получение Telegram API Credentials

#### API ID и API Hash (для User Bot)

1. Перейдите на https://my.telegram.org
2. Войдите с вашим номером телефона
3. Выберите "API Development Tools"
4. Создайте новое приложение:
   - App title: Vacancy Collector
   - Short name: vacancy_bot
   - Platform: Other
5. Сохраните `api_id` и `api_hash`

#### Bot Token (для отправки уведомлений)

1. Откройте [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте `/newbot`
3. Укажите имя: Vacancy Notification Bot
4. Укажите username (должен быть уникальным)
5. Сохраните полученный `BOT_TOKEN`

#### Генерация Session String (Telethon)

Локально выполните этот скрипт для генерации session string:

```python
# generate_session.py
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

API_ID = "your_api_id"
API_HASH = "your_api_hash"

with TelegramClient(StringSession(), API_ID, API_HASH) as client:
    print("Session String:")
    print(client.session.save())
```

Запустите:
```bash
pip install telethon
python generate_session.py
```

При запуске введите номер телефона и код подтверждения. Сохраните полученный session string.

### 2. Настройка получателей

**ВАЖНО:** Каждый получатель должен один раз написать боту `/start`. Это нужно сделать только ОДИН РАЗ после деплоя. После этого вакансии будут приходить автоматически каждый день.

Можно указать несколько получателей через запятую:
```
TARGET_USERNAME=mediaya,eduardtulipe
```

### 3. Локальное тестирование

```bash
# Клонировать репозиторий
git clone <your-repo-url>
cd telegram_jobs

# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # или venv\Scripts\activate на Windows

# Установить зависимости
pip install -r requirements.txt

# Создать .env файл
cat > .env << EOF
API_ID=your_api_id
API_HASH=your_api_hash
SESSION_STRING=your_session_string
BOT_TOKEN=your_bot_token
TARGET_USERNAME=your_username
DATABASE_URL=sqlite:///./telegram_jobs.db
OPENAI_API_KEY=your_openai_api_key
SCHEDULE_TIME=21:00
TIMEZONE=Europe/Moscow
LOG_LEVEL=INFO
BATCH_SIZE=10
BATCH_DELAY=30
EOF

# Запустить тестовый сбор вакансий
python main.py --test
```

## Деплой на Render

### 1. Создание GitHub репозитория

```bash
git init
git add .
git commit -m "Initial commit: Telegram vacancy collector bot"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

### 2. Создание PostgreSQL на Render

1. Перейдите на https://dashboard.render.com
2. New → PostgreSQL
3. Name: `telegram-jobs-db`
4. Plan: Free
5. Create Database
6. Сохраните `Internal Database URL`

### 3. Создание Background Worker на Render

1. New → Background Worker
2. Connect your GitHub repository
3. Name: `telegram-jobs-worker`
4. Runtime: Python 3
5. Build Command: `pip install -r requirements.txt`
6. Start Command: `python main.py`
7. Plan: Free

### 4. Настройка Environment Variables

```
API_ID=<your_api_id>
API_HASH=<your_api_hash>
SESSION_STRING=<your_session_string>
BOT_TOKEN=<your_bot_token>
TARGET_USERNAME=mediaya,eduardtulipe
DATABASE_URL=<postgres_internal_url>
OPENAI_API_KEY=<your_openai_api_key>
SCHEDULE_TIME=21:00
TIMEZONE=Europe/Moscow
LOG_LEVEL=INFO
BATCH_SIZE=10
BATCH_DELAY=30
```

### 5. Деплой

1. Нажмите "Create Background Worker"
2. Render автоматически:
   - Клонирует ваш репозиторий
   - Установит зависимости
   - Создаст таблицы в БД
   - Загрузит 105 каналов из CSV
   - Запустит бота

## Техническая информация

### AI-фильтрация вакансий (GPT-4o-mini)

Вместо regex-фильтрации используется GPT-4o-mini для точного определения релевантности.

**Что анализирует AI:**
1. Это реальная вакансия? (не спам, не реклама, не курсы)
2. Позиция: сценарист / редактор видео / шеф-редактор?
3. Сфера: видеопродакшн (реклама, кино, документалки, продакшены)?

**Подходят:**
- Сценарист для рекламы, кино, видеороликов, YouTube
- Видеоредактор, монтажёр, редактор видео
- Шеф-редактор видеопродакшена

**НЕ подходят (AI отсеивает):**
- SMM-менеджеры, контент-менеджеры, копирайтеры
- Текстовые/литературные редакторы
- Журналистика, новостные редакции
- Редакторы сайтов, контент-редакторы
- Курсы, реклама каналов, спам

**Стоимость:** ~$0.01/день (400 вакансий × 27 батчей)

**Батчинг:** 15 вакансий за один запрос к API для эффективности

### Дедупликация

- SHA-256 хеш от (название + компания + URL)
- Fuzzy matching с порогом 90%
- Временное окно: 7 дней

### Rate Limiting

- Глобальная задержка: 100ms между запросами
- Задержка на канал: 500ms
- Батчинг: 10 каналов одновременно
- Пауза между батчами: 30 секунд

### Каналы

Бот парсит **105 Telegram каналов**, включая:
- Digital и маркетинг: normrabota, marketing_jobs, vacanciesrus
- Медиа и контент: mediajobs_ru, forallmedia, Work4writers
- Фриланс: distantsiya, freelancechoice, FreeWorkFeed
- Креатив: huggabletalents, cliquejobs, workinart
- И многие другие...

## Мониторинг

### Логи в Render Dashboard

```
Step 1: Initializing clients...
Step 2: Loading channels from database... (105 channels)
Step 3: Reading messages from channels...
Step 4: Extracting vacancy data...
Step 5: Filtering vacancies with GPT AI...
  Processing GPT batch 1/27 (15 items)
  Processing GPT batch 2/27 (15 items)
  ...
  GPT filtering complete: 25 relevant vacancies
Step 6: Removing duplicates...
Step 7: Saving vacancies to database...
Step 8: Sending notifications...
Vacancy collection completed successfully
```

### Ключевые метрики

- Количество обработанных каналов (105)
- Количество прочитанных сообщений
- Количество найденных вакансий
- Количество дубликатов
- Количество отправленных вакансий

## Troubleshooting

### Бот не отправляет сообщения

**Причина:** Пользователь не написал боту `/start`

**Решение:** Отправьте `/start` боту один раз

### FloodWait ошибки

**Причина:** Превышен rate limit Telegram API

**Решение:** Бот автоматически обрабатывает FloodWait и ждёт указанное время

### Нет вакансий в ежедневной рассылке

**Причины:**
- За последние 24 часа не было подходящих вакансий
- Все найденные вакансии - дубликаты
- Фильтры слишком строгие

**Решение:** Проверьте логи для диагностики

### Session String не работает

**Причина:** Session string был создан для Pyrogram, а не Telethon

**Решение:** Сгенерируйте новый session string с помощью Telethon (см. раздел установки)

## Структура проекта

```
telegram_jobs/
├── main.py                 # Entry point
├── config/
│   ├── settings.py         # Environment variables
│   └── logging_config.py   # Logging setup
├── database/
│   ├── models.py           # SQLAlchemy models
│   └── connection.py       # DB connection
├── collectors/
│   ├── channel_reader.py   # Telethon client
│   └── rate_limiter.py     # API rate limiting
├── processors/
│   ├── vacancy_extractor.py    # Extract data from messages
│   ├── gpt_filter.py           # AI filtering with GPT-4o-mini
│   ├── vacancy_filter.py       # Legacy regex filter (backup)
│   ├── deduplicator.py         # Remove duplicates
│   └── context_analyzer.py     # Video context detection
├── notifiers/
│   └── telegram_bot.py     # Send notifications
├── scheduler/
│   └── job_scheduler.py    # APScheduler
├── utils/
│   ├── csv_loader.py       # Load channels from CSV
│   ├── hash_generator.py   # Generate vacancy hash
│   └── text_utils.py       # Text utilities
├── data/
│   └── Телеграм_каналы_для_поиска_работы.csv
├── requirements.txt
├── render.yaml
└── README.md
```

## Лицензия

MIT
