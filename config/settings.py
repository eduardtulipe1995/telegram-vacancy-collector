import os
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла (для локальной разработки)
load_dotenv()


class Settings:
    """Настройки приложения из переменных окружения"""

    # Telegram User Account (Pyrogram)
    API_ID = os.getenv('API_ID')
    API_HASH = os.getenv('API_HASH')
    SESSION_STRING = os.getenv('SESSION_STRING')

    # Telegram Bot
    BOT_TOKEN = os.getenv('BOT_TOKEN')

    # Получатель вакансий
    TARGET_USERNAME = os.getenv('TARGET_USERNAME', 'mediaya')

    # Database
    DATABASE_URL = os.getenv('DATABASE_URL')

    # Scheduler
    SCHEDULE_TIME = os.getenv('SCHEDULE_TIME', '21:00')
    TIMEZONE = os.getenv('TIMEZONE', 'Europe/Moscow')

    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    # Rate limiting
    RATE_LIMIT_GLOBAL_DELAY = float(os.getenv('RATE_LIMIT_GLOBAL_DELAY', '0.1'))  # 100ms
    RATE_LIMIT_CHANNEL_DELAY = float(os.getenv('RATE_LIMIT_CHANNEL_DELAY', '0.5'))  # 500ms
    BATCH_SIZE = int(os.getenv('BATCH_SIZE', '10'))
    BATCH_DELAY = int(os.getenv('BATCH_DELAY', '30'))  # секунд

    @classmethod
    def validate(cls):
        """Валидация обязательных переменных окружения"""
        required_vars = [
            'API_ID',
            'API_HASH',
            'SESSION_STRING',
            'BOT_TOKEN',
            'DATABASE_URL',
        ]

        missing = []
        for var in required_vars:
            if not getattr(cls, var):
                missing.append(var)

        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                f"Please check your .env file or environment configuration."
            )

        return True


# Создаем экземпляр настроек
settings = Settings()
