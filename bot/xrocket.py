"""Клиент xRocket Pay API (https://docs.xrocket.exchange/api/pay/pay-api-overview).

Авторизация — Bearer-токен приложения из @xRocket → Rocket Pay → приложение → API Token.
"""
from typing import Any

import aiohttp

from bot.config import config


class XRocketError(Exception):
    pass


class XRocket:
    def __init__(self, token: str, testnet: bool = False):
        self.token = token
        host = "pay.api.testnet.xrocket.exchange" if testnet else "pay.api.xrocket.exchange"
        self.base = f"https://{host}/api/v1/"
        self.verified = False   # ключ проверен при старте (verify)

    @property
    def enabled(self) -> bool:
        return bool(self.token) and self.verified

    async def _call(self, method: str, path: str, *, params: dict | None = None, json: dict | None = None) -> Any:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as s:
            async with s.request(method, self.base + path, params=params, json=json,
                                 headers={"Authorization": f"Bearer {self.token}",
                                          "Accept": "application/json"}) as r:
                data = await r.json(content_type=None) if r.content_length != 0 else {}
                if r.status >= 400:
                    detail = (data or {}).get("detail") or (data or {}).get("title") or r.reason
                    raise XRocketError(f"{r.status}: {detail}")
        return data

    async def verify(self) -> str | None:
        """Проверяет ключ. Возвращает текст ошибки или None, если всё в порядке."""
        if not self.token:
            return "XROCKET_TOKEN не задан"
        try:
            await self._call("GET", "app-info")
        except (XRocketError, aiohttp.ClientError, TimeoutError, ValueError) as e:
            self.verified = False
            return str(e)
        self.verified = True
        return None

    def setup(self, token: str) -> None:
        """Новый токен из веб-панели; включится после verify()."""
        self.token = token
        self.verified = False

    async def create_invoice(self, amount_usd: float, description: str, client_id: str,
                             expires_in: int = 24 * 3600) -> dict:
        """Счёт в USDT (1 USDT ≈ 1 $). Оплатить можно любой криптой из кошелька xRocket.

        client_id делает повторную отправку безопасной: тот же client_id второй счёт не создаст.
        """
        return await self._call("POST", "invoices", json={
            "priceAmount": f"{amount_usd:.2f}",
            "priceCurrency": "USDT",
            "numPayments": 1,
            "description": description[:1000],
            "clientInvoiceId": client_id,
            "expiresIn": int(expires_in) * 1000,      # API ждёт миллисекунды
        })

    async def paid_ids(self, limit: int = 100) -> set[str]:
        """ID последних оплаченных счетов — одним запросом (у API лимит 20 запросов в минуту)."""
        data = await self._call("GET", "invoices", params={"status": "paid", "limit": str(limit)})
        return {str(inv["id"]) for inv in data.get("items", [])}

    async def get_invoice(self, invoice_id: str | int) -> dict:
        return await self._call("GET", "invoice", params={"invoiceId": str(invoice_id)})


xrocket = XRocket(config.xrocket_token)
