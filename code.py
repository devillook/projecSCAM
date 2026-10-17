"""
🏴‍☠️ Гарант-бот: безопасные сделки, бланки договоров, система арбитража и Inline-интерфейс.
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
        InputMediaPhoto,
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
    "хуй", "пизд", "еб", "eb", "хуе", "бля", "сук", "мраз", "сволоч",
    "гандон", "долбо", "идио", "дебил", "залуп", "шлюх", "сука", "ебал",
    "хуесос", "шлюха", "уеб", "блять", "нахуй", "похуй", "залупа", "мама",
    "твоя", "иди", "соси", "хз", "зачем", "просто", "зач", "нет"
]

CURRENT_REVIEW_INDEX = 0


class DealState(StatesGroup):
    waiting_for_deal_form = State()

class ReportState(StatesGroup):
    waiting_for_report_reason = State()

class IdeaState(StatesGroup):
    waiting_for_idea = State()


# ──────────────────────── KEYBOARDS (INLINE) ─────────────────────────────
def main_inline_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="◼️ Найти гаранта в сети", callback_data="btn_find_guarantor"),
            ],
            [
                InlineKeyboardButton(text="📄 Договор сделки", callback_data="btn_make_deal"),
                InlineKeyboardButton(text="🖤 Отзывы", callback_data="btn_reviews"),
            ],
            [
                InlineKeyboardButton(text="📜 Правила сервиса", callback_data="btn_rules"),
                InlineKeyboardButton(text="⛓️ Идея (/idea)", callback_data="btn_idea_trigger"),
            ],
            [
                InlineKeyboardButton(text="🏴‍☠️ Поддержка / Арбитраж", url=f"https://t.me/{SUPPORT_USERNAME}"),
            ]
        ]
    )


def review_inline_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Еще отзыв", callback_data="btn_reviews"),
                InlineKeyboardButton(text="« Меню", callback_data="btn_back_to_main")
            ]
        ]
    )


async def notify_admin_action(bot: Bot, user: types.User, action_text: str):
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

    first_name = message.from_user.first_name or "Kowareta"
    
    caption_text = (
        f"🕷 Приветствую, {first_name}! ;()\n"
        f"Это теневой гарант-сервис безопасных сделок.\n\n"
        f"⭐️⭐️⭐️⭐️⭐️⭐️⭐️⭐️⭐️⭐️⭐️\n\n"
        f"Что умеет бот:\n"
        f" 🗯 Автоматический подбор свободных гарантов\n\n"
        f" 💬 Составление ускоренных договоров сделок\n\n"
        f" 🔘 Проверенная система отзывов и арбитража\n\n"
        f"🔐 Перед началом работы ознакомьтесь с правилами и условиями\n\n"
        f"Используя бота, вы автоматически принимаете регламент сервиса. ;()"
    )

    if os.path.exists("banner.jpg"):
        photo = FSInputFile("banner.jpg")
        await message.answer_photo(
            photo=photo,
            caption=caption_text,
            parse_mode="HTML",
            reply_markup=main_inline_kb()
        )
    else:
        await message.answer(
            text=caption_text,
            parse_mode="HTML",
            reply_markup=main_inline_kb()
        )


def get_all_reviews():
    all_files = [f for f in os.listdir('.') if f.startswith('rep') and f.lower().endswith(('.png', '.jpg', '.jpeg')) and 'rep13' not in f]
    groups = {}
    for filename in sorted(all_files):
        match = re.match(r"(rep\d+)", filename)
        if match:
            group_key = match.group(1)
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(filename)
        else:
            groups[filename] = [filename]

    reviews_list = []
    for group_key in sorted(groups.keys()):
        files = sorted(groups[group_key])
        if len(files) > 1:
            media_group = [
                InputMediaPhoto(media=FSInputFile(files[0]), caption="🖤 <b>Реальный отзыв о сделке ;()</b> #", parse_mode="HTML")
            ]
            for f in files[1:]:
                media_group.append(InputMediaPhoto(media=FSInputFile(f)))
            reviews_list.append(media_group)
        elif len(files) == 1:
            reviews_list.append(FSInputFile(files[0]))
            
    return reviews_list


async def cb_reviews_handler(call: types.CallbackQuery, bot: Bot):
    global CURRENT_REVIEW_INDEX
    await call.answer()
    await notify_admin_action(bot, call.from_user, "Запросил отзывы (🖤 Отзывы / Еще отзыв)")
    
    reviews_library = get_all_reviews()
    
    if not reviews_library:
        await call.message.answer("⚠️ <b>Отзывы пока недоступны.</b> ;() #", parse_mode="HTML")
        return

    current_review = reviews_library[CURRENT_REVIEW_INDEX % len(reviews_library)]
    CURRENT_REVIEW_INDEX = (CURRENT_REVIEW_INDEX + 1) % len(reviews_library)
    
    try:
        if isinstance(current_review, list):
            # В Телеграме альбомы отправляются пачкой, кнопку прикрепляем к последнему фото или отправляем текст с кнопкой рядом
            await call.message.answer_media_group(media=current_review)
            await call.message.answer(
                "🖤 <b>Следующий отзыв всегда под рукой ;()</b> #",
                parse_mode="HTML",
                reply_markup=review_inline_kb()
            )
        else:
            await call.message.answer_photo(
                photo=current_review,
                caption="🖤 <b>Реальный отзыв о работе гаранта ;()</b> #",
                parse_mode="HTML",
                reply_markup=review_inline_kb()
            )
    except Exception as e:
        logging.error(f"Ошибка отправки отзыва: {e}")
        await call.message.answer("⚠️ <b>Не удалось загрузить данный отзыв.</b> ;() #", parse_mode="HTML")


# ── Раздел Правила ─────────────────────────────────────────
async def cb_rules_handler(call: types.CallbackQuery, bot: Bot):
    await call.answer()
    await notify_admin_action(bot, call.from_user, "Открыл правила сервиса")
    
    rules_text = (
        "📜 <b>ПРАВИЛА И РЕГЛАМЕНТ СЕРВИСА ;()</b>\n\n"
        "1. <b>Безопасность сделки:</b> Все финансовые операции проводятся строго через официальных гарантов сервиса. #\n"
        "2. <b>Фейки и подделки:</b> Всегда сверяйте юзернейм гаранта в диалоге! Единственный логин поддержки — @codcry. ✔️\n"
        "3. <b>Комиссия:</b> Комиссия гаранта фиксируется до начала проведения сделки. ;()\n"
        "4. <b>Запрещенные действия:</b> Оскорбления, спам, попытка обмана или использование нецензурной лексики в договоре ведут к блокировке. 🖤\n"
        "5. <b>Арбитраж:</b> Все споры решаются исключительно через официальную поддержку / арбитраж бота.\n\n"
        "<i>Соблюдение правил гарантирует 100% безопасность ваших средств.</i> 🕷️"
    )
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="« Назад в меню", callback_data="btn_back_to_main")]
        ]
    )
    
    await call.message.answer(rules_text, parse_mode="HTML", reply_markup=kb)


async def cb_back_to_main(call: types.CallbackQuery, state: FSMContext, bot: Bot):
    await call.answer()
    await cmd_start(call.message, state, bot)


# ── Бланк договора сделки ────────────────────────────────────
async def cb_make_deal(call: types.CallbackQuery, state: FSMContext, bot: Bot):
    await call.answer()
    await notify_admin_action(bot, call.from_user, "Создание договора сделки")
    await state.set_state(DealState.waiting_for_deal_form)
    await call.message.answer(
        "📄 <b>Заполните бланк договора сделки ;()</b>\n\n"
        "Отправьте одним сообщением данные строго по пунктам:\n\n"
        "1) Юзы покупателя и продавца (через @)\n"
        "2) Сумма сделки (только цифры)\n"
        "3) Валюта сделки\n"
        "4) Суть сделки\n\n"
        "<i>(Заполните все 4 пункта, без нецензурной лексики и лишнего шума).</i> #",
        parse_
