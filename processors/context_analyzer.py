from rapidfuzz import fuzz
from config.logging_config import get_logger

logger = get_logger(__name__)


class ContextAnalyzer:
    """Анализирует контекст вакансии для определения связи с видеопроизводством"""

    # Ключевые слова видеопроизводства
    VIDEO_PRODUCTION_KEYWORDS = [
        'видео', 'видеопроизводство', 'видеопродакшн', 'video production',
        'монтаж', 'постпродакшн', 'постпродакшен', 'post-production', 'пост-продакшн',
        'ролик', 'видеоролик', 'видеоконтент',
        'съёмка', 'съемка', 'filming', 'shooting',
        'продакшн', 'продакшен', 'production',
        'студия видео', 'видеостудия', 'video studio',
        'youtube', 'ютуб', 'тикток', 'tiktok', 'reels', 'рилс',
        'креатив', 'creative production',
        'видеограф', 'оператор', 'cinematographer', 'кинематограф',
        'видеоконтент', 'видео контент', 'video content',
        'монтажер', 'видеомонтаж', 'видео монтаж',
        'premiere', 'after effects', 'davinci', 'final cut',
        'видеоблог', 'видео блог', 'влог', 'vlog',
        'медиапроизводство', 'медиа производство'
    ]

    def __init__(self, min_matches=2, fuzzy_threshold=85):
        """
        Args:
            min_matches: Минимальное количество совпадений keywords
            fuzzy_threshold: Порог для fuzzy matching (0-100)
        """
        self.min_matches = min_matches
        self.fuzzy_threshold = fuzzy_threshold

    def check_video_context(self, text):
        """
        Проверяет, относится ли текст к видеопроизводству

        Args:
            text: Текст вакансии

        Returns:
            bool: True если контекст видеопроизводства определен
        """
        if not text:
            return False

        text_lower = text.lower()
        match_count = 0

        # Точные совпадения
        for keyword in self.VIDEO_PRODUCTION_KEYWORDS:
            if keyword in text_lower:
                match_count += 1

        # Fuzzy matching (для опечаток)
        if match_count < self.min_matches:
            for keyword in self.VIDEO_PRODUCTION_KEYWORDS:
                # Пропускаем слишком короткие keywords для fuzzy matching
                if len(keyword) < 5:
                    continue

                similarity = fuzz.partial_ratio(keyword, text_lower)
                if similarity >= self.fuzzy_threshold:
                    match_count += 1

        is_video_context = match_count >= self.min_matches

        logger.debug(
            f"Video context check: {match_count} matches "
            f"(min_matches={self.min_matches}) -> {is_video_context}"
        )

        return is_video_context

    def get_matched_keywords(self, text):
        """
        Возвращает список найденных keywords (для отладки)

        Args:
            text: Текст вакансии

        Returns:
            List[str]: Список найденных keywords
        """
        if not text:
            return []

        text_lower = text.lower()
        matched = []

        for keyword in self.VIDEO_PRODUCTION_KEYWORDS:
            if keyword in text_lower:
                matched.append(keyword)

        return matched


# Глобальный экземпляр
context_analyzer = ContextAnalyzer()
