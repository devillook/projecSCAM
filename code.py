"""
🏴‍☠️ Гарант-бот: безопасные сделки, бланки резюме и система арбитража.
"""

import asyncio
import datetime
import logging
import os
import random
import re

print(">>> 🌑 Инициализация теневых систем...")

try:
    from aiogram import Bot, Dispatcher, F, types
    from aiogram.filters import Command, StateFilter
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.state import State, StatesGroup
    from aiogram.types import (
        FSInputFile,
        InlineKeyboardButton,
        InlineKeyboardMarkup,
        KeyboardButton,
        InputMediaPhoto,
        ReplyKeyboardMarkup,
    )
    from aiohttp import web

    print(">>> 🕷️ Зависимости aiogram и aiohttp успешно загружены!")
except ImportError as e:
    print(f">>> ⚠️ ОШИБКА: Модули не найдены! Детали: {e}")
    exit(1)

# ──────────────────────── CONFIG ──────────────────────────
TG_BOT_TOKEN = "8848474277:AAHQ82X-lQKK6OXKJ-NmS8DizhMwAdPdHlQ"
ADMIN_CHAT_ID = 985669697
SUPPORT_USERNAME = "codcry"

GUARANTORS = [
    ("arkovh", 11.25),
    ("codcry", 55.00),
    ("hyppergamy", 11.25),
    ("hightwear", 11.25),
    ("Inarkav", 11.25),
]
_weights = [w for _, w in GUARANTORS]
_total = sum(_weights)
NORMALIZED = [(n, w / _total) for n, w in GUARANTORS]
NAMES = [n for n, _ in NORMALIZED]

PROFANITY_WORDS = [
    "хуй",
    "пизд",
    "еб",
    "eb",
    "хуе",
    "бля",
    "сук",
    "мраз",
    "сволоч",
    "гандон",
    "долбо",
    "идио",
    "дебил",
    "залуп",
    "шлюх",
    "сука",
    "ебал",
    "хуесос",
    "шлюха",
    "уеб",
    "блять",
    "нахуй", "похуй", "залупа", "мама", "твоя", "иди", "соси", "хз", "зачем", "просто", "зач", "нет"
]


# ──────────────────────── FSM (Состояния) ─────────────────────────
class DealState(StatesGroup):
    waiting_for_deal_form = State()


class ReportState(StatesGroup):
    waiting_for_report_reason = State()


class IdeaState(StatesGroup):
    waiting_for_idea = State()


# ──────────────────────── KEYBOARDS ─────────────────────────────
def main_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Отзывы 🖤")],
            [
                KeyboardButton(text="🔍 Найти гаранта в сети"),
                KeyboardButton(text="📄 Сделать резюме сделки"),
            ],
            [
                KeyboardButton(text="🛡️ Поддержка"),
                KeyboardButton(text="⚙️ In progress... ⛓️"),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="🌑 Выберите действие…",
    )


# ──────────────────────── UTILS ─────────────────────────────
async def notify_admin_action(
    bot: Bot, user: types.User, action_text: str
):
    """Отправка уведомления об активности в ЛС админу"""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    username = f"@{user.username}" if user.username else "без_юзернейма"
    text = (
        f"⚡ <b>[Лог активности]</b>\n"
        f"👤 <b>Пользователь:</b> {username} (ID: <code>{user.id}</code>)\n"
        f"🕒 <b>Время:</b> {now}\n"
        f"🎯 <b>Действие:</b> <code>{action_text}</code>"
    )
    try:
        await bot.send_message(ADMIN_CHAT_ID, text, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Ошибка логирования админу: {e}")


# ──────────────────────── HANDLERS ──────────────────────────────
async def cmd_start(message: types.Message, state: FSMContext, bot: Bot):
    await state.clear()
    await notify_admin_action(bot, message.from_user, "Команда /start или Сброс")

    await message.answer(
        "🕷️ <b>ЭТОТ БОТ ТВОРЕНИЕ БОЖЬЕ</b>\n\n"
        "✔️ <b>Заменяет @codcry во всех смыслах</b> ✔️\n\n"
        "—————————————————-\n"
        "🖤 created by @codcry: @jonnkq\n"
        "—————————————————-\n\n"
        "⚡️ <b>Правила строгие. Защита активна.</b>\n\n"
        f"💬 Нужны отзывы? — @{SUPPORT_USERNAME}\n\n"
        "⚖️ <b>Доступные модули:</b>\n"
        "_________________________________________\n\n"
        "🔍 <b>Найти гаранта в сети</b> — запуск поиска свободного гаранта.\n\n"
        "📄 <b>Сделать резюме сделки</b> — +50% к ускорению поиска гаранта.\n\n"
        "🛡️ <b>Поддержка</b> — прямой канал с администрацией.\n\n"
        "⚙️ <b>In progress...</b> — вектор развития и предложений.\n",
        parse_mode="HTML",
        reply_markup=main_kb(),
    )


async def btn_reviews_handler(message: types.Message, state: FSMContext, bot: Bot):
    await notify_admin_action(bot, message.from_user, "Запросил отзывы (Отзывы 🖤)")
    
    # Полный список загруженных файлов отзывов с их точными расширениями .jpg
    review_variants = [
        "rep5.jpg",
        "rep6.jpg",
        "rep7.jpg",
        "rep8.jpg",
        "rep9.jpg",
        "rep10.jpg",
        "rep11.jpg",
        "rep12.jpg",
        "rep13.jpg",
        "rep1_part1_png.jpg",
    ]
    
    # Случайным образом выбираем один из скриншотов
    chosen_file = random.choice(review_variants)
    
    try:
        photo_file = FSInputFile(chosen_file)
        await message.answer_photo(
            photo=photo_file,
            caption="🖤 <b>Реальный отзыв о работе гаранта ;()</b> #",
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"Ошибка отправки файла отзыва {chosen_file}: {e}")
        await message.answer(
            "⚠️ <b>Файлы отзывов загружаются или временно недоступны на сервере.</b> ;() #",
            parse_mode="HTML"
        )


# ── Бланк резюме сделки ────────────────────────────────────
async def cmd_make_deal(message: types.Message, state: FSMContext, bot: Bot):
    await notify_admin_action(bot, message.from_user, "Создание резюме сделки")
    await state.set_state(DealState.waiting_for_deal_form)
    await message.answer(
        "📄 <b>Заполните бланк сделки ;()</b>\n\n"
        "Отправьте одним сообщением данные строго по пунктам:\n\n"
        "1) Юзы покупателя и продавца (через @)\
