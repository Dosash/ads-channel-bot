"""Минимальный клиент Crypto Pay API (@CryptoBot)."""
from typing import Any

import aiohttp

from bot.config import config


class CryptoPayError(Exception):
    pass


class CryptoPay:
    def __init__(self, token: str, testnet: bool = False):
        self.token = token
        host = "testnet-pay.crypt.bot" if testnet else "pay.crypt.bot"
        self.base = f"https://{host}/api/"

    async def _call(self, method: str, **params: Any) -> Any:
        params = {k: v for k, v in params.items() if v is not None}
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as s:
            async with s.post(self.base + method, json=params,
                              headers={"Crypto-Pay-API-Token": self.token}) as r:
                data = await r.json(content_type=None)
        if not data.get("ok"):
            raise CryptoPayError(str(data.get("error")))
        return data["result"]

    async def create_invoice(self, amount_usd: float, description: str, payload: str,
                             expires_in: int = 24 * 3600) -> dict:
        # Счёт в долларах — пользователь сам выбирает, какой криптой платить
        return await self._call(
            "createInvoice",
            currency_type="fiat",
            fiat="USD",
            amount=f"{amount_usd:.2f}",
            description=description[:1024],
            payload=payload,
            allow_comments=False,
            allow_anonymous=True,
            expires_in=int(expires_in),
        )

    async def get_invoices(self, invoice_ids: list[int]) -> list[dict]:
        if not invoice_ids:
            return []
        res = await self._call("getInvoices", invoice_ids=",".join(map(str, invoice_ids)))
        return res.get("items", [])


cryptopay = CryptoPay(config.cryptopay_token, config.cryptopay_testnet)
# Для тестовых заказов: тестовая сеть @CryptoTestnetBot (ненастоящие монеты), если задан токен
cryptopay_test = CryptoPay(config.cryptopay_test_token, testnet=True) if config.cryptopay_test_token else None


def client_for(order) -> CryptoPay | None:
    """Клиент CryptoPay для заказа. None — для тестового заказа без testnet-токена."""
    if order["is_test"]:
        return cryptopay_test
    return cryptopay
