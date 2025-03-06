import asyncio
import os
from typing import Optional, Union, Dict, Any

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

from middlewares.antiflood import AntiFloodMiddleware
from middlewares.private_chat import PrivateChatMiddleware
from middlewares.work_set import WorkSetMiddleware

from handlers.main_handler import router as main_router
from handlers.functions.shop_handler import router as shop_router
from handlers.functions.faq_handler import router as faq_router
from handlers.functions.support_handler import router as support_router
from handlers.functions.referral_system_handler import router as referral_router

load_dotenv()

default_setting = DefaultBotProperties(parse_mode='HTML')
bot = Bot(os.getenv("BOT_TOKEN"), default=default_setting)
dp = Dispatcher()

async def main() -> None:
    dp.message.middleware(PrivateChatMiddleware())
    # dp.message.middleware(AntiFloodMiddleware(limit=0.5))
    # dp.message.middleware(WorkSetMiddleware())
    
    dp.include_router(main_router)
    dp.include_router(shop_router)
    dp.include_router(faq_router)
    dp.include_router(support_router)
    dp.include_router(referral_router)
    
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, skip_updates=True)
    except Exception as e:
        print(f"Ошибка при запуске бота: {e}")
    finally:
        await bot.session.close()

if __name__ == '__main__':
    try:
        print("Бот стартовал :)")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен :(")
    except Exception as e:
        print(f"Произошла ошибка: {e}")