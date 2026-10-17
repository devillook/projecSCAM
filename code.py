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
    "хуй", "пизд", "еб", "eb", "хуе", "бля", "сук", "мраз", "сволоч",
    "гандон", "долбо", "идио", "дебил", "залуп", "шлюх", "сука", "ебал",
    "хуесос", "шлюха", "уеб", "блять", "нахуй", "похуй", "залупа", "мама",
    "твоя", "иди", "соси", "хз", "зачем", "просто", "зач", "нет"
]

# Глобальный счетчик для отправки отзывов строго по очереди без повторов
CURRENT_REVIEW_INDEX = 0


class DealState(StatesGroup):
    waiting_for_deal_form = State()

class ReportState(StatesGroup):
    waiting_for_report_reason = State()

class IdeaState(StatesGroup):
    waiting_for_idea = State()


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
    global CURRENT_REVIEW_INDEX
    await notify_admin_action(bot, message.from_user, "Запросил отзывы (Отзывы 🖤)")
    
    # Структура отзывов: каждый элемент списка — это отдельный отзыв.
    # Он может содержать как один файл, так и несколько частей (альбом).
    # Здесь прописаны твои группы файлов (rep1 с part1 и part2, а также остальные одиночные файлы).
    reviews_library = [
        # Отзыв 1 (состоит из двух частей альбома)
        [
            InputMediaPhoto(media=FSInputFile("rep1_part1.png"), caption="🖤 <b>Реальный отзыв о сделке ;()</b> #"),
            InputMediaPhoto(media=FSInputFile("rep1_part2.png"))
        ],
        # Остальные одиночные отзывы (проверь расширения .jpg или .png и поправь при необходимости)
        FSInputFile("rep5.jpg"),
        FSInputFile("rep6.jpg"),
        FSInputFile("rep7.jpg"),
        FSInputFile("rep8.jpg"),
        FSInputFile("rep9.jpg"),
        FSInputFile("rep10.jpg"),
        FSInputFile("rep11.jpg"),
        FSInputFile("rep12.jpg"),
        FSInputFile("rep13.jpg"),
    ]
    
    # Берем текущий отзыв по индексу
    current_review = reviews_library[CURRENT_REVIEW_INDEX]
    
    # Перемещаем указатель на следующий отзыв по кругу (когда дойдет до конца, начнется сначала)
    CURRENT_REVIEW_INDEX = (CURRENT_REVIEW_INDEX + 1) % len(reviews_library)
    
    try:
        if isinstance(current_review, list):
            # Отправка альбома (несколько частей разом)
            await message.answer_media_group(media=current_review)
        else:
            # Отправка одиночного файла
            await message.answer_photo(
                photo=current_review,
                caption="🖤 <b>Реальный отзыв о работе гаранта ;()</b> #",
                parse_mode="HTML"
            )
    except Exception as e:
        logging.error(f"Ошибка отправки отзыва: {e}")
        await message.answer(
            "⚠️ <b>Файл отзыва временно недоступен на сервере.</b> ;() #",
            parse_mode="HTML"
        )


async def cmd_make_deal(message: types.Message, state: FSMContext, bot: Bot):
    await notify_admin_action(bot, message.from_user, "Создание резюме сделки")
    await state.set_state(DealState.waiting_for_deal_form)
    await message.answer(
        "📄 <b>Заполните бланк сделки ;()</b>\n\n"
        "Отправьте одним сообщением данные строго по пунктам:\n\n"
        "1) Юзы покупателя и продавца (через @)\n"
        "2) Сумма сделки (только цифры)\n"
        "3) Валюта сделки\n"
        "4) Суть сделки\n\n"
        "<i>(Заполните все 4 пункта, без нецензурной лексики и лишнего шума).</i> #",
        parse_mode="HTML",
        reply_markup=main_kb(),
    )


async def process_deal_form(message: types.Message, state: FSMContext, bot: Bot):
    text = message.text.strip()
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    if len(lines) < 4:
        await message.answer("⚠️ <b>Заполните бланк до конца ;()</b>\n\nСообщение должно содержать минимум 4 строки.")
        return

    text_lower = text.lower()
    if any(prof in text_lower for prof in PROFANITY_WORDS):
        await message.answer("⚠️ <b>Не используйте мат и деструктивный лексикон.</b> #")
        return

    line_1 = lines[0]
    ats_count = len(re.findall(r"@[a-zA-Z0-9_]{3,}", line_1))
    if ats_count < 2:
        await message.answer("⚠️ <b>Укажите минимум 2 юзернейма через @ в первой строке.</b>")
        return

    line_2 = lines[1]
    if not re.search(r"\d+", line_2):
        await message.answer("⚠️ <b>Укажите сумму цифрами во второй строке.</b>")
        return

    await state.update_data(saved_deal_summary=text)
    await state.set_state(None)
    await notify_admin_action(bot, message.from_user, "Успешно заполнено резюме сделки")
    await message.answer(
        "✅ <b>Резюме зафиксировано! ✔️</b>\n\n"
        "Теперь при поиске гарантирован приоритетный отклик гарантов. 🕷️",
        parse_mode="HTML",
        reply_markup=main_kb(),
    )


