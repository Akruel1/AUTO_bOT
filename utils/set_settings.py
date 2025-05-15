# utils/settings.py
from sqlalchemy import select, update
from database import async_session
from models.models import Settings


async def set_setting(key: str, value: str):
    async with async_session() as session:
        result = await session.execute(select(Settings).where(Settings.key == key))
        existing = result.scalar_one_or_none()

        if existing:
            await session.execute(update(Settings).where(Settings.key == key).values(value=value))
        else:
            session.add(Settings(key=key, value=value))
        await session.commit()


async def get_setting(key: str) -> str | None:
    async with async_session() as session:
        result = await session.execute(select(Settings).where(Settings.key == key))
        setting = result.scalar_one_or_none()
        return setting.value if setting else None
