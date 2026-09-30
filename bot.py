import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from config import BOT_TOKEN
from handlers.bot_handlers import router
from alerts import check_alerts_loop

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)


async def set_main_menu(bot: Bot):
    """Sets up Telegram's native command menu button."""
    commands = [
        BotCommand(command="start", description="🚀 Запустить бота / Start bot"),
        BotCommand(command="price", description="📊 Дашборд / Dashboard"),
        BotCommand(command="pairs", description="💱 Валютные пары / Pairs"),
        BotCommand(command="alerts", description="🔔 Алерты по цене / Price Alerts"),
        BotCommand(command="settings", description="⚙️ Настройки языка / Language"),
        BotCommand(command="help", description="❓ Справка / Help"),
    ]
    await bot.set_my_commands(commands)


async def main():
    logging.info("Starting Forex Analytics Telegram Bot...")
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Set up Telegram UI Menu Commands
    await set_main_menu(bot)

    # Register handlers router
    dp.include_router(router)

    # Start background Price Alert monitoring loop
    asyncio.create_task(check_alerts_loop(bot))

    # Drop any pending updates and start polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped.")
