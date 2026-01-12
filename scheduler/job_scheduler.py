import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone
from collectors.channel_reader import channel_reader
from processors.vacancy_extractor import vacancy_extractor
from processors.vacancy_filter import vacancy_filter
from processors.deduplicator import deduplicator
from notifiers.telegram_bot import telegram_notifier
from database.models import JobRun, Vacancy, Channel
from database.connection import get_session, close_session, init_database
from utils.csv_loader import get_enabled_channels
from utils.hash_generator import generate_vacancy_hash
from config.settings import settings
from config.logging_config import get_logger

logger = get_logger(__name__)


class JobScheduler:
    """Планировщик задач для сбора вакансий"""

    def __init__(self):
        self.scheduler = None
        self.timezone = timezone(settings.TIMEZONE)
        logger.info(f"JobScheduler initialized (timezone: {settings.TIMEZONE})")

    def start(self):
        """Запуск планировщика"""
        if self.scheduler:
            logger.warning("Scheduler already running")
            return

        logger.info("Starting scheduler...")

        self.scheduler = AsyncIOScheduler(timezone=self.timezone)

        # Парсим время из настроек (формат: "21:00")
        hour, minute = settings.SCHEDULE_TIME.split(':')
        hour = int(hour)
        minute = int(minute)

        # Создаем CRON trigger для ежедневного запуска
        trigger = CronTrigger(
            hour=hour,
            minute=minute,
            timezone=self.timezone
        )

        self.scheduler.add_job(
            func=run_vacancy_collection,
            trigger=trigger,
            id='vacancy_collection',
            name='Daily Vacancy Collection',
            replace_existing=True
        )

        self.scheduler.start()
        logger.info(f"Scheduler started. Job will run daily at {settings.SCHEDULE_TIME} {settings.TIMEZONE}")

    def stop(self):
        """Остановка планировщика"""
        if self.scheduler:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")

    def run_now(self):
        """Запустить сбор вакансий немедленно (для тестирования)"""
        logger.info("Running vacancy collection immediately...")
        asyncio.create_task(run_vacancy_collection())


async def run_vacancy_collection():
    """
    Основная функция сбора вакансий.
    Выполняется по расписанию в 21:00 МСК.
    """
    logger.info("=" * 80)
    logger.info("Starting vacancy collection job")
    logger.info("=" * 80)

    session = get_session()
    job_run = JobRun(status='running')

    try:
        session.add(job_run)
        session.commit()

        # 1. Инициализация клиентов
        logger.info("Step 1: Initializing clients...")
        await channel_reader.initialize()
        await telegram_notifier.initialize()

        # 2. Загрузка каналов из БД
        logger.info("Step 2: Loading channels from database...")
        channels = get_enabled_channels()
        logger.info(f"Loaded {len(channels)} enabled channels")

        if not channels:
            logger.warning("No enabled channels found!")
            job_run.status = 'completed'
            job_run.completed_at = datetime.now()
            session.commit()
            return

        # 3. Чтение сообщений из каналов
        logger.info("Step 3: Reading messages from channels (last 24 hours)...")
        all_messages = await channel_reader.read_multiple_channels(channels, hours=24)

        total_messages = sum(len(msgs) for msgs in all_messages.values())
        logger.info(f"Read {total_messages} messages from {len(all_messages)} channels")

        # 4. Извлечение данных о вакансиях
        logger.info("Step 4: Extracting vacancy data from messages...")
        all_vacancies = []

        for channel_username, messages in all_messages.items():
            if not messages:
                continue

            # Находим channel в БД
            channel = session.query(Channel).filter_by(username=channel_username).first()
            if not channel:
                logger.warning(f"Channel not found in DB: {channel_username}")
                continue

            # Извлекаем данные
            vacancies = vacancy_extractor.batch_extract(messages)

            # Добавляем channel_id
            for vacancy in vacancies:
                vacancy['channel_id'] = channel.id

            all_vacancies.extend(vacancies)

        logger.info(f"Extracted {len(all_vacancies)} potential vacancies")
        job_run.vacancies_found = len(all_vacancies)

        # 5. Фильтрация по позициям
        logger.info("Step 5: Filtering vacancies by position...")
        filtered_vacancies = vacancy_filter.filter_vacancies(all_vacancies)
        logger.info(f"Filtered: {len(filtered_vacancies)} relevant vacancies")

        # 6. Дедупликация
        logger.info("Step 6: Removing duplicates...")
        unique_vacancies = deduplicator.filter_duplicates(filtered_vacancies)
        logger.info(f"After deduplication: {len(unique_vacancies)} unique vacancies")

        # 7. Сохранение в БД
        logger.info("Step 7: Saving vacancies to database...")
        saved_vacancies = []

        for vacancy_data in unique_vacancies:
            vacancy_hash = generate_vacancy_hash(
                title=vacancy_data.get('title', ''),
                company=vacancy_data.get('company', ''),
                url=vacancy_data.get('url', '')
            )

            vacancy = Vacancy(
                channel_id=vacancy_data.get('channel_id'),
                message_id=vacancy_data.get('message_id'),
                title=vacancy_data.get('title'),
                company=vacancy_data.get('company'),
                url=vacancy_data.get('url'),
                position_type=vacancy_data.get('position_type'),
                full_text=vacancy_data.get('full_text'),
                hash=vacancy_hash,
                found_at=vacancy_data.get('date', datetime.now())
            )

            session.add(vacancy)
            vacancy_data['hash'] = vacancy_hash  # Для последующей отправки
            saved_vacancies.append(vacancy_data)

        session.commit()
        logger.info(f"Saved {len(saved_vacancies)} vacancies to database")

        # 8. Отправка уведомлений
        logger.info("Step 8: Sending notifications...")
        if saved_vacancies:
            success = await telegram_notifier.send_vacancies(saved_vacancies)
            if success:
                job_run.vacancies_sent = len(saved_vacancies)
                logger.info(f"Sent {len(saved_vacancies)} vacancies to user")
            else:
                logger.warning("Failed to send vacancies to user")
        else:
            # Отправляем сообщение "Вакансий не найдено"
            await telegram_notifier.send_vacancies([])
            logger.info("Sent 'No vacancies found' message")

        # 9. Завершение
        job_run.status = 'completed'
        job_run.completed_at = datetime.now()
        session.commit()

        logger.info("=" * 80)
        logger.info(f"Vacancy collection completed successfully")
        logger.info(f"Total found: {job_run.vacancies_found}")
        logger.info(f"Sent: {job_run.vacancies_sent}")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"Error during vacancy collection: {e}", exc_info=True)
        job_run.status = 'failed'
        job_run.error_message = str(e)
        job_run.completed_at = datetime.now()
        session.commit()

    finally:
        # Закрываем клиенты
        try:
            await channel_reader.close()
        except:
            pass

        close_session(session)


# Глобальный экземпляр
job_scheduler = JobScheduler()
