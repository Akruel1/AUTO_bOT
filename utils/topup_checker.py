import asyncio
from sqlalchemy import select, update
from datetime import datetime, timedelta
import aiohttp

from config import LTC_API_URL, LTC_WALLET
from database import async_session
from models.models import TopUpRequest, User

CHECK_INTERVAL = 60  # секунд

async def check_topups():
    while True:
        try:
            async with async_session() as session:
                # Получаем все ожидающие заявки
                result = await session.execute(
                    select(TopUpRequest).where(TopUpRequest.status == "waiting")
                )
                requests = result.scalars().all()

                if not requests:
                    await asyncio.sleep(CHECK_INTERVAL)
                    continue

                # Получаем список транзакций через API
                async with aiohttp.ClientSession() as http:
                    async with http.get(f"{LTC_API_URL}/wallet/{LTC_WALLET}/transactions") as resp:
                        data = await resp.json()
                        transactions = data.get("txs", [])

                for req in requests:
                    for tx in transactions:
                        amount = float(tx.get("amount", 0))
                        to_address = tx.get("to", "")
                        timestamp = datetime.fromtimestamp(tx.get("timestamp", 0))

                        if to_address == LTC_WALLET and abs(amount - req.expected_ltc) < 0.0001:
                            # Успешное пополнение
                            req.status = "confirmed"
                            req.timestamp = datetime.utcnow()

                            user = await session.get(User, req.user_id)
                            user.balance_usd += req.amount_usd

                            await session.commit()
                            break

        except Exception as e:
            print("Ошибка при проверке пополнений:", e)

        await asyncio.sleep(CHECK_INTERVAL)
