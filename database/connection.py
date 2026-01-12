from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from config.settings import settings
from config.logging_config import get_logger

logger = get_logger(__name__)

# Создание engine с connection pooling
engine = None
SessionLocal = None


def init_database():
    """Инициализация подключения к базе данных"""
    global engine, SessionLocal

    if not settings.DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is not set")

    logger.info("Initializing database connection...")

    # Создаем engine с настройками для Render PostgreSQL
    engine = create_engine(
        settings.DATABASE_URL,
        poolclass=QueuePool,
        pool_size=5,                    # Количество постоянных соединений
        max_overflow=10,                # Дополнительные соединения при необходимости
        pool_timeout=30,                # Таймаут получения соединения из пула
        pool_recycle=3600,              # Пересоздание соединений каждый час
        pool_pre_ping=True,             # Проверка соединения перед использованием
        echo=False                      # Не логировать SQL запросы
    )

    # Создаем фабрику сессий
    session_factory = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )

    # Scoped session для thread-safety
    SessionLocal = scoped_session(session_factory)

    logger.info("Database connection initialized successfully")

    return engine


def get_session():
    """Получить новую сессию БД"""
    if SessionLocal is None:
        init_database()

    return SessionLocal()


def close_session(session):
    """Закрыть сессию БД"""
    if session:
        session.close()


def get_db():
    """
    Context manager для работы с сессией БД
    Использование:
        with get_db() as db:
            # работа с БД
            pass
    """
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        close_session(session)


def close_database():
    """Закрытие всех подключений к БД"""
    global engine
    if engine:
        logger.info("Closing database connections...")
        engine.dispose()
        logger.info("Database connections closed")
