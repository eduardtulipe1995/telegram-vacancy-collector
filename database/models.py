from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean,
    BigInteger, DateTime, ForeignKey, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Channel(Base):
    """Telegram каналы для мониторинга"""
    __tablename__ = 'channels'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    username = Column(String(255), unique=True, nullable=False, index=True)
    enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_checked = Column(DateTime)

    # Relationships
    vacancies = relationship('Vacancy', back_populates='channel')

    def __repr__(self):
        return f"<Channel(id={self.id}, username='{self.username}', enabled={self.enabled})>"


class Vacancy(Base):
    """Найденные вакансии"""
    __tablename__ = 'vacancies'

    id = Column(Integer, primary_key=True)
    channel_id = Column(Integer, ForeignKey('channels.id'), nullable=False)
    message_id = Column(BigInteger)
    title = Column(Text, nullable=False)
    company = Column(String(255))
    url = Column(Text)
    position_type = Column(String(50))  # 'сценарист', 'редактор', 'шеф-редактор'
    full_text = Column(Text)
    hash = Column(String(64), unique=True, nullable=False, index=True)
    found_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    channel = relationship('Channel', back_populates='vacancies')
    sent_records = relationship('SentVacancy', back_populates='vacancy')

    # Indexes
    __table_args__ = (
        Index('idx_vacancy_found_at', 'found_at'),
        Index('idx_vacancy_url', 'url'),
    )

    def __repr__(self):
        return f"<Vacancy(id={self.id}, title='{self.title[:30]}...', type='{self.position_type}')>"


class SentVacancy(Base):
    """История отправленных вакансий"""
    __tablename__ = 'sent_vacancies'

    id = Column(Integer, primary_key=True)
    vacancy_id = Column(Integer, ForeignKey('vacancies.id'), nullable=False)
    sent_to = Column(String(255), nullable=False)  # username получателя
    sent_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    vacancy = relationship('Vacancy', back_populates='sent_records')

    def __repr__(self):
        return f"<SentVacancy(id={self.id}, vacancy_id={self.vacancy_id}, sent_to='{self.sent_to}')>"


class JobRun(Base):
    """История запусков джобов сбора вакансий"""
    __tablename__ = 'job_runs'

    id = Column(Integer, primary_key=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    status = Column(String(50))  # 'running', 'completed', 'failed'
    vacancies_found = Column(Integer, default=0)
    vacancies_sent = Column(Integer, default=0)
    error_message = Column(Text)

    def __repr__(self):
        return f"<JobRun(id={self.id}, status='{self.status}', found={self.vacancies_found}, sent={self.vacancies_sent})>"


class UserChatID(Base):
    """Хранение chat_id пользователей для отправки уведомлений"""
    __tablename__ = 'user_chat_ids'

    id = Column(Integer, primary_key=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    chat_id = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<UserChatID(username='{self.username}', chat_id={self.chat_id})>"
