import asyncio
import time
from config.settings import settings
from config.logging_config import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """
    Rate limiter для соблюдения ограничений Telegram API:
    - Глобальная задержка между запросами
    - Задержка для каждого канала
    - Предотвращение FloodWait
    """

    def __init__(self):
        self.last_request_time = {}  # {channel_id: timestamp}
        self.last_global_request = 0

        # Настройки из конфигурации
        self.min_channel_delay = settings.RATE_LIMIT_CHANNEL_DELAY  # 500ms
        self.global_delay = settings.RATE_LIMIT_GLOBAL_DELAY  # 100ms

        logger.info(
            f"RateLimiter initialized: "
            f"global_delay={self.global_delay}s, "
            f"channel_delay={self.min_channel_delay}s"
        )

    async def wait_if_needed(self, channel_id=None):
        """
        Применяет rate limiting перед запросом

        Args:
            channel_id: ID канала (опционально)
        """
        current_time = time.time()

        # Глобальная задержка
        if self.last_global_request > 0:
            elapsed = current_time - self.last_global_request
            if elapsed < self.global_delay:
                wait_time = self.global_delay - elapsed
                logger.debug(f"Global rate limit: waiting {wait_time:.3f}s")
                await asyncio.sleep(wait_time)

        # Задержка для конкретного канала
        if channel_id and channel_id in self.last_request_time:
            elapsed = current_time - self.last_request_time[channel_id]
            if elapsed < self.min_channel_delay:
                wait_time = self.min_channel_delay - elapsed
                logger.debug(f"Channel {channel_id} rate limit: waiting {wait_time:.3f}s")
                await asyncio.sleep(wait_time)

        # Обновляем timestamps
        current_time = time.time()
        if channel_id:
            self.last_request_time[channel_id] = current_time
        self.last_global_request = current_time

    def reset(self):
        """Сброс всех счетчиков"""
        self.last_request_time = {}
        self.last_global_request = 0
        logger.info("RateLimiter reset")


# Глобальный экземпляр rate limiter
rate_limiter = RateLimiter()