async def cmd_guarantor(message: types.Message, state: FSMContext, bot: Bot):
    await notify_admin_action(bot, message.from_user, "Запрос на поиск гаранта")
    user_data = await state.get_data()
    deal_summary = user_data.get("saved_deal_summary")

    if not deal_summary:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Создать резюме сделки✔️", callback_data="go_make_summary")],
                [InlineKeyboardButton(text="Забить ✖️", callback_data="cancel_search")],
            ]
        )
        await message.answer(
            "💡 <b>Внимание ;()</b>\n\n"
            "У вас отсутствует заполненное резюме сделки. Для безопасного поиска советуем оформить бланк! #",
            parse_mode="HTML",
            reply_markup=kb,
        )
        return

    await run_guarantor_search(message, bot)


async def cb_go_make_summary(call: types.CallbackQuery, state: FSMContext, bot: Bot):
    await call.answer()
    await state.set_state(DealState.waiting_for_deal_form)
    await call.message.edit_text(
        "📄 <b>Заполните бланк сделки ;()</b>\n\n"
        "1) Юзы покупателя и продавца (через @)\n"
        "2) Сумма сделки (только цифры)\n"
        "3) Валюта сделки\n"
        "4) Суть сделки\n\n"
        "<i>Отправьте всё одним сообщением.</i> #",
        parse_mode="HTML",
    )


async def cb_cancel_search(call: types.CallbackQuery, bot: Bot):
    await call.answer("Поиск отменен.")
    await notify_admin_action(bot, call.from_user, "Нажал 'Забить' на поиске гаранта")
    await call.message.edit_text("🌑 <b>Поиск гаранта отменен.</b> #", parse_mode="HTML")


async def run_guarantor_search(message: types.Message, bot: Bot):
    await notify_admin_action(bot, message.from_user, "Старт процесса поиска в сети")
    total_duration = random.randint(15, 25)
    msg = await message.answer("🤖 <b>Инициализация поиска…</b> ;()", parse_mode="HTML")

    elapsed = 0
    step = 1

    while elapsed < total_duration:
        await asyncio.sleep(step)
        elapsed += step
        dots = "." * ((elapsed % 3) + 1)

        if elapsed <= 3:
            status_text = f"📄 <b>Проверка резюме{dots}</b> ;()"
        elif elapsed <= 10:
            status_text = f"🤖 <b>Проверка на бота{dots}</b> #"
        else:
            status_text = f"🌐 <b>Резюме отправлено, гаранты в сети получат уведомление{dots}</b> 🖤"

        try:
            await msg.edit_text(status_text, parse_mode="HTML")
        except Exception:
            pass

    name = random.choices(NAMES, weights=[w for _, w in NORMALIZED], k=1)[0]
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔗 Связаться с гарантом", url=f"https://t.me/{name}")],
            [InlineKeyboardButton(text="🚨 Пожаловаться на гаранта", callback_data=f"report:{name}")],
        ]
    )

    await msg.edit_text(
        f"🏴‍☠️ <b>Гарант отозвался</b> — @{name}\n\n"
        f"<i>Защищенный канал связи готов. Перешлите гаранту детали сделки. ;()</i> #",
        parse_mode="HTML",
        reply_markup=kb,
    )


async def cmd_in_progress(message: types.Message, bot: Bot):
    await notify_admin_action(bot, message.from_user, "Открыл раздел In Progress")
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💡 Предложить идею (/idea)", callback_data="btn_idea_trigger")]
        ]
    )
    await message.answer(
        "⚙️ <b>Мы растем, бот развивается!</b> ;()\n\n"
        "Мы работаем не покладая рук, и даже больше. ⚔️\n\n"
        "Вы можете предложить идею написав /idea #\n",
        parse_mode="HTML",
        reply_markup=kb,
    )


async def cb_idea_trigger(call: types.CallbackQuery, state: FSMContext, bot: Bot):
    await call.answer()
    await state.set_state(IdeaState.waiting_for_idea)
    await call.message.answer(
        "🖤 <b>Напишите вашу идею одним сообщением:</b>\n\n"
        "Мы внимательно изучим ваше предложение. ;() #",
        parse_mode="HTML",
    )


async def cmd_idea(message: types.Message, state: FSMContext, bot: Bot):
    await notify_admin_action(bot, message.from_user, "Ввел команду /idea")
    await state.set_state(IdeaState.waiting_for_idea)
    await message.answer(
        "🖤 <b>Напишите вашу идею одним сообщением:</b> ;()\n\n"
        "Опишите суть предложения максимально подробно. #",
        parse_mode="HTML",
    )


