import os

import asyncio
from aiogram import Bot, Dispatcher, types
import logging

from app.handlers.user_handlers import user_router
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import asyncio
import app.core.reservation_service as reserv_service
from app.handlers.admin_handlers import admin_router
from app.database.models import async_main
from app.core.entities_service import get_core_entities

dp = Dispatcher()
# Базовая конфигурация логгера
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)


@dp.errors()
async def error_handler(error: types.ErrorEvent):
    print(f'Update: {error.update} \nException: {error.exception}')

    # Отправка пользовательского сообщения в случае ошибки
    if error.update.message:
        await error.update.message.answer("Произошла ошибка, пожалуйста, попробуйте позже.")
    
    # Возвращаем True, чтобы сообщить диспетчеру, что ошибка была обработана
    return True


async def main():
    global dp

    await async_main()
    await get_core_entities()
    os.makedirs("photo", exist_ok=True)
    bot = Bot(token = '7027121616:AAG0yE9RfLbdQABzKzW0rtiI447bGvsac6E')

    dp.include_router(user_router)
    dp.include_router(admin_router)

    scheduler = AsyncIOScheduler()
    
    # Добавление задания с использованием Cron триггера для запуска каждые 30 минут (в 00 и 30 минуты каждого часа)
    scheduler.add_job(reserv_service.check_upcoming_reservations,
                      trigger=CronTrigger(minute='30, 0'), kwargs={'bot': bot})
    
    # Запуск планировщика
    scheduler.start()



    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        logger.info("Starting bot")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Stopping bot")
