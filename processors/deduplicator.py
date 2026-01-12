from datetime import datetime, timedelta
from rapidfuzz import fuzz
from database.models import Vacancy
from database.connection import get_session, close_session
from utils.hash_generator import generate_vacancy_hash
from config.logging_config import get_logger

logger = get_logger(__name__)


class Deduplicator:
    """Удаляет дубликаты вакансий на основе хеша и fuzzy matching"""

    def __init__(self, similarity_threshold=90, time_window_days=7):
        """
        Args:
            similarity_threshold: Порог similarity для fuzzy matching (0-100)
            time_window_days: Временное окно для проверки дубликатов (в днях)
        """
        self.similarity_threshold = similarity_threshold
        self.time_window_days = time_window_days

    def is_duplicate(self, vacancy_data, session=None):
        """
        Проверяет, является ли вакансия дубликатом

        Args:
            vacancy_data: dict с данными вакансии
            session: SQLAlchemy session (опционально)

        Returns:
            bool: True если дубликат
        """
        should_close_session = False
        if session is None:
            session = get_session()
            should_close_session = True

        try:
            # Генерируем хеш
            vacancy_hash = generate_vacancy_hash(
                title=vacancy_data.get('title', ''),
                company=vacancy_data.get('company', ''),
                url=vacancy_data.get('url', '')
            )

            # 1. Проверка по точному хешу
            cutoff_date = datetime.now() - timedelta(days=self.time_window_days)
            existing_by_hash = session.query(Vacancy).filter(
                Vacancy.hash == vacancy_hash,
                Vacancy.found_at >= cutoff_date
            ).first()

            if existing_by_hash:
                logger.debug(f"Duplicate found by hash: {vacancy_data.get('title')[:50]}")
                return True

            # 2. Проверка по URL (если есть)
            url = vacancy_data.get('url')
            if url:
                existing_by_url = session.query(Vacancy).filter(
                    Vacancy.url == url,
                    Vacancy.found_at >= cutoff_date
                ).first()

                if existing_by_url:
                    logger.debug(f"Duplicate found by URL: {url}")
                    return True

            # 3. Fuzzy matching по названию
            title = vacancy_data.get('title', '')
            if len(title) > 10:  # Только для достаточно длинных заголовков
                recent_vacancies = session.query(Vacancy).filter(
                    Vacancy.found_at >= cutoff_date,
                    Vacancy.position_type == vacancy_data.get('position_type')
                ).all()

                for existing in recent_vacancies:
                    similarity = fuzz.ratio(title.lower(), existing.title.lower())
                    if similarity >= self.similarity_threshold:
                        logger.debug(
                            f"Duplicate found by fuzzy matching "
                            f"(similarity={similarity}): {title[:50]}"
                        )
                        return True

            return False

        finally:
            if should_close_session:
                close_session(session)

    def filter_duplicates(self, vacancies):
        """
        Фильтрует дубликаты из списка вакансий

        Args:
            vacancies: List[dict] - список вакансий

        Returns:
            List[dict]: Уникальные вакансии
        """
        session = get_session()
        unique_vacancies = []
        duplicate_count = 0

        try:
            for vacancy in vacancies:
                if not self.is_duplicate(vacancy, session=session):
                    unique_vacancies.append(vacancy)
                else:
                    duplicate_count += 1

            logger.info(
                f"Deduplication complete: {len(unique_vacancies)} unique, "
                f"{duplicate_count} duplicates filtered"
            )

        finally:
            close_session(session)

        return unique_vacancies

    def cleanup_old_vacancies(self, days=30):
        """
        Удаляет вакансии старше указанного количества дней

        Args:
            days: Количество дней (по умолчанию 30)

        Returns:
            int: Количество удаленных вакансий
        """
        session = get_session()
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            deleted_count = session.query(Vacancy).filter(
                Vacancy.found_at < cutoff_date
            ).delete()

            session.commit()
            logger.info(f"Cleaned up {deleted_count} old vacancies (older than {days} days)")

            return deleted_count

        except Exception as e:
            session.rollback()
            logger.error(f"Error cleaning up old vacancies: {e}")
            raise
        finally:
            close_session(session)


# Глобальный экземпляр
deduplicator = Deduplicator()
