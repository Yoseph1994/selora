import asyncio
import logging
import sys
import uvicorn
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

import config
from handlers import start, admin, catalog, delivery, order, track, business, ai_chat
from dashboard.app import app as fastapi_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("selora_bot")

async def set_bot_commands(bot: Bot):
    """Register menu commands visible in Telegram UI."""
    commands = [
        BotCommand(command="start", description="💛 Welcome menu"),
        BotCommand(command="catalog", description="🏷 Products & Prices"),
        BotCommand(command="order", description="📝 Place an order (50% deposit)"),
        BotCommand(command="track", description="🔍 Track your order status"),
        BotCommand(command="delivery", description="📍 Delivery & Pickup info"),
        BotCommand(command="contact", description="📞 Contact the owner"),
        BotCommand(command="admin", description="👑 Owner control center"),
        BotCommand(command="help", description="💡 Bot guide"),
        BotCommand(command="cancel", description="❌ Cancel current order")
    ]
    await bot.set_my_commands(commands)

def find_available_port(start_port: int = 8000, max_attempts: int = 10) -> int:
    import socket
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
    return start_port

async def run_dashboard():
    """Run dynamic web dashboard on background server with automatic port recovery."""
    target_port = find_available_port(config.DASHBOARD_PORT)
    if target_port != config.DASHBOARD_PORT:
        logger.warning(f"⚠️ Port {config.DASHBOARD_PORT} was occupied, running Dashboard on port {target_port}")

    logger.info(f"🌐 Dynamic Web Dashboard is LIVE at: http://localhost:{target_port}")
    uvicorn_config = uvicorn.Config(
        app=fastapi_app,
        host=config.DASHBOARD_HOST,
        port=target_port,
        log_level="warning"
    )
    server = uvicorn.Server(uvicorn_config)
    await server.serve()

async def run_bot():
    """Run Telegram bot polling."""
    if not config.BOT_TOKEN or config.BOT_TOKEN == "your_telegram_bot_token_here":
        logger.warning(
            "\n" + "=" * 60 + "\n"
            "⚠️ BOT_TOKEN is not configured in .env yet.\n"
            "The Telegram Bot is paused, but the Web Dashboard is LIVE at:\n"
            f"👉 http://localhost:{config.DASHBOARD_PORT}\n\n"
            "When ready, add your BOT_TOKEN from @BotFather into .env and restart!\n"
            + "=" * 60 + "\n"
        )
        # Keep web server alive even if bot token is not set yet
        while True:
            await asyncio.sleep(3600)

    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Register routers in priority order
    dp.include_router(start.router)
    dp.include_router(admin.router)
    dp.include_router(catalog.router)
    dp.include_router(delivery.router)
    dp.include_router(order.router)
    dp.include_router(track.router)
    dp.include_router(business.router)
    dp.include_router(ai_chat.router)  # Fallback router must be registered last

    try:
        bot_info = await bot.get_me()
        logger.info(f"🚀 Telegram Bot started successfully as @{bot_info.username} ({bot_info.first_name})!")
        logger.info("💛 Selora Prints Bot is now online and listening for messages & orders...")
        
        await set_bot_commands(bot)
        
        # Drop pending updates and start polling
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error(f"Error in Telegram bot: {e}", exc_info=True)
    finally:
        await bot.session.close()

async def main():
    # Run both the Web Dashboard and the Telegram Bot concurrently
    await asyncio.gather(
        run_dashboard(),
        run_bot()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Selora service stopped.")
