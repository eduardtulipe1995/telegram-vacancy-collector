import csv
import os
from database.models import Channel
from database.connection import get_session, close_session
from config.logging_config import get_logger

logger = get_logger(__name__)


def extract_username_from_url(url):
    """
    Извлекает username из Telegram URL
    https://t.me/normrabota -> normrabota
    https://t.me/+R_KxUQG5hYo5ZjAy -> +R_KxUQG5hYo5ZjAy (private link)
    """
    url = url.strip()
    if 't.me/' in url:
        username = url.split('t.me/')[-1]
        return username
    return url


def load_channels_from_csv(csv_path='data/Телеграм_каналы_для_поиска_работы.csv'):
    """Загрузить каналы из CSV в базу данных"""

    if not os.path.exists(csv_path):
        logger.error(f"CSV file not found: {csv_path}")
        return 0

    session = get_session()
    loaded_count = 0
    skipped_count = 0

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                name = row.get('Название', '').strip()
                description = row.get('Описание', '').strip()
                url = row.get('Телеграмм канал', '').strip()

                if not url:
                    logger.warning(f"Skipping row with empty URL: {row}")
                    skipped_count += 1
                    continue

                username = extract_username_from_url(url)

                # Проверяем, существует ли уже канал
                existing = session.query(Channel).filter_by(username=username).first()
                if existing:
                    logger.debug(f"Channel already exists: {username}")
                    skipped_count += 1
                    continue

                # Создаем новый канал
                channel = Channel(
                    name=name or username,
                    description=description,
                    username=username,
                    enabled=True
                )
                session.add(channel)
                loaded_count += 1
                logger.info(f"Added channel: {username} ({name})")

        session.commit()
        logger.info(f"Channels loaded: {loaded_count}, skipped: {skipped_count}")

    except Exception as e:
        session.rollback()
        logger.error(f"Error loading channels from CSV: {e}")
        raise
    finally:
        close_session(session)

    return loaded_count


def get_enabled_channels():
    """Получить список активных каналов из БД"""
    session = get_session()
    try:
        channels = session.query(Channel).filter_by(enabled=True).all()
        return channels
    finally:
        close_session(session)


if __name__ == '__main__':
    # Для тестирования
    print("Loading channels from CSV...")
    count = load_channels_from_csv()
    print(f"Loaded {count} channels")

    channels = get_enabled_channels()
    print(f"Total enabled channels: {len(channels)}")
