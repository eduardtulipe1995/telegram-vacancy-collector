#!/usr/bin/env python3
"""
Telegram Vacancy Collector Bot
Автоматически собирает вакансии из Telegram каналов и отправляет их пользователю
"""

import asyncio
import argparse
import signal
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from config.settings import settings
from config.logging_config import setup_logging, get_logger
from database.connection import init_database, close_database
from database.models import Base
from scheduler.job_scheduler import job_scheduler, run_vacancy_collection
from notifiers.telegram_bot import telegram_notifier
from utils.csv_loader import load_channels_from_csv

# Настройка логирования
setup_logging()
logger = get_logger(__name__)


# Обработчик команды /start для бота
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start от пользователя"""
    user = update.effective_user
    chat_id = update.effective_chat.id

    logger.info(f"Received /start from @{user.username} (chat_id: {chat_id})")

    # Сохраняем chat_id пользователя
    await telegram_notifier.save_chat_id(user.username, chat_id)

    await update.message.reply_text(
        f"Привет, @{user.username}!\n\n"
        f"Бот настроен и готов к работе.\n"
        f"Вакансии будут автоматически приходить каждый день в {settings.SCHEDULE_TIME} МСК."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    await update.message.reply_text(
        "🎬 Telegram Vacancy Collector Bot\n\n"
        f"Автоматический сбор вакансий:\n"
        f"• Сценарист\n"
        f"• Редактор (видеопроизводство)\n"
        f"• Шеф-редактор (видеопроизводство)\n\n"
        f"Расписание: ежедневно в {settings.SCHEDULE_TIME} МСК\n\n"
        f"Доступные команды:\n"
        f"/start - Начать работу с ботом\n"
        f"/help - Показать эту справку"
    )


async def run_bot_commands():
    """Запуск бота для обработки команд /start"""
    logger.info("Starting bot command handler...")

    application = Application.builder().token(settings.BOT_TOKEN).build()

    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))

    # Запускаем polling (обработку сообщений)
    await application.initialize()
    await application.start()
    await application.updater.start_polling(drop_pending_updates=True)

    logger.info("Bot command handler started")

    return application


def setup_signal_handlers(loop):
    """Настройка обработчиков сигналов для graceful shutdown"""

    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        job_scheduler.stop()
        close_database()
        loop.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


async def main(test_mode=False):
    """Главная функция приложения"""
    logger.info("=" * 80)
    logger.info("Starting Telegram Vacancy Collector Bot")
    logger.info("=" * 80)

    try:
        # 1. Валидация настроек
        logger.info("Step 1: Validating configuration...")
        settings.validate()
        logger.info("Configuration validated successfully")

        # 2. Инициализация БД
        logger.info("Step 2: Initializing database...")
        engine = init_database()

        # Создание таблиц (если не существуют)
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")

        # 3. Загрузка каналов из CSV (если еще не загружены)
        logger.info("Step 3: Loading channels from CSV...")
        loaded_count = load_channels_from_csv()
        if loaded_count > 0:
            logger.info(f"Loaded {loaded_count} new channels from CSV")
        else:
            logger.info("No new channels to load (already in database)")

        # 4. Запуск бота для обработки команд
        logger.info("Step 4: Starting bot command handler...")
        bot_app = await run_bot_commands()

        # 5. Запуск планировщика (если не тестовый режим)
        if not test_mode:
            logger.info("Step 5: Starting job scheduler...")
            job_scheduler.start()
            logger.info(f"Job scheduler started. Jobs will run at {settings.SCHEDULE_TIME} {settings.TIMEZONE}")
        else:
            logger.info("Step 5: Test mode - running vacancy collection immediately...")
            await run_vacancy_collection()
            logger.info("Test run completed")

            # Останавливаем бота после тестового запуска
            await bot_app.updater.stop()
            await bot_app.stop()
            await bot_app.shutdown()
            return

        # 6. Основной цикл
        logger.info("=" * 80)
        logger.info("Bot is running. Press Ctrl+C to stop.")
        logger.info("=" * 80)

        # Держим бота активным
        while True:
            await asyncio.sleep(60)  # Heartbeat каждую минуту
            logger.debug("Heartbeat: Bot is running...")

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise
    finally:
        # Очистка ресурсов
        logger.info("Shutting down...")
        job_scheduler.stop()
        close_database()
        logger.info("Shutdown complete")


if __name__ == '__main__':
    # Парсинг аргументов командной строки
    parser = argparse.ArgumentParser(description='Telegram Vacancy Collector Bot')
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run in test mode (execute collection immediately and exit)'
    )
    args = parser.parse_args()

    # Запуск приложения
    try:
        asyncio.run(main(test_mode=args.test))
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application crashed: {e}", exc_info=True)
        exit(1)
