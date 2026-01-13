from processors.context_analyzer import context_analyzer
from config.logging_config import get_logger

logger = get_logger(__name__)


class VacancyFilter:
    """Фильтрует вакансии по позициям и контексту"""

    # Конфигурация целевых позиций
    TARGET_POSITIONS = {
        'сценарист': {
            'keywords': [
                'сценарист', 'screenwriter', 'копирайтер-сценарист',
                'сценаристом', 'сценариста', 'сценаристку', 'сценаристов',
                'автор сценариев', 'автор сценария', 'script writer',
                'scriptwriter', 'сценарное', 'сценарий'
            ],
            'exclude': [],
            'requires_video_context': False
        },
        'шеф-редактор': {
            'keywords': [
                'шеф-редактор', 'шеф редактор', 'главный редактор',
                'шеф-редактора', 'шеф редактора', 'chief editor',
                'ведущий редактор', 'старший редактор', 'senior editor',
                'руководитель редакции', 'head editor'
            ],
            'exclude': [
                'книжное издательство', 'книжный',
                'журнал', 'газета', 'онлайн-медиа', 'онлайн медиа',
                'издательств', 'журналист', 'новостной'
            ],
            'requires_video_context': True
        },
        'редактор': {
            'keywords': [
                'редактор видео', 'видеоредактор', 'видео редактор',
                'video editor', 'монтажер', 'монтажёр', 'монтажера',
                'редактор роликов', 'видеомонтажер', 'видео-редактор',
                'editor', 'монтаж видео', 'монтажист',
                'colorist', 'колорист', 'color grading',
                'режиссер монтажа', 'режиссёр монтажа'
            ],
            'exclude': [
                'редактор текста', 'текстовый редактор',
                'литературный редактор', 'редактор статей',
                'книжный редактор', 'редактор контента', 'контент-редактор',
                'smm редактор', 'smm-редактор', 'копирайтер',
                'редактор сайта', 'веб-редактор'
            ],
            'requires_video_context': True
        }
    }

    def check_position_match(self, vacancy_data):
        """
        Проверяет, соответствует ли вакансия целевым позициям

        Args:
            vacancy_data: dict с полями title, company, full_text

        Returns:
            str or None: Название позиции ('сценарист', 'редактор', 'шеф-редактор') или None
        """
        title = vacancy_data.get('title', '').lower()
        full_text = vacancy_data.get('full_text', '').lower()

        # Объединяем заголовок и текст для анализа
        combined_text = f"{title} {full_text}"

        for position_name, config in self.TARGET_POSITIONS.items():
            # Проверка keywords
            keyword_found = any(
                keyword in combined_text
                for keyword in config['keywords']
            )

            if not keyword_found:
                continue

            # Проверка исключений
            is_excluded = any(
                exclude in combined_text
                for exclude in config['exclude']
            )

            if is_excluded:
                logger.debug(f"Position {position_name} excluded due to exclude keywords")
                continue

            # Проверка видео-контекста (если требуется)
            if config['requires_video_context']:
                has_video_context = context_analyzer.check_video_context(full_text)
                if not has_video_context:
                    logger.debug(f"Position {position_name} rejected: no video context")
                    continue

            logger.info(f"Position matched: {position_name}")
            return position_name

        return None

    def filter_vacancies(self, vacancies):
        """
        Фильтрует список вакансий

        Args:
            vacancies: List[dict] - список данных о вакансиях

        Returns:
            List[dict]: Отфильтрованный список с добавленным полем 'position_type'
        """
        filtered = []

        for vacancy in vacancies:
            position_type = self.check_position_match(vacancy)
            if position_type:
                vacancy['position_type'] = position_type
                filtered.append(vacancy)

        logger.info(f"Filtered vacancies: {len(filtered)}/{len(vacancies)}")

        return filtered


# Глобальный экземпляр
vacancy_filter = VacancyFilter()