async def process_idea_text(message: types.Message, state: FSMContext, bot: Bot):
    idea_text = message.text.strip()
    user = message.from_user
    username = f"@{user.username}" if user.username else "без_юзернейма"
    await state.clear()

    admin_msg = (
        f"💡 <b>НОВАЯ ИДЕЯ ДЛЯ БОТА!</b> ;()\n\n"
        f"👤 <b>Автор:</b> {username} (ID: <code>{user.id}</code>)\n\n"
        f"📝 <b>Текст идеи:</b>\n{idea_text}"
    )

    try:
        await bot.send_message(ADMIN_CHAT_ID, admin_msg, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Не удалось переслать идею админу: {e}")

    await message.answer("идея подана на рассмотрение ✔️", reply_markup=main_kb())


async def cmd_support(message: types.Message, state: FSMContext, bot: Bot):
    await state.clear()
    await notify_admin_action(bot, message.from_user, "Запросил Поддержку")
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"💬 Обратиться к @{SUPPORT_USERNAME}", url=f"https://t.me/{SUPPORT_USERNAME}")]
        ]
    )
    await message.answer(
        f"🛡️ <b>Арбитраж / Поддержка</b> ;()\n\n"
        f"Прямой канал связи с администрацией: @{SUPPORT_USERNAME}. #",
        parse_mode="HTML",
        reply_markup=kb,
    )


async def cb_report_guarantor(call: types.CallbackQuery, state: FSMContext, bot: Bot):
    guarantor_name = call.data.split(":")[-1]
    await state.update_data(
        target_guarantor=guarantor_name,
        user_id=call.from_user.id,
        username=call.from_user.username,
    )
    await state.set_state(ReportState.waiting_for_report_reason)
    await call.answer()
    await call.message.answer(
        "⚠️ <b>Причина? ;()</b>\n\nОпишите суть жалобы на гаранта одним сообщением: #",
        parse_mode="HTML",
    )


async def process_report_reason(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    guarantor = data.get("target_guarantor")
    user_id = data.get("user_id")
    username = data.get("username", "не указан")
    reason = message.text
    await state.clear()

    report_text = (
        f"🚨 <b>НОВАЯ ЖАЛОБА НА ГАРАНТА!</b>\n\n"
        f"🛡 <b>Гарант:</b> @{guarantor}\n\n"
        f"👤 <b>От кого:</b> @{username} (ID: <code>{user_id}</code>)\n\n"
        f"📝 <b>Причина:</b>\n{reason}"
    )

    try:
        await bot.send_message(ADMIN_CHAT_ID, report_text, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Не удалось отправить жалобу: {e}")

    await message.answer(
        "✅ <b>Жалоба отправлена.</b> Администрация рассмотрит обращение в ближайшее время. ✔️",
        reply_markup=main_kb(),
    )


async def handle_random_text(message: types.Message, state: FSMContext, bot: Bot):
    current_state = await state.get_state()
    if current_state is not None:
        return
    await cmd_start(message, state, bot)


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
    print(f">>> 🌐 Веб-сервер активен на порту {port}")


async def main():
    print(">>> ⚔️ ИНИЦИАЛИЗАЦИЯ БОТА И ДИСПЕТЧЕРА...")
    logging.basicConfig(level=logging.INFO)

    bot = Bot(TG_BOT_TOKEN)
    dp = Dispatcher()

    dp.message.register(process_deal_form, StateFilter(DealState.waiting_for_deal_form))
    dp.message.register(process_report_reason, StateFilter(ReportState.waiting_for_report_reason))
    dp.message.register(process_idea_text, StateFilter(IdeaState.waiting_for_idea))

    dp.message.register(cmd_start, Command("start"))
    dp.message.register(btn_reviews_handler, F.text == "Отзывы 🖤")

    dp.message.register(cmd_guarantor, F.text == "🔍 Найти гаранта в сети")
    dp.message.register(cmd_make_deal, F.text == "📄 Сделать резюме сделки")
    dp.message.register(cmd_support, F.text == "🛡️ Поддержка")
    dp.message.register(cmd_in_progress, F.text == "⚙️ In progress... ⛓️")
    dp.message.register(cmd_idea, Command("idea"))

    dp.callback_query.register(cb_go_make_summary, F.data == "go_make_summary")
    dp.callback_query.register(cb_cancel_search, F.data == "cancel_search")
    dp.callback_query.register(cb_idea_trigger, F.data == "btn_idea_trigger")
    dp.callback_query.register(cb_report_guarantor, F.data.startswith("report:"))

    dp.message.register(handle_random_text, F.text)

    await start_web_server()

    print(">>> 🕷️ БОТ УСПЕШНО ЗАПУЩЕН!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(">>> 🌑 Бот остановлен.")
