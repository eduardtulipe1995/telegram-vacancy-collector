import re


def normalize_text(text):
    """
    Нормализация текста для дедупликации и сравнения:
    - приведение к lowercase
    - сохранение важных символов (+, -, /)
    - удаление лишних специальных символов
    - удаление лишних пробелов
    """
    if not text:
        return ''

    # Lowercase
    text = text.lower().strip()

    # Удаление специальных символов, но сохраняем важные: +, -, /, #, @
    # Это важно для: C++, Python-разработчик, SMM/контент и т.д.
    text = re.sub(r'[^\w\s\+\-\/#@]', '', text)

    # Удаление множественных пробелов
    text = re.sub(r'\s+', ' ', text)

    return text


def extract_url_from_text(text):
    """Извлечь URL из текста сообщения"""
    if not text:
        return None

    # Поиск URLs
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    urls = re.findall(url_pattern, text)

    if urls:
        return urls[0]

    # Поиск t.me ссылок без http
    tme_pattern = r't\.me/[a-zA-Z0-9_/]+'
    tme_links = re.findall(tme_pattern, text)

    if tme_links:
        return f"https://{tme_links[0]}"

    return None


def clean_text(text):
    """Очистка текста от лишних символов и форматирования"""
    if not text:
        return ''

    # Удаление множественных переносов строк
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Удаление лишних пробелов
    text = re.sub(r' {2,}', ' ', text)

    # Удаление пробелов в начале и конце строк
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)

    return text.strip()


def truncate_text(text, max_length=100):
    """Обрезать текст до указанной длины"""
    if not text:
        return ''

    if len(text) <= max_length:
        return text

    return text[:max_length] + '...'


def extract_first_line(text):
    """Извлечь первую строку из текста (обычно это заголовок вакансии)"""
    if not text:
        return ''

    lines = text.strip().split('\n')
    if lines:
        return lines[0].strip()

    return ''
