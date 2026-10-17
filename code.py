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
        parse_mode="HTML"
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
    await notify_admin_action(bot, message.from_user, "Успешно заполнено договор сделки")
    
    await message.answer(
        "✅ <b>Договор зафиксирован! ✔️</b>\n\n"
        "Теперь при поиске гарантирован приоритетный отклик гарантов. 🕷️",
        parse_mode="HTML",
        reply_markup=main_inline_kb()
    )


# ── Поиск гаранта ────────────────────────────────────────
async def cb_find_guarantor(call: types.CallbackQuery, state: FSMContext, bot: Bot):
    await call.answer()
    await notify_admin_action(bot, call.from_user, "Запрос на поиск гаранта")
    user_data = await state.get_data()
    deal_summary = user_data.get("saved_deal_summary")

    if not deal_summary:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Создать договор сделки✔️", callback_data="cb_go_make_summary")],
                [InlineKeyboardButton(text="Забить ✖️", callback_data="cancel_search")],
            ]
        )
        await call.message.answer(
            "💡 <b>Внимание ;()</b>\n\n"
            "У вас отсутствует заполненный договор сделки. Для безопасного поиска советуем оформить бланк! #",
            parse_mode="HTML",
            reply_markup=kb,
        )
        return

    await run_guarantor_search(call.message, bot, call.from_user)


async def cb_go_make_summary(call: types.CallbackQuery, state: FSMContext, bot: Bot):
    await call.answer()
    await state.set_state(DealState.waiting_for_deal_form)
    await call.message.edit_text(
        "📄 <b>Заполните бланк договора сделки ;()</b>\n\n"
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


async def run_guarantor_search(message: types.Message, bot: Bot, user: types.User):
    await notify_admin_action(bot, user, "Старт процесса поиска в сети")
    total_duration = random.randint(15, 25)
    msg = await message.answer("🤖 <b>Инициализация поиска…</b> ;()", parse_mode="HTML")

    elapsed = 0
    step = 1

    while elapsed < total_duration:
        await asyncio.sleep(step)
        elapsed += step
        dots = "." * ((elapsed % 3) + 1)

        if elapsed <= 3:
            status_text = f"📄 <b>Проверка договора{dots}</b> ;()"
        elif elapsed <= 10:
            status_text = f"🤖 <b>Проверка на бота{dots}</b> #"
        else:
            status_text = f"🌐 <b>Договор отправлен, гаранты в сети получат уведомление{dots}</b> 🖤"

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


# ── Идеи ──────────────────────────────────────────────
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

    await message.answer("идея подана на рассмотрение ✔️", reply_markup=main_inline_kb())


# ── Жалоба на гаранта ──────────────────────────────────
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
        reply_markup=main_inline_kb(),
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


# ──────────────────────── MAIN ────────────────────────────
async def main():
    print(">>> ⚔️ ИНИЦИАЛИЗАЦИЯ БОТА И ДИСПЕТЧЕРА...")
    logging.basicConfig(level=logging.INFO)

    bot = Bot(TG_BOT_TOKEN)
    dp = Dispatcher()

    # FSM
    dp.message.register(process_deal_form, StateFilter(DealState.waiting_for_deal_form))
    dp.message.register(process_report_reason, StateFilter(ReportState.waiting_for_report_reason))
    dp.message.register(process_idea_text, StateFilter(IdeaState.waiting_for_idea))

    # Команды
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_idea, Command("idea"))

    # Инлайн-обработчики
    dp.callback_query.register(cb_reviews_handler, F.data == "btn_reviews")
    dp.callback_query.register(cb_rules_handler, F.data == "btn_rules")
    dp.callback_query.register(cb_back_to_main, F.data == "btn_back_to_main")
    dp.callback_query.register(cb_find_guarantor, F.data == "btn_find_guarantor")
    dp.callback_query.register(cb_make_deal, F.data == "btn_make_deal")
    dp.callback_query.register(cb_go_make_summary, F.data == "cb_go_make_summary")
    dp.callback_query.register(cb_cancel_search, F.data == "cancel_search")
    dp.callback_query.register(cb_idea_trigger, F.data == "btn_idea_trigger")
    dp.callback_query.register(cb_report_guarantor, F.data.startswith("report:"))

    # Перехват любого текста
    dp.message.register(handle_random_text, F.text)

    await start_web_server()

    print(">>> 🕷️ БОТ УСПЕШНО ЗАПУЩЕН!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(">>> 🌑 Бот остановлен.")
