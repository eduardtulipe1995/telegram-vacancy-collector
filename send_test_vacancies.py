#!/usr/bin/env python3
"""
Скрипт для быстрой отправки вакансий пользователю
"""
import asyncio
from scheduler.job_scheduler import run_vacancy_collection

if __name__ == '__main__':
    print("Starting vacancy collection and sending...")
    asyncio.run(run_vacancy_collection())
    print("Done!")
