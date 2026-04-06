from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChannelScope, Plan

DEFAULT_PLANS = [
    {
        "code": "ch1_30",
        "title": "Канал 1 — 30 дней",
        "description": "Доступ к первому приватному каналу на 30 дней",
        "channel_scope": ChannelScope.CHANNEL_1,
        "duration_days": 30,
        "price_xtr": 250,
    },
    {
        "code": "ch2_30",
        "title": "Канал 2 — 30 дней",
        "description": "Доступ ко второму приватному каналу на 30 дней",
        "channel_scope": ChannelScope.CHANNEL_2,
        "duration_days": 30,
        "price_xtr": 250,
    },
    {
        "code": "bundle_30",
        "title": "Оба канала — 30 дней",
        "description": "Доступ к двум приватным каналам на 30 дней",
        "channel_scope": ChannelScope.BUNDLE,
        "duration_days": 30,
        "price_xtr": 450,
    },
]


async def seed_plans(session: AsyncSession) -> None:
    for item in DEFAULT_PLANS:
        existing = await session.scalar(select(Plan).where(Plan.code == item["code"]))
        if existing is None:
            session.add(Plan(**item))
    await session.commit()
