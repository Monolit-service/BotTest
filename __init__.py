from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.keyboards import donation_methods_keyboard, main_menu, plan_payment_keyboard, plans_keyboard
from app.services.plan_service import get_active_plans, get_plan_by_id
from app.services.user_service import get_or_create_user
from app.utils.text import format_welcome_text

router = Router()
settings = get_settings()


@router.message(CommandStart())
async def start_handler(message: Message, session: AsyncSession) -> None:
    user = message.from_user
    await get_or_create_user(
        session=session,
        telegram_id=user.id,
        username=user.username,
        full_name=user.full_name,
    )
    text = format_welcome_text(settings.channel_1_name, settings.channel_2_name)
    await message.answer(text, reply_markup=main_menu())


@router.callback_query(lambda c: c.data == "menu")
async def menu_handler(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        format_welcome_text(settings.channel_1_name, settings.channel_2_name),
        reply_markup=main_menu(),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "show_plans")
async def show_plans_handler(callback: CallbackQuery, session: AsyncSession) -> None:
    plans = await get_active_plans(session)
    await callback.message.edit_text("Выбери тариф:", reply_markup=plans_keyboard(plans))
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("plan:"))
async def plan_details_handler(callback: CallbackQuery, session: AsyncSession) -> None:
    plan_id = int(callback.data.split(":", maxsplit=1)[1])
    plan = await get_plan_by_id(session, plan_id)
    if plan is None or not plan.is_active:
        await callback.answer("Тариф не найден или отключён", show_alert=True)
        return

    text = (
        f"<b>{plan.title}</b>\n\n"
        f"{plan.description}\n\n"
        f"Срок: {plan.duration_days} дней\n"
        f"Цена в Telegram: {plan.price_xtr} ⭐\n\n"
        "Выбери способ оплаты:"
    )
    await callback.message.edit_text(text, reply_markup=plan_payment_keyboard(plan))
    await callback.answer()


@router.callback_query(lambda c: c.data == "show_donations")
async def donations_handler(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "Поддержать проект можно звёздами внутри Telegram или через CryptoBot.",
        reply_markup=donation_methods_keyboard(),
    )
    await callback.answer()
