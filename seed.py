from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.config import get_settings
from app.models import Plan
from app.services.payment_service import crypto_price_for_plan

settings = get_settings()


def main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Тарифы", callback_data="show_plans")
    builder.button(text="👤 Мой профиль", callback_data="my_profile")
    builder.button(text="⭐ Донат звёздами", callback_data="donate:stars")
    builder.button(text="💝 Донаты", callback_data="show_donations")
    builder.adjust(1)
    return builder.as_markup()


def plans_keyboard(plans: list[Plan]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for plan in plans:
        builder.button(
            text=f"{plan.title} — {plan.price_xtr} ⭐",
            callback_data=f"plan:{plan.id}",
        )
    builder.button(text="👤 Мой профиль", callback_data="my_profile")
    builder.button(text="⭐ Донат звёздами", callback_data="donate:stars")
    builder.button(text="💝 Донаты", callback_data="show_donations")
    builder.adjust(1)
    return builder.as_markup()


def plan_payment_keyboard(plan: Plan) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=f"⭐ Оплатить за {plan.price_xtr} XTR", callback_data=f"buy_stars:{plan.id}")
    if settings.crypto_pay_enabled:
        crypto_price = crypto_price_for_plan(plan)
        builder.button(
            text=f"🪙 CryptoBot · {crypto_price} {settings.crypto_pay_asset}",
            callback_data=f"buy_crypto:{plan.id}",
        )
    builder.button(text="⬅️ К тарифам", callback_data="show_plans")
    builder.button(text="👤 Мой профиль", callback_data="my_profile")
    builder.adjust(1)
    return builder.as_markup()


def crypto_invoice_keyboard(pay_url: str, payment_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🪙 Открыть счёт CryptoBot", url=pay_url)
    builder.button(text="✅ Проверить оплату", callback_data=f"check_crypto:{payment_id}")
    builder.button(text="⬅️ К тарифам", callback_data="show_plans")
    builder.adjust(1)
    return builder.as_markup()


def donation_methods_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⭐ Донат звёздами", callback_data="donate:stars")
    if settings.crypto_pay_enabled:
        builder.button(text="🪙 Донат через CryptoBot", callback_data="donate:crypto")
    if settings.donate_url:
        builder.button(text="🔗 Внешняя ссылка на донат", url=settings.donate_url)
    builder.button(text="⬅️ В меню", callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()


def donation_amounts_keyboard(method: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if method == "stars":
        for amount in settings.donate_xtr_amounts:
            builder.button(text=f"{amount} ⭐", callback_data=f"donate_stars:{amount}")
    elif method == "crypto":
        for amount in settings.donate_crypto_amounts:
            builder.button(
                text=f"{amount} {settings.crypto_pay_asset}",
                callback_data=f"donate_crypto:{amount}",
            )
    builder.button(text="⬅️ Назад", callback_data="show_donations")
    builder.adjust(2)
    return builder.as_markup()


def crypto_donation_keyboard(pay_url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🪙 Открыть донат-счёт", url=pay_url)
    builder.button(text="⬅️ К донатам", callback_data="show_donations")
    builder.adjust(1)
    return builder.as_markup()


def profile_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Купить/продлить", callback_data="show_plans")
    builder.button(text="⭐ Донат звёздами", callback_data="donate:stars")
    builder.button(text="💝 Донаты", callback_data="show_donations")
    builder.button(text="🔄 Обновить профиль", callback_data="my_profile")
    builder.adjust(1)
    return builder.as_markup()


def after_purchase_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="👤 Мой профиль", callback_data="my_profile")
    builder.button(text="💳 Купить ещё", callback_data="show_plans")
    builder.button(text="⭐ Донат звёздами", callback_data="donate:stars")
    builder.button(text="💝 Донаты", callback_data="show_donations")
    builder.adjust(1)
    return builder.as_markup()
