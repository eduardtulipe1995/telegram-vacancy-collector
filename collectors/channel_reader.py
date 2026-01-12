import asyncio
from datetime import datetime, timedelta
from pyrogram import Client
from pyrogram.errors import FloodWait, UsernameInvalid, ChannelPrivate, PeerIdInvalid
from collectors.rate_limiter import rate_limiter
from config.settings import settings
from config.logging_config import get_logger

logger = get_logger(__name__)


class ChannelReader:
    """
    Читает сообщения из Telegram каналов используя Pyrogram User Bot
    """

    def __init__(self):
        self.client = None
        logger.info("ChannelReader initialized")

    async def initialize(self):
        """Инициализация Pyrogram client"""
        if self.client:
            logger.warning("Client already initialized")
            return

        logger.info("Initializing Pyrogram client...")

        self.client = Client(
            "vacancy_collector",
            api_id=int(settings.API_ID),
            api_hash=settings.API_HASH,
            session_string=settings.SESSION_STRING,
            in_memory=True  # Не создавать session файл
        )

        await self.client.start()
        logger.info("Pyrogram client started successfully")

    async def close(self):
        """Закрытие клиента"""
        if self.client:
            await self.client.stop()
            logger.info("Pyrogram client stopped")

    async def read_channel_messages(self, channel_username, hours=24, limit=100):
        """
        Читает сообщения из канала за последние N часов

        Args:
            channel_username: Username канала (например, 'normrabota')
            hours: Количество часов назад (по умолчанию 24)
            limit: Максимальное количество сообщений (по умолчанию 100)

        Returns:
            List[Message]: Список сообщений
        """
        if not self.client:
            await self.initialize()

        messages = []
        cutoff_time = datetime.now() - timedelta(hours=hours)

        try:
            # Rate limiting
            await rate_limiter.wait_if_needed(channel_username)

            logger.info(f"Reading messages from channel: {channel_username}")

            # Получаем сообщения из канала
            async for message in self.client.get_chat_history(channel_username, limit=limit):
                # Проверяем временную метку
                if message.date < cutoff_time:
                    break

                messages.append(message)

            logger.info(f"Read {len(messages)} messages from {channel_username}")

        except FloodWait as e:
            logger.warning(f"FloodWait for {e.value} seconds on channel {channel_username}")
            await asyncio.sleep(e.value)
            # Retry после ожидания
            return await self.read_channel_messages(channel_username, hours, limit)

        except UsernameInvalid:
            logger.error(f"Invalid username: {channel_username}")

        except ChannelPrivate:
            logger.error(f"Channel is private or not accessible: {channel_username}")

        except PeerIdInvalid:
            logger.error(f"Peer ID invalid for channel: {channel_username}")

        except Exception as e:
            logger.error(f"Error reading channel {channel_username}: {e}")

        return messages

    async def read_multiple_channels(self, channels, hours=24):
        """
        Читает сообщения из нескольких каналов с батчингом

        Args:
            channels: List[Channel] - список объектов Channel из БД
            hours: Количество часов назад

        Returns:
            Dict[str, List[Message]]: {channel_username: [messages]}
        """
        if not self.client:
            await self.initialize()

        all_messages = {}
        batch_size = settings.BATCH_SIZE
        batch_delay = settings.BATCH_DELAY

        logger.info(f"Reading messages from {len(channels)} channels (batch_size={batch_size})")

        for i in range(0, len(channels), batch_size):
            batch = channels[i:i+batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(channels)-1)//batch_size + 1}")

            # Обрабатываем батч параллельно
            tasks = [
                self.read_channel_messages(channel.username, hours=hours)
                for channel in batch
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Сохраняем результаты
            for channel, messages in zip(batch, results):
                if isinstance(messages, Exception):
                    logger.error(f"Exception for channel {channel.username}: {messages}")
                    all_messages[channel.username] = []
                else:
                    all_messages[channel.username] = messages

            # Задержка между батчами (кроме последнего)
            if i + batch_size < len(channels):
                logger.info(f"Waiting {batch_delay}s before next batch...")
                await asyncio.sleep(batch_delay)

        total_messages = sum(len(msgs) for msgs in all_messages.values())
        logger.info(f"Total messages read from all channels: {total_messages}")

        return all_messages


# Глобальный экземпляр
channel_reader = ChannelReader()
