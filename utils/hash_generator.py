import hashlib
from utils.text_utils import normalize_text


def generate_vacancy_hash(title, company='', url=''):
    """
    Генерирует уникальный SHA-256 хеш для вакансии на основе:
    - Нормализованного названия
    - Названия компании
    - URL

    Args:
        title: Название вакансии
        company: Название компании (опционально)
        url: URL вакансии (опционально)

    Returns:
        str: SHA-256 хеш (64 символа)
    """
    # Нормализация компонентов
    normalized_title = normalize_text(title) if title else ''
    normalized_company = normalize_text(company) if company else ''
    normalized_url = url.strip() if url else ''

    # Создание строки для хеширования
    hash_string = f"{normalized_title}|{normalized_company}|{normalized_url}"

    # Генерация SHA-256 хеша
    hash_object = hashlib.sha256(hash_string.encode('utf-8'))
    return hash_object.hexdigest()


def is_same_vacancy(hash1, hash2):
    """Проверка идентичности двух вакансий по хешам"""
    return hash1 == hash2


if __name__ == '__main__':
    # Тестирование
    hash1 = generate_vacancy_hash(
        title='Видеоредактор',
        company='Студия Креатив',
        url='https://t.me/channel/123'
    )

    hash2 = generate_vacancy_hash(
        title='Видео редактор',  # Небольшое отличие
        company='Студия Креатив',
        url='https://t.me/channel/123'
    )

    print(f"Hash 1: {hash1}")
    print(f"Hash 2: {hash2}")
    print(f"Are same: {is_same_vacancy(hash1, hash2)}")
