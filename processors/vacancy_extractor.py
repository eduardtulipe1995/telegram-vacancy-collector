import re
from telethon.tl.types import MessageEntityUrl, MessageEntityTextUrl
from utils.text_utils import extract_first_line, extract_url_from_text, clean_text
from config.logging_config import get_logger

logger = get_logger(__name__)


class VacancyExtractor:
    """Извлекает информацию о вакансии из сообщения Telegram"""

    # Patterns для извлечения компании (приоритет по порядку)
    COMPANY_PATTERNS = [
        # Прямое указание компании
        r'компания[:\s]+[«"]?([А-Яа-яA-Za-z0-9\s\-\.]+)[»"]?',
        r'(?:в\s+)?(?:компанию?|студию?|агентств[оау]?)\s+[«"]?([А-Яа-яA-Za-z0-9\s\-\.]+)[»"]?',
        # Компания ищет/приглашает
        r'([А-Яа-яA-Za-z0-9\s\-\.]+)\s+(?:ищет|приглашает|набирает|открыта вакансия)',
        r'(?:в|для)\s+([А-Яа-яA-Za-z0-9\s\-\.]+)\s+(?:требуется|нужен|ищем)',
        # Работодатель
        r'работодатель[:\s]+[«"]?([А-Яа-яA-Za-z0-9\s\-\.]+)[»"]?',
        # Хештег с названием компании
        r'#([A-Za-z0-9_]+)',
        # Название в кавычках в начале текста
        r'^[«"]([А-Яа-яA-Za-z0-9\s\-\.]+)[»"]',
    ]

    def extract_vacancy_data(self, message):
        """
        Извлекает данные о вакансии из сообщения

        Args:
            message: Pyrogram Message object

        Returns:
            dict: {
                'title': str,
                'company': str or None,
                'url': str or None,
                'full_text': str,
                'message_id': int,
                'date': datetime
            }
        """
        if not message.text:
            return None

        text = clean_text(message.text)

        # Извлечение заголовка (первая строка)
        title = extract_first_line(text)
        if not title or len(title) < 5:  # Слишком короткий заголовок
            # Попробуем взять первые 100 символов
            title = text[:100] if len(text) > 100 else text

        # Извлечение компании
        company = self._extract_company(text)

        # Извлечение URL
        url = self._extract_url(message)

        vacancy_data = {
            'title': title,
            'company': company,
            'url': url,
            'full_text': text,
            'message_id': message.id,
            'date': message.date
        }

        return vacancy_data

    def _extract_company(self, text):
        """Извлекает название компании из текста"""
        text_lower = text.lower()

        for pattern in self.COMPANY_PATTERNS:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                company = match.group(1).strip()
                # Очистка от лишних символов
                company = company.strip('.,;:!?-_')
                if len(company) > 3:  # Минимальная длина названия
                    return company

        return None

    def _extract_url(self, message):
        """Извлекает URL из сообщения"""
        # 1. Проверяем inline buttons (reply_markup) - Telethon использует rows атрибут
        if message.reply_markup:
            try:
                # В Telethon reply_markup может быть ReplyInlineMarkup
                rows = getattr(message.reply_markup, 'rows', None)
                if rows:
                    for row in rows:
                        for button in row.buttons:
                            if hasattr(button, 'url') and button.url:
                                return button.url
            except Exception as e:
                logger.debug(f"Error extracting URL from reply_markup: {e}")

        # 2. Ищем URL в тексте
        if message.text:
            url = extract_url_from_text(message.text)
            if url:
                return url

        # 3. Проверяем entities (ссылки в тексте) - Telethon entities
        if message.entities:
            for entity in message.entities:
                # Telethon использует типы объектов, а не строки
                if isinstance(entity, MessageEntityUrl):
                    # URL прямо в тексте
                    if message.text:
                        url_text = message.text[entity.offset:entity.offset + entity.length]
                        return url_text
                elif isinstance(entity, MessageEntityTextUrl):
                    # Гиперссылка (текст со скрытым URL)
                    return entity.url

        # 4. Генерируем ссылку на сообщение в канале
        # В Telethon это peer_id.channel_id или chat
        try:
            if hasattr(message, 'peer_id') and hasattr(message.peer_id, 'channel_id'):
                # Получаем username канала если он есть в чате
                chat = getattr(message, 'chat', None)
                if chat and hasattr(chat, 'username') and chat.username:
                    return f"https://t.me/{chat.username}/{message.id}"
        except Exception as e:
            logger.debug(f"Error generating message URL: {e}")

        return None

    def batch_extract(self, messages):
        """
        Обрабатывает несколько сообщений

        Args:
            messages: List[Message]

        Returns:
            List[dict]: Список данных о вакансиях
        """
        vacancies = []

        for message in messages:
            try:
                vacancy_data = self.extract_vacancy_data(message)
                if vacancy_data:
                    vacancies.append(vacancy_data)
            except Exception as e:
                logger.error(f"Error extracting vacancy from message {message.id}: {e}")

        return vacancies


# Глобальный экземпляр
vacancy_extractor = VacancyExtractor()
