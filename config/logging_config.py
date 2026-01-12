import logging
import sys
from config.settings import settings


def setup_logging():
    """Настройка логирования для всего приложения"""

    # Создаем корневой логгер
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    # Очищаем существующие handlers
    logger.handlers = []

    # Console handler (для Render Logs)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    # Формат логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    # Отключаем логи от сторонних библиотек (если слишком шумные)
    logging.getLogger('telegram').setLevel(logging.WARNING)
    logging.getLogger('pyrogram').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
    logging.getLogger('apscheduler').setLevel(logging.INFO)

    return logger


def get_logger(name):
    """Получить логгер для конкретного модуля"""
    return logging.getLogger(name)
