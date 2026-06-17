import asyncio
import logging
import signal

from pyrogram import Client

from config import get_settings
from database.session import init_db
from handlers.source_watcher import register_user_handlers
from utils.logger import setup_logging

logger = logging.getLogger(__name__)


def build_clients() -> tuple[Client, Client]:
    s = get_settings()

    if not s.session_string:
        raise RuntimeError(
            "SESSION_STRING empty"
        )

    user_client = Client(
        name="user_session",
        api_id=s.api_id,
        api_hash=s.api_hash,
        session_string=s.session_string,
        no_updates=False,
        in_memory=True,
    )

    bot_client = Client(
        name="bot_session",
        api_id=s.api_id,
        api_hash=s.api_hash,
        bot_token=s.bot_token,
        no_updates=True,
        in_memory=True,
    )

    # пробрасываем бота в user , чтобы хендлер мог публиковать
    user_client.bot_client = bot_client
    register_user_handlers(user_client)

    return user_client, bot_client


async def main() -> None:
    s = get_settings()
    setup_logging(s.log_level)

    logger.info("Инициализация БД...")
    await init_db()

    user_client, bot_client = build_clients()

    logger.info("Запуск user (чтение каналов)")
    await user_client.start()
    logger.info("Запуск bot (публикация)")
    await bot_client.start()

    logger.info("Сервис запущен. Слежу за каналами: %s", s.source_channels)
    logger.info("Целевой канал: %s", s.target_channel)

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except NotImplementedError:
            pass

    try:
        await stop_event.wait()
    finally:
        logger.info("Останавливаюсь")
        await bot_client.stop()
        await user_client.stop()
        logger.info("Остановлено")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
