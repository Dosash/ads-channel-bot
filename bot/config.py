import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    bot_token: str
    cryptopay_token: str
    cryptopay_testnet: bool
    admin_ids: tuple[int, ...]
    db_path: str
    test_channel_id: int | None
    cryptopay_test_token: str
    timezone: str
    work_start: int          # первый слот дня (час)
    work_end: int            # последний слот дня (час)
    booking_days: int        # на сколько дней вперёд можно бронировать
    min_lead_minutes: int    # минимум до времени публикации при бронировании
    xrocket_token: str
    panel_host: str
    panel_port: int          # 0 — панель выключена
    panel_prefix: str        # путь панели за nginx хаба, например /ads
    panel_password: str      # пусто — без логина (как у соседних панелей в LAN)


def load_config() -> Config:
    admins = tuple(int(x) for x in os.getenv("ADMIN_IDS", "").replace(" ", "").split(",") if x)
    return Config(
        bot_token=os.environ["BOT_TOKEN"],
        cryptopay_token=os.getenv("CRYPTOPAY_TOKEN", ""),
        cryptopay_testnet=os.getenv("CRYPTOPAY_TESTNET", "false").lower() == "true",
        admin_ids=admins,
        db_path=os.getenv("DB_PATH", "data/bot.db"),
        test_channel_id=int(os.getenv("TEST_CHANNEL_ID")) if os.getenv("TEST_CHANNEL_ID") else None,
        cryptopay_test_token=os.getenv("CRYPTOPAY_TESTNET_TOKEN", ""),
        timezone=os.getenv("TIMEZONE", "Europe/Moscow"),
        work_start=int(os.getenv("WORK_HOURS", "9-22").split("-")[0]),
        work_end=int(os.getenv("WORK_HOURS", "9-22").split("-")[1]),
        booking_days=int(os.getenv("BOOKING_DAYS", "14")),
        min_lead_minutes=int(os.getenv("MIN_LEAD_MINUTES", "60")),
        xrocket_token=os.getenv("XROCKET_TOKEN", ""),
        panel_host=os.getenv("PANEL_HOST", "0.0.0.0"),
        panel_port=int(os.getenv("PANEL_PORT", "8093")),
        panel_prefix="/" + os.getenv("PANEL_PREFIX", "/ads").strip("/"),
        panel_password=os.getenv("PANEL_PASSWORD", ""),
    )


config = load_config()
