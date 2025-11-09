import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import os
from loguru import logger

from app.handlers import start , menu , payment_receipt



from app.services.database import init_db

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

logger.add("logs/bot.log", level=LOG_LEVEL, rotation="10 MB", compression="zip")

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher(storage=MemoryStorage())


async def main():
    # Initialize database
    await init_db()

    # Register handlers
    dp.include_router(start.router)
    dp.include_router(menu.router)
    dp.include_router(payment_receipt.router)


    logger.info("🤖 Bot started successfully...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("🚫 Bot stopped manually.")
