"""
Гарант-бот: безопасные сделки, бланки резюме и система арбитража.
"""

import asyncio
import logging
import os
import re

print(">>> Загрузка библиотек...")

try:
    from aiogram import Bot, Dispatcher, F, types
    from aiogram.filters import Command, StateFilter
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.state import State, StatesGroup
    from aiogram.types import (
        InlineKeyboardButton,
        InlineKeyboardMarkup,
        ReplyKeyboardMarkup,
        KeyboardButton,
    )
    from aiohttp import web
    print(">>> Библиотеки aiogram и aiohttp успешно импортированы!")
except ImportError as e:
    print(f">>> ПОМИЛКА: Не встановлено необхідні бібліотеки! Встановіть через 'pip install aiogram aiohttp'. Деталі: {e}")
    exit(1)

TG_BOT_TOKEN = "8848474277:AAHQ82X-lQKK6OXKJ-NmS8DizhMwAdPdHlQ"
ADMIN_CHAT_ID = 985669697
SUPPORT_USERNAME = "codcry"

GUARANTORS = [
    ("arkovh",   11.25),
    ("codcry",   55.00),
    ("hyppergamy", 11.25),
    ("hightwear",  11.25),
    ("Inarkav",    11.25),
]
_weights = [w for _, w in GUARANTORS]
_total = sum(_weights)
NORMALIZED = [(n, w / _total) for n, w in GUARANTORS]
NAMES = [n for n, _ in NORMALIZED]

SEARCH_MIN, SEARCH_MAX = 20, 50

PROFANITY_WORDS = [
    "хуй", "пизд", "еб", "eb", "хуе", "бля", "сук", "мраз", "сволоч", 
    "гандон", "долбо", "идио", "дебил", "залуп", "шлюх", "сука", "ебал",
    "хуесос", "шлюха", "уеб", "блять", "нахуй", "похуй", "залупа",
    "мама", "твоя", "иди", "соси", "хз", "зачем", "просто", "зач", "нет"
]

class DealState(StatesGroup):
    waiting_for_deal_form = State()

class ReportState(StatesGroup):
    waiting_for_report_reason = State()

def main_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Найти гаранта в сети")],
            [KeyboardButton(text="📄 Сделать резюме сделки")],
            [KeyboardButton(text="🛡️ Поддержка")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие…",
    )

async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    print(f"[{message.from_user.id}] Запрошена команда /start")
    await message.answer(
        "Привет! Этот бот-заместитель @codcry во всех планах\n\n"
        "Он может напрямую вас связать со администрацией так и найти гаранта для сделки\n\n"
        "—————————————————-\n\n"
        "🌑 created by @codcry: @jonnkq😍\n\n"
        "—————————————————-\n\n"
        "Правила строгие, защита имеется\n\n"
        f"💬 Нужны отзывы? — @{SUPPORT_USERNAME}\n\n"
        "⚖️ Доступные разделы:\n\n"
        "-\n"
        "🔍 Найти гаранта в сети — поиск свободного агента для сделки.\n\n"
        "-\n"
        "📄 Сделать резюме сделки — +50% к поиску гарантов с вашими условиями сделки, занимает пару секунд!\n\n"
        "-\n"
        "🛡 Поддержка — прямой чат с администрацией.",
        parse_mode="HTML",
        reply_markup=main_kb(),
    )

async def cmd_make_deal(message: types.Message, state: FSMContext):
    await state.set_state(DealState.waiting_for_deal_form)
    await message.answer(
        "📄 <b>Заполните бланк сделки</b>\n\n"
        "Отправьте одним сообщением данные ровно по пунктам:\n\n"
        "1) Юзы покупателя и продавца (через @)\n\n"
        "2) Сумма сделки (только цифры)\n\n"
        "3) Валюта сделки\n\n"
        "4) Суть сделки\n\n"
        "<i>(Заполните все 4 пункта, без мата и сторонних слов).</i>",
        parse_mode="HTML",
        reply_markup=main_kb(),
    )

async def process_deal_form(message: types.Message, state: FSMContext):
    text = message.text.strip()
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if len(lines) < 4:
        await message.answer("⚠️ <b>Заполните до конца бланк.</b>\n\nСообщение должно содержать минимум 4 строки.")
        return
    text_lower = text.lower()
    if any(prof in text_lower for prof in PROFANITY_WORDS):
        await message.answer("⚠️ <b>Не используйте мат и оскорбления.</b>")
        return
    line_1 = lines[0]
    ats_count = len(re.findall(r"@[a-zA-Z0-9_]{3,}", line_1))
    if ats_count < 2:
        await message.answer("⚠️ <b>Укажите минимум 2 юзернейма через @</b>")
        return
    line_2 = lines[1]
    if not re.search(r"\d+", line_2):
        await message.answer("⚠️ <b>Укажите сумму цифрами.</b>")
        return
    await state.update_data(saved_deal_summary=text)
    await state.set_state(None)
    await message.answer("✅ <b>Резюме создано!</b>", parse_mode="HTML", reply_markup=main_kb())

