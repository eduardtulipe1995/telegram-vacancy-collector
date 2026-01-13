import json
import asyncio
from openai import AsyncOpenAI
from config.logging_config import get_logger
import os

logger = get_logger(__name__)

SYSTEM_PROMPT = """Ты — фильтр вакансий для видеопродакшена.

Анализируй каждый пост и определи:
1. Это реальная вакансия? (не спам, не реклама канала, не курсы, не поиск заказов фрилансером)
2. Позиция одна из: сценарист / редактор (видео/монтажёр) / шеф-редактор?
3. Сфера: видеопродакшн (реклама, кино, документалки, продакшены, видеоконтент)?

ПОДХОДЯТ:
- Сценарист для рекламы, кино, видеороликов, YouTube
- Видеоредактор, монтажёр, редактор видео
- Шеф-редактор видеопродакшена, главный редактор продакшена

НЕ подходят:
- SMM-менеджеры, контент-менеджеры, копирайтеры
- Текстовые/литературные редакторы
- Журналистика, новостные редакции, блоги
- Редакторы сайтов, контент-редакторы
- Курсы, реклама каналов, спам
- Поиск заказов фрилансерами (не вакансии)

Для каждого поста верни JSON:
{
  "vacancies": [
    {
      "index": 0,
      "is_relevant": true/false,
      "position_type": "сценарист" | "редактор" | "шеф-редактор" | null,
      "title": "Чистое название позиции",
      "company": "Компания/проект или null"
    }
  ]
}

Если вакансия НЕ подходит, всё равно укажи is_relevant: false и причину в title."""


class GPTVacancyFilter:
    """Фильтрует и обрабатывает вакансии с помощью GPT"""

    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"
        logger.info(f"GPTVacancyFilter initialized (model: {self.model})")

    async def filter_vacancies(self, vacancies, batch_size=15):
        """
        Фильтрует вакансии с помощью GPT

        Args:
            vacancies: List[dict] - список вакансий с полями full_text, url, message_id, channel_id
            batch_size: int - размер батча для одного запроса к GPT

        Returns:
            List[dict]: Отфильтрованные и обработанные вакансии
        """
        if not vacancies:
            return []

        logger.info(f"GPT filtering {len(vacancies)} vacancies...")

        filtered = []
        batches = [vacancies[i:i + batch_size] for i in range(0, len(vacancies), batch_size)]

        for batch_idx, batch in enumerate(batches):
            logger.info(f"Processing GPT batch {batch_idx + 1}/{len(batches)} ({len(batch)} items)")

            try:
                results = await self._process_batch(batch)
                filtered.extend(results)
            except Exception as e:
                logger.error(f"Error processing batch {batch_idx + 1}: {e}")
                continue

            # Небольшая пауза между батчами
            if batch_idx < len(batches) - 1:
                await asyncio.sleep(1)

        logger.info(f"GPT filtering complete: {len(filtered)} relevant vacancies")
        return filtered

    async def _process_batch(self, batch):
        """Обрабатывает батч вакансий через GPT"""

        # Формируем текст для GPT
        posts_text = ""
        for i, vacancy in enumerate(batch):
            text = vacancy.get('full_text', '')[:1500]  # Ограничиваем длину
            posts_text += f"\n--- ПОСТ {i} ---\n{text}\n"

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Проанализируй эти посты:\n{posts_text}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=2000
            )

            result_text = response.choices[0].message.content
            result = json.loads(result_text)

            filtered = []
            for item in result.get('vacancies', []):
                idx = item.get('index', 0)
                if idx >= len(batch):
                    continue

                if item.get('is_relevant'):
                    original = batch[idx]
                    filtered.append({
                        'title': item.get('title', 'Без названия'),
                        'company': item.get('company'),
                        'position_type': item.get('position_type'),
                        'url': original.get('url'),
                        'full_text': original.get('full_text'),
                        'message_id': original.get('message_id'),
                        'channel_id': original.get('channel_id'),
                        'date': original.get('date')
                    })

            return filtered

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return []
        except Exception as e:
            logger.error(f"GPT API error: {e}")
            return []


# Глобальный экземпляр
gpt_filter = GPTVacancyFilter()
