from __future__ import annotations

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from uuid import uuid4

import httpx
from aiogram.types import LabeledPrice, Message, PreCheckoutQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import Payment, PaymentMethod, PaymentStatus, Plan, User

settings = get_settings()


def crypto_price_for_plan(plan: Plan) -> str:
    amount = (Decimal(plan.price_xtr) * Decimal(str(settings.crypto_usdt_per_star))).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    if amount <= 0:
        amount = Decimal("0.01")
    return format(amount, "f")


async def create_pending_payment(
    session: AsyncSession,
    user: User,
    plan: Plan,
    payment_method: PaymentMethod = PaymentMethod.STARS,
) -> Payment:
    payload = f"sub:{payment_method}:{user.telegram_id}:{plan.id}:{uuid4().hex[:12]}"
    payment = Payment(
        user_id=user.id,
        plan_id=plan.id,
        payload=payload,
        payment_method=payment_method,
        amount_xtr=plan.price_xtr,
        status=PaymentStatus.PENDING,
    )
    session.add(payment)
    await session.commit()
    await session.refresh(payment)
    return payment


async def send_plan_invoice(message: Message, payment: Payment, plan: Plan) -> None:
    prices = [LabeledPrice(label=plan.title, amount=plan.price_xtr)]
    await message.answer_invoice(
        title=plan.title,
        description=plan.description,
        payload=payment.payload,
        currency="XTR",
        prices=prices,
        provider_token="",
        start_parameter=plan.code,
    )


async def send_donation_invoice(message: Message, stars_amount: int) -> None:
    payload = f"donate:stars:{message.from_user.id}:{stars_amount}:{uuid4().hex[:8]}"
    prices = [LabeledPrice(label=f"Донат {stars_amount} ⭐", amount=stars_amount)]
    await message.answer_invoice(
        title="Поддержать проект",
        description="Спасибо за донат ❤️",
        payload=payload,
        currency="XTR",
        prices=prices,
        provider_token="",
        start_parameter=f"donate_{stars_amount}",
    )


async def approve_pre_checkout(pre_checkout_query: PreCheckoutQuery) -> None:
    await pre_checkout_query.answer(ok=True)


async def mark_payment_paid(
    session: AsyncSession,
    payload: str,
    telegram_payment_charge_id: str | None,
    provider_payment_charge_id: str | None,
) -> tuple[Payment | None, bool]:
    payment = await session.scalar(select(Payment).where(Payment.payload == payload))
    if payment is None:
        return None, False

    if payment.status == PaymentStatus.PAID:
        return payment, False

    payment.status = PaymentStatus.PAID
    payment.telegram_payment_charge_id = telegram_payment_charge_id
    payment.provider_payment_charge_id = provider_payment_charge_id
    payment.paid_at = datetime.utcnow()
    await session.commit()
    await session.refresh(payment)
    return payment, True


async def get_payment_by_id(session: AsyncSession, payment_id: int) -> Payment | None:
    return await session.get(Payment, payment_id)


async def create_crypto_invoice_for_payment(session: AsyncSession, payment: Payment, plan: Plan) -> str:
    if not settings.crypto_pay_enabled:
        raise RuntimeError("Crypto Pay token is not configured")

    url = f"{settings.crypto_pay_base_url.rstrip('/')}/createInvoice"
    amount = crypto_price_for_plan(plan)
    payload = {
        "asset": settings.crypto_pay_asset,
        "amount": amount,
        "description": f"Оплата подписки: {plan.title}",
        "hidden_message": "Спасибо за оплату. Вернись в бота и нажми «Проверить оплату», если доступ ещё не выдался.",
        "payload": payment.payload,
        "paid_btn_name": "openBot",
        "paid_btn_url": f"https://t.me/{settings.bot_username}",
        "allow_comments": False,
        "allow_anonymous": True,
        "expires_in": 3600,
    }
    headers = {
        "Crypto-Pay-API-Token": settings.crypto_pay_token,
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    result = data.get("result") or {}
    invoice_id = result.get("invoice_id")
    pay_url = result.get("bot_invoice_url") or result.get("pay_url")
    if not invoice_id or not pay_url:
        raise RuntimeError("Crypto Pay did not return invoice data")

    payment.provider_payment_charge_id = str(invoice_id)
    await session.commit()
    return pay_url


async def create_crypto_donation_invoice(amount: str) -> str:
    if not settings.crypto_pay_enabled:
        raise RuntimeError("Crypto Pay token is not configured")

    url = f"{settings.crypto_pay_base_url.rstrip('/')}/createInvoice"
    payload = {
        "asset": settings.crypto_pay_asset,
        "amount": amount,
        "description": "Донат проекту",
        "hidden_message": "Спасибо за донат ❤️",
        "paid_btn_name": "openBot",
        "paid_btn_url": f"https://t.me/{settings.bot_username}",
        "allow_comments": False,
        "allow_anonymous": True,
        "expires_in": 3600,
    }
    headers = {
        "Crypto-Pay-API-Token": settings.crypto_pay_token,
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    result = data.get("result") or {}
    pay_url = result.get("bot_invoice_url") or result.get("pay_url")
    if not pay_url:
        raise RuntimeError("Crypto Pay did not return invoice URL")
    return pay_url


async def get_crypto_invoice(invoice_id: str) -> dict | None:
    if not settings.crypto_pay_enabled:
        return None

    url = f"{settings.crypto_pay_base_url.rstrip('/')}/getInvoices"
    headers = {"Crypto-Pay-API-Token": settings.crypto_pay_token}
    params = {"invoice_ids": invoice_id, "count": 1}

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

    invoices = data.get("result", {}).get("items") or data.get("result") or []
    if isinstance(invoices, dict):
        invoices = invoices.get("items") or []
    return invoices[0] if invoices else None


async def sync_crypto_payment_status(session: AsyncSession, payment: Payment) -> tuple[Payment | None, bool]:
    if payment.payment_method != PaymentMethod.CRYPTOBOT:
        return payment, False
    if not payment.provider_payment_charge_id:
        return payment, False

    invoice = await get_crypto_invoice(payment.provider_payment_charge_id)
    if not invoice:
        return payment, False

    status = str(invoice.get("status", "")).lower()
    if status != "paid":
        return payment, False

    provider_charge_id = str(invoice.get("invoice_id") or payment.provider_payment_charge_id)
    return await mark_payment_paid(
        session=session,
        payload=payment.payload,
        telegram_payment_charge_id=None,
        provider_payment_charge_id=provider_charge_id,
    )
