import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from bot import db
from bot.channel_info import refresh_loop
from bot.config import config
from bot import broadcast
from bot.handlers import admin, audience, payments, support, user
from bot import ui
from bot.orders import crypto_poll_loop, scheduler_loop
from bot.web import start_panel


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    await db.init_db()

    bot = Bot(config.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    # порядок важен: аудитория (блокировки, пост для рассылки) → админка → оплата → пользовательские сценарии (там же «ловушка» прочих сообщений)
    dp.message.outer_middleware(audience.TouchUser())
    dp.callback_query.outer_middleware(audience.TouchUser())
    dp.include_routers(audience.router, admin.router, support.admin_router, admin.events, payments.router,
                       support.user_router, user.router)

    ui.BOT_USERNAME = (await bot.me()).username
    from bot.xrocket import xrocket
    err = await xrocket.verify()
    if err:
        logging.warning("xRocket Pay отключён: %s", err)
    else:
        logging.info("xRocket Pay подключён")
    await bot.set_my_commands([BotCommand(command="start", description="Главное меню / Main menu"),
                               BotCommand(command="lang", description="Язык / Language")])

    panel = await start_panel(bot)
    tasks = [
        asyncio.create_task(crypto_poll_loop(bot)),
        asyncio.create_task(refresh_loop(bot)),
        asyncio.create_task(scheduler_loop(bot)),
        asyncio.create_task(admin.discovery_report_loop(bot)),
        broadcast.resume_all(bot),
    ]
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        for t in tasks:
            t.cancel()
        if panel:
            await panel.cleanup()
        await db.close_db()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
