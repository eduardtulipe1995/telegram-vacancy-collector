# Инструкция по локальному запуску

## 1. Установка зависимостей

```bash
cd /Users/eduardepstejn/claude_code/telegram_jobs

# Создать виртуальное окружение (рекомендуется)
python3 -m venv venv
source venv/bin/activate

# Установить зависимости
pip install -r requirements.txt
```

## 2. Генерация SESSION_STRING

**ВАЖНО:** Перед запуском бота необходимо сгенерировать SESSION_STRING.

```bash
python generate_session.py
```

Скрипт попросит:
1. Ваш номер телефона в формате `+79123456789`
2. Код подтверждения из Telegram
3. Возможно, двухфакторную аутентификацию (если включена)

После успешной авторизации скрипт выведет SESSION_STRING - скопируйте его.

## 3. Обновление .env файла

Откройте файл `.env` и замените строку:
```
SESSION_STRING=PLACEHOLDER_RUN_GENERATE_SESSION_PY
```

На полученный SESSION_STRING:
```
SESSION_STRING=ваш_длинный_session_string_здесь
```

## 4. Запуск бота

### Тестовый запуск (сразу собирает вакансии и завершается)
```bash
python main.py --test
```

### Обычный запуск (запускает scheduler, работает постоянно)
```bash
python main.py
```

## 5. Первое использование

**ВАЖНО:** После запуска бота, откройте Telegram и:
1. Найдите вашего бота по username (тот, что вы создали через @BotFather)
2. Отправьте команду `/start` от аккаунта @mediaya
3. Бот сохранит chat_id и начнет отправлять вакансии

## Проверка работы

После тестового запуска проверьте:
- ✅ Бот успешно подключился к Telegram
- ✅ База данных создана (файл `telegram_jobs.db`)
- ✅ Каналы загружены из CSV
- ✅ Сбор вакансий выполнен
- ✅ Найдены и отфильтрованы вакансии

## Деплой на Render

После успешного локального тестирования:

1. Закоммитьте изменения (НЕ коммитьте .env файл!)
2. Создайте PostgreSQL базу на Render
3. Создайте Background Worker на Render
4. Добавьте все переменные окружения из .env в настройки Worker
5. Замените `DATABASE_URL` на PostgreSQL URL из Render

## Troubleshooting

### Ошибка "SESSION_STRING is invalid"
- Перегенерируйте SESSION_STRING через `python generate_session.py`
- Убедитесь что используете тот же API_ID и API_HASH

### Ошибка "Could not connect to Telegram"
- Проверьте API_ID и API_HASH
- Проверьте интернет соединение

### Вакансии не приходят
- Убедитесь что @mediaya отправил `/start` боту
- Проверьте логи бота