async def cmd_guarantor(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    deal_summary = user_data.get("saved_deal_summary")
    if not deal_summary:
        await message.answer("💡 <b>Рекомендация:</b> Сделайте резюме сделки для ускорения.", parse_mode="HTML")
    else:
        await message.answer("📋 <b>Резюме прикреплено. Поиск запущен...</b>", parse_mode="HTML")
    duration = random.randint(SEARCH_MIN, SEARCH_MAX)
    msg = await message.answer("🤖 <b>Проверка на бота…</b>", parse_mode="HTML")
    elapsed = 0
    step = 4
    while elapsed < duration:
        await asyncio.sleep(step)
        elapsed += step
        dots = "." * ((elapsed // 2) % 4)
        status_text = f"🤖 <b>Проверка на бота{dots}</b>" if elapsed <= 8 else (f"🌐 <b>Отправка запроса{dots}</b>" if elapsed <= 24 else f"⚖️ <b>Ждём отклик гарантов{dots}</b>")
        try:
            await msg.edit_text(status_text, parse_mode="HTML")
        except Exception:
            pass
    name = random.choices(NAMES, weights=[w for _, w in NORMALIZED], k=1)[0]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Связаться с гарантом", url=f"https://t.me/{name}")],
        [InlineKeyboardButton(text="🚨 Пожаловаться на гаранта", callback_data=f"report:{name}")],
    ])
    await msg.edit_text(f"🏴‍☠️ <b>Гарант отозвался</b> — @{name}", parse_mode="HTML", reply_markup=kb)

async def cmd_support(message: types.Message, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=f"💬 Обратиться к @{SUPPORT_USERNAME}", url=f"https://t.me/{SUPPORT_USERNAME}")]])
    await message.answer(f"🛡️ <b>Арбитраж / Поддержка</b>\n\nПрямой канал связи: @{SUPPORT_USERNAME}.", parse_mode="HTML", reply_markup=kb)

async def cb_report_guarantor(call: types.CallbackQuery, state: FSMContext):
    guarantor_name = call.data.split(":")[-1]
    await state.update_data(target_guarantor=guarantor_name, user_id=call.from_user.id, username=call.from_user.username)
    await state.set_state(ReportState.waiting_for_report_reason)
    await call.answer()
    await call.message.answer("⚠️ <b>Опишите суть жалобы на гаранта одним сообщением:</b>", parse_mode="HTML")

async def process_report_reason(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    guarantor = data.get("target_guarantor")
    user_id = data.get("user_id")
    username = data.get("username", "не указан")
    reason = message.text
    await state.clear()
    report_text = f"🚨 <b>НОВАЯ ЖАЛОБА!</b>\n\n🛡 <b>Гарант:</b> @{guarantor}\n👤 <b>От кого:</b> @{username} (ID: <code>{user_id}</code>)\n📝 <b>Причина:</b>\n{reason}"
    try:
        await bot.send_message(ADMIN_CHAT_ID, report_text, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Не удалось отправить жалобу: {e}")
    await message.answer("✅ <b>Жалоба отправлена администратору.</b>", reply_markup=main_kb())

async def handle_ping(request):
    return web.Response(text="Bot is alive!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f">>> Веб-сервер запущен на порту {port}")

async def main():
    print(">>> ИНИЦИАЛИЗАЦИЯ БОТА...")
    logging.basicConfig(level=logging.INFO)
    bot = Bot(TG_BOT_TOKEN)
    dp = Dispatcher()
    dp.message.register(process_deal_form, StateFilter(DealState.waiting_for_deal_form))
    dp.message.register(process_report_reason, StateFilter(ReportState.waiting_for_report_reason))
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_guarantor, F.text == "🔍 Найти гаранта в сети")
    dp.message.register(cmd_make_deal, F.text == "📄 Сделать резюме сделки")
    dp.message.register(cmd_support, F.text == "🛡️ Поддержка")
    dp.callback_query.register(cb_report_guarantor, F.data.startswith("report:"))
    await start_web_server()
    print(">>> БОТ УСПЕШНО ЗАПУЩЕН!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(">>> Бот остановлен.")

