import asyncio
from telegram import Bot
from telegram.error import TelegramError, Forbidden, BadRequest
from database.models import UserChatID, SentVacancy, Vacancy
from database.connection import get_session, close_session
from config.settings import settings
from config.logging_config import get_logger

logger = get_logger(__name__)


class TelegramNotifier:
    """Отправляет уведомления о вакансиях через Telegram Bot"""

    def __init__(self):
        self.bot = None
        self.target_usernames = settings.get_target_usernames()
        logger.info(f"TelegramNotifier initialized (targets: {', '.join('@' + u for u in self.target_usernames)})")

    async def initialize(self):
        """Инициализация Telegram Bot"""
        if self.bot:
            logger.warning("Bot already initialized")
            return

        logger.info("Initializing Telegram Bot...")
        self.bot = Bot(token=settings.BOT_TOKEN)

        # Проверяем, что бот работает
        try:
            bot_info = await self.bot.get_me()
            logger.info(f"Bot initialized: @{bot_info.username}")
        except Exception as e:
            logger.error(f"Failed to initialize bot: {e}")
            raise

    async def get_chat_id(self, username):
        """
        Получить chat_id пользователя из БД

        Args:
            username: Username пользователя

        Returns:
            int or None: chat_id пользователя
        """
        session = get_session()
        try:
            user_chat = session.query(UserChatID).filter_by(
                username=username
            ).first()

            if user_chat:
                return user_chat.chat_id

            logger.warning(
                f"Chat ID not found for @{username}. "
                f"User needs to send /start to the bot first."
            )
            return None

        finally:
            close_session(session)

    async def save_chat_id(self, username, chat_id):
        """
        Сохранить chat_id пользователя в БД (вызывается при /start)

        Args:
            username: Username пользователя
            chat_id: Chat ID пользователя
        """
        session = get_session()
        try:
            user_chat = session.query(UserChatID).filter_by(username=username).first()

            if user_chat:
                user_chat.chat_id = chat_id
                logger.info(f"Updated chat_id for @{username}")
            else:
                user_chat = UserChatID(username=username, chat_id=chat_id)
                session.add(user_chat)
                logger.info(f"Saved new chat_id for @{username}")

            session.commit()

        except Exception as e:
            session.rollback()
            logger.error(f"Error saving chat_id: {e}")
            raise
        finally:
            close_session(session)

    def format_vacancies_message(self, vacancies):
        """
        Форматирует список вакансий в текстовое сообщение
        Группировка по типу позиции, минималистичный формат

        Args:
            vacancies: List[dict] - список вакансий

        Returns:
            str: Отформатированное сообщение
        """
        if not vacancies:
            return (
                "📭 Вакансий не найдено\n\n"
                "За последние 24 часа не было найдено новых вакансий "
                "по вашим критериям (сценарист, редактор видео, шеф-редактор)."
            )

        # Группируем вакансии по типу позиции
        groups = {
            'сценарист': [],
            'редактор': [],
            'шеф-редактор': []
        }

        for vacancy in vacancies:
            position_type = vacancy.get('position_type', 'редактор')
            if position_type in groups:
                groups[position_type].append(vacancy)

        # Формируем сообщение
        message = ""

        # Сценаристы
        if groups['сценарист']:
            message += "📝 СЦЕНАРИСТЫ:\n\n"
            for vacancy in groups['сценарист']:
                message += self._format_single_vacancy(vacancy)
            message += "\n"

        # Редакторы
        if groups['редактор']:
            message += "🎬 РЕДАКТОРЫ:\n\n"
            for vacancy in groups['редактор']:
                message += self._format_single_vacancy(vacancy)
            message += "\n"

        # Шеф-редакторы
        if groups['шеф-редактор']:
            message += "👔 ШЕФ-РЕДАКТОРЫ:\n\n"
            for vacancy in groups['шеф-редактор']:
                message += self._format_single_vacancy(vacancy)

        return message.strip()

    def _format_single_vacancy(self, vacancy):
        """Форматирует одну вакансию"""
        title = vacancy.get('title', 'Без названия')
        company = vacancy.get('company')
        url = vacancy.get('url', '')

        # Формат: Название — Компания
        if company:
            line = f"{title} — {company}\n"
        else:
            line = f"{title}\n"

        # Ссылка на отдельной строке
        if url:
            line += f"{url}\n"

        line += "\n"
        return line

    async def send_vacancies(self, vacancies):
        """
        Отправляет список вакансий всем пользователям

        Args:
            vacancies: List[dict] - список вакансий

        Returns:
            bool: True если отправка хотя бы одному пользователю успешна
        """
        if not self.bot:
            await self.initialize()

        message = self.format_vacancies_message(vacancies)
        success_count = 0

        # Отправляем каждому пользователю
        for username in self.target_usernames:
            try:
                chat_id = await self.get_chat_id(username)
                if not chat_id:
                    logger.error(
                        f"Cannot send message: chat_id not found for @{username}. "
                        f"User must send /start to the bot first."
                    )
                    continue

                # Telegram имеет лимит на длину сообщения (4096 символов)
                if len(message) > 4096:
                    # Разбиваем на части
                    await self._send_long_message(chat_id, message)
                else:
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        disable_web_page_preview=True
                    )

                logger.info(f"Vacancies sent to @{username} (chat_id: {chat_id})")

                # Сохраняем информацию об отправке
                await self._save_sent_vacancies(vacancies, username)

                success_count += 1

            except Forbidden:
                logger.error(f"Bot is blocked by user @{username}")
                continue

            except BadRequest as e:
                logger.error(f"Bad request sending message to @{username}: {e}")
                continue

            except TelegramError as e:
                logger.error(f"Telegram error sending to @{username}: {e}")
                continue

            except Exception as e:
                logger.error(f"Unexpected error sending message to @{username}: {e}")
                continue

        if success_count > 0:
            logger.info(f"Vacancies sent to {success_count}/{len(self.target_usernames)} users")
            return True
        else:
            logger.error("Failed to send vacancies to any user")
            return False

    async def _send_long_message(self, chat_id, message):
        """Отправка длинного сообщения частями"""
        max_length = 4096
        parts = []

        while message:
            if len(message) <= max_length:
                parts.append(message)
                break

            # Ищем последний перенос строки в пределах лимита
            split_index = message.rfind('\n\n', 0, max_length)
            if split_index == -1:
                split_index = max_length

            parts.append(message[:split_index])
            message = message[split_index:].lstrip()

        for i, part in enumerate(parts):
            await self.bot.send_message(
                chat_id=chat_id,
                text=part,
                disable_web_page_preview=True
            )
            if i < len(parts) - 1:
                await asyncio.sleep(0.5)  # Небольшая задержка между частями

    async def _save_sent_vacancies(self, vacancies, username):
        """Сохранить информацию об отправленных вакансиях"""
        session = get_session()
        saved_count = 0
        try:
            for vacancy_data in vacancies:
                # Находим вакансию в БД
                vacancy_hash = vacancy_data.get('hash')
                if not vacancy_hash:
                    continue

                vacancy = session.query(Vacancy).filter_by(hash=vacancy_hash).first()
                if not vacancy:
                    continue

                # Проверяем, не была ли вакансия уже отправлена этому пользователю
                existing_sent = session.query(SentVacancy).filter_by(
                    vacancy_id=vacancy.id,
                    sent_to=username
                ).first()

                if existing_sent:
                    logger.debug(f"Vacancy {vacancy.id} already sent to @{username}, skipping")
                    continue

                # Создаем запись об отправке
                sent = SentVacancy(
                    vacancy_id=vacancy.id,
                    sent_to=username
                )
                session.add(sent)
                saved_count += 1

            session.commit()
            logger.info(f"Saved {saved_count} sent vacancy records for @{username}")

        except Exception as e:
            session.rollback()
            logger.error(f"Error saving sent vacancies for @{username}: {e}")
        finally:
            close_session(session)


# Глобальный экземпляр
telegram_notifier = TelegramNotifier()
