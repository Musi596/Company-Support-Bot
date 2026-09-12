import asyncio
import os
from typing import Any

from aiogram import Bot, Dispatcher, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from dotenv import load_dotenv

from bot import buttons, services, sql
from bot.fsm import AdminStates, BroadcastStates, CourseStates, ReportStates
from bot.utils import normalize_slug

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
if not API_TOKEN:
    raise RuntimeError("API_TOKEN is not set in environment")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
db_pool: Any = None

LANG_TITLES = {
    "tj": "Выберите курс на языке Тоҷикӣ:",
    "ru": "Выберите курс:",
    "en": "Choose a course:",
}

COURSE_LANGUAGE_NAMES = {
    "tj": "Тоҷикӣ",
    "ru": "Русский",
    "en": "English",
}


async def safe_callback_answer(
    callback: CallbackQuery,
    text: str | None = None,
    *,
    show_alert: bool = False,
):
    try:
        await callback.answer(text, show_alert=show_alert)
    except TelegramBadRequest:
        pass


async def safe_edit_message(
    callback: CallbackQuery,
    text: str,
    *,
    parse_mode=None,
    reply_markup=None,
):
    if callback.message is None:
        return

    try:
        if callback.message.content_type == "photo":
            try:
                await callback.message.edit_caption(
                    caption=text,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup,
                )
                return
            except TelegramBadRequest:
                pass
        await callback.message.edit_text(
            text,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
        )
    except TelegramBadRequest:
        try:
            await callback.message.answer(
                text,
                parse_mode=parse_mode,
                reply_markup=reply_markup,
            )
        except TelegramBadRequest:
            pass


def is_group_chat(chat) -> bool:
    return chat.type in {"group", "supergroup", "channel"}


def build_course_list_keyboard(courses, lang: str):
    rows = []
    current_row = []

    for course in courses:
        current_row.append(
            InlineKeyboardButton(
                text=course["title"],
                callback_data=f"courses_course:{lang}:{course['slug']}",
            )
        )
        if len(current_row) == 2:
            rows.append(current_row)
            current_row = []

    if current_row:
        rows.append(current_row)

    rows.append([
        InlineKeyboardButton(text="🔙 Назад к выбору языка", callback_data="courses_menu")
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@dp.message(Command("add_group"))
async def add_group_to_broadcast(message: Message):
    if not is_group_chat(message.chat):
        await message.answer("⚠️ Команда /add_group доступна только в группе.")
        return

    if not await services.is_admin(db_pool, message.from_user.id):
        await message.answer("⚠️ Только администратор бота может подключать эту группу к рассылке.")
        return

    await services.save_or_update_chat(
        db_pool,
        message.chat.id,
        message.chat.type,
        message.chat.title or message.chat.username,
    )
    await message.answer("✅ Группа добавлена в список рассылок.")


@dp.message(Command("courses"))
async def cmd_courses(message: Message):
    if is_group_chat(message.chat):
        return

    await message.answer(
        "Выберите язык, на котором хотите узнать о курсах:",
        reply_markup=buttons.get_courses_language_keyboard(),
    )


@dp.callback_query(F.data == "courses_menu")
async def courses_menu(callback: CallbackQuery):
    await safe_edit_message(
        callback,
        "Выберите язык, на котором хотите узнать о курсах:",
        reply_markup=buttons.get_courses_language_keyboard(),
    )
    await safe_callback_answer(callback)


@dp.callback_query(F.data.startswith("courses_lang:"))
async def courses_language(callback: CallbackQuery):
    lang = callback.data.split(":", 1)[1]
    pool = db_pool
    courses = await services.get_courses_by_lang(pool, lang)

    if not courses:
        await safe_edit_message(
            callback,
            "Пока нет курсов для выбранного языка.",
            reply_markup=buttons.get_courses_back_keyboard(),
        )
        await safe_callback_answer(callback)
        return

    kb = build_course_list_keyboard(courses, lang)
    await safe_edit_message(
        callback,
        LANG_TITLES.get(lang, "Выберите курс:"),
        reply_markup=kb,
    )
    await safe_callback_answer(callback)


@dp.callback_query(F.data.startswith("courses_list:"))
async def courses_list(callback: CallbackQuery):
    lang = callback.data.split(":", 1)[1]
    courses = await services.get_courses_by_lang(db_pool, lang)

    if not courses:
        await safe_edit_message(
            callback,
            "Пока нет курсов для выбранного языка.",
            reply_markup=buttons.get_courses_back_keyboard(),
        )
        await safe_callback_answer(callback)
        return

    kb = build_course_list_keyboard(courses, lang)
    await safe_edit_message(
        callback,
        LANG_TITLES.get(lang, "Выберите курс:"),
        reply_markup=kb,
    )
    await safe_callback_answer(callback)


@dp.callback_query(F.data.startswith("courses_course:"))
async def courses_detail(callback: CallbackQuery):
    _, lang, slug = callback.data.split(":", 2)
    course = await services.get_course_by_slug(db_pool, slug, lang)
    if not course:
        await safe_callback_answer(callback, "Курс не найден.", show_alert=True)
        return

    text = course["description"] or course["title"]
    kb = buttons.get_courses_detail_keyboard(lang)

    if course["photo"]:
        try:
            await callback.message.answer_photo(
                photo=course["photo"],
                caption=text,
                reply_markup=kb,
            )
            await safe_callback_answer(callback)
            return
        except Exception:
            pass

    await safe_edit_message(callback, text, reply_markup=kb)
    await safe_callback_answer(callback)


@dp.message(CommandStart())
async def cmd_start(message: Message):
    if is_group_chat(message.chat):
        return

    await services.save_or_update_user(db_pool, message.from_user.id, message.from_user.full_name)
    is_admin = await services.is_admin(db_pool, message.from_user.id)

    await message.answer_sticker(
        sticker="CAACAgIAAxkBAAER3dRqns8OAAFAJ_41_64myZOJ35l9DIQAAkaFAAJtfQABSYjWiVDXg4rkPQQ"
    )

    if is_admin:
        await message.answer(
            "👑 *Добро пожаловать, администратор!*\n\n"
            "Вы можете просматривать новые вопросы и жалобы, отвечать на них и закрывать обращения.",
            parse_mode="Markdown",
            reply_markup=buttons.get_admin_reply_keyboard(),
        )
        return

    await message.answer(
        "✨ *Добро пожаловать в SoftClub!* 🚀\n\n"
        "Рады видеть вас в нашем учебном центре программирования.\n\n"
        "📌 *Основные команды:*\n\n"
        "📚 /help — Узнать о SoftClub и боте\n"
        "📝 /report — Отправить вопрос или жалобу администрации\n\n"
        "💡 _Выберите нужную команду выше или введите её._",
        parse_mode="Markdown",
        reply_markup=buttons.get_user_reply_keyboard(),
    )


@dp.message(F.text == "📚 Курсы")
async def user_courses_button(message: Message):
    if is_group_chat(message.chat):
        return
    await cmd_courses(message)


@dp.message(F.text == "📝 Написать в поддержку")
async def user_report_button(message: Message, state: FSMContext):
    if is_group_chat(message.chat):
        return
    await cmd_report(message, state)


@dp.message(F.text == "📖 Помощь")
async def user_help_button(message: Message):
    if is_group_chat(message.chat):
        return
    await cmd_help(message)


@dp.message(F.text == "📋 Вопросы")
async def admin_tickets_button(message: Message):
    if is_group_chat(message.chat):
        return
    if not await services.is_admin(db_pool, message.from_user.id):
        await message.answer("⚠️ У вас нет прав администратора.")
        return

    tickets = await services.get_open_tickets(db_pool)
    if not tickets:
        await message.answer(
            "📭 Нет новых вопросов и жалоб. Все обращения уже закрыты.",
            reply_markup=buttons.get_admin_main_keyboard(),
        )
        return

    lines = []
    for ticket in tickets:
        preview = ticket["question"].replace("\n", " ")[:70]
        if len(ticket["question"]) > 70:
            preview += "..."
        lines.append(f"#{ticket['ticket_id']} • {ticket['user_name']} • {preview}")

    text = "📋 *Неотвеченные вопросы и жалобы:*\n\n" + "\n".join(lines)
    await message.answer(text, parse_mode="Markdown", reply_markup=buttons.get_admin_ticket_list_keyboard(tickets))


@dp.message(F.text == "📣 Рассылка")
async def admin_broadcast_button(message: Message, state: FSMContext):
    if is_group_chat(message.chat):
        return
    if not await services.is_admin(db_pool, message.from_user.id):
        await message.answer("⚠️ У вас нет прав администратора.")
        return

    await message.answer("📣 Куда отправлять рассылку?", reply_markup=buttons.get_broadcast_mode_keyboard())
    await state.update_data(broadcast_all=False, selected_chat_ids=[])


@dp.message(F.text == "🧑‍🏫 Курсы")
async def admin_courses_button(message: Message):
    if is_group_chat(message.chat):
        return
    if not await services.is_admin(db_pool, message.from_user.id):
        await message.answer("⚠️ У вас нет прав администратора.")
        return

    courses = []
    for lang in ("ru", "en", "tj"):
        courses.extend(await services.get_courses_by_lang(db_pool, lang))

    keyboard_rows = [[InlineKeyboardButton(text="➕ Добавить курс", callback_data="admin_add_course")]]
    for course in courses:
        keyboard_rows.append([
            InlineKeyboardButton(
                text=f"{course['lang']} • {course['slug']} — {course['title']}",
                callback_data=f"admin_course:{course['course_id']}",
            )
        ])
    keyboard_rows.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_open_tickets")])

    await message.answer("🛠 Управление курсами:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_rows))


@dp.message(F.text == "👥 Группы")
async def admin_groups_button(message: Message):
    if is_group_chat(message.chat):
        return
    if not await services.is_admin(db_pool, message.from_user.id):
        await message.answer("⚠️ У вас нет прав администратора.")
        return

    chats = await services.get_registered_chats(db_pool)
    await message.answer(
        "👥 Подключённые группы:\n\nВыберите группу для удаления из списка рассылки.",
        reply_markup=buttons.get_group_list_keyboard(chats),
    )


@dp.callback_query(F.data == "admin_open_tickets")
async def admin_open_tickets(callback: CallbackQuery):
    if not await services.is_admin(db_pool, callback.from_user.id):
        await safe_callback_answer(callback, "⚠️ У вас нет прав администратора.", show_alert=True)
        return

    tickets = await services.get_open_tickets(db_pool)
    if not tickets:
        await safe_edit_message(
            callback,
            "📭 Нет новых вопросов и жалоб. Все обращения уже закрыты.",
            reply_markup=buttons.get_admin_main_keyboard(),
        )
        await safe_callback_answer(callback, "Нет новых обращений.")
        return

    lines = []
    for ticket in tickets:
        preview = ticket["question"].replace("\n", " ")[:70]
        if len(ticket["question"]) > 70:
            preview += "..."
        lines.append(f"#{ticket['ticket_id']} • {ticket['user_name']} • {preview}")

    text = "📋 *Неотвеченные вопросы и жалобы:*\n\n" + "\n".join(lines)
    await safe_edit_message(
        callback,
        text,
        parse_mode="Markdown",
        reply_markup=buttons.get_admin_ticket_list_keyboard(tickets),
    )
    await safe_callback_answer(callback)


@dp.callback_query(F.data == "admin_manage_courses")
async def admin_manage_courses(callback: CallbackQuery):
    if not await services.is_admin(db_pool, callback.from_user.id):
        await safe_callback_answer(callback, "⚠️ У вас нет прав администратора.", show_alert=True)
        return

    courses = []
    for lang in ("ru", "en", "tj"):
        courses.extend(await services.get_courses_by_lang(db_pool, lang))

    keyboard_rows = [[InlineKeyboardButton(text="➕ Добавить курс", callback_data="admin_add_course")]]
    for course in courses:
        keyboard_rows.append([
            InlineKeyboardButton(
                text=f"{course['lang']} • {course['slug']} — {course['title']}",
                callback_data=f"admin_course:{course['course_id']}",
            )
        ])
    keyboard_rows.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_open_tickets")])

    await safe_edit_message(callback, "🛠 Управление курсами:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_rows))
    await safe_callback_answer(callback)


@dp.callback_query(F.data == "admin_view_groups")
async def admin_view_groups(callback: CallbackQuery):
    if not await services.is_admin(db_pool, callback.from_user.id):
        await safe_callback_answer(callback, "⚠️ У вас нет прав администратора.", show_alert=True)
        return

    chats = await services.get_registered_chats(db_pool)
    await safe_edit_message(
        callback,
        "👥 Подключённые группы:\n\nВыберите группу для удаления из списка рассылки.",
        reply_markup=buttons.get_group_list_keyboard(chats),
    )
    await safe_callback_answer(callback)


@dp.callback_query(F.data.startswith("admin_group_delete:"))
async def admin_group_delete(callback: CallbackQuery):
    if not await services.is_admin(db_pool, callback.from_user.id):
        await safe_callback_answer(callback, "⚠️ У вас нет прав администратора.", show_alert=True)
        return

    chat_id = int(callback.data.split(":", 1)[1])
    try:
        await bot.leave_chat(chat_id)
    except Exception:
        pass

    await services.delete_chat(db_pool, chat_id)
    await admin_view_groups(callback)
    await safe_callback_answer(callback, "Группа удалена и бот вышел из неё.")


@dp.callback_query(F.data == "admin_add_course")
async def admin_add_course_start(callback: CallbackQuery, state: FSMContext):
    if not await services.is_admin(db_pool, callback.from_user.id):
        await safe_callback_answer(callback, "⚠️ У вас нет прав администратора.", show_alert=True)
        return

    await callback.message.answer("📥 Введите язык курса (ru / tj / en):")
    await state.set_state(CourseStates.waiting_for_lang)
    await safe_callback_answer(callback)


@dp.message(CourseStates.waiting_for_lang, F.text)
async def course_waiting_lang(message: Message, state: FSMContext):
    lang = message.text.strip().lower()
    if lang not in {"ru", "tj", "en"}:
        await message.answer("Неверный язык. Введите один из: ru, tj, en")
        return

    await state.update_data(lang=lang)
    await message.answer("Введите уникальный идентификатор курса (slug), например: python или ai")
    await state.set_state(CourseStates.waiting_for_slug)


@dp.message(CourseStates.waiting_for_slug, F.text)
async def course_waiting_slug(message: Message, state: FSMContext):
    slug = normalize_slug(message.text)
    if not slug or slug == "course":
        await message.answer("Слаг не может быть пустым. Попробуйте ещё раз.")
        return

    await state.update_data(slug=slug)
    await message.answer("Введите заголовок курса (короткое название):")
    await state.set_state(CourseStates.waiting_for_title)


@dp.message(CourseStates.waiting_for_title, F.text)
async def course_waiting_title(message: Message, state: FSMContext):
    title = message.text.strip()
    if not title:
        await message.answer("Заголовок не может быть пустым.")
        return

    data = await state.get_data()
    editing_course_id = data.get("editing_course_id")

    if editing_course_id:
        try:
            await services.update_course(db_pool, editing_course_id, title=title)
            await message.answer("✅ Название курса обновлено.")
        except Exception as exc:
            await message.answer(f"❌ Ошибка при обновлении курса: {exc}")
        await state.clear()
        return

    await state.update_data(title=title)
    await message.answer("Введите полное описание курса (текст). Для пропуска отправьте /skip")
    await state.set_state(CourseStates.waiting_for_description)


@dp.message(CourseStates.waiting_for_description, F.text)
async def course_waiting_description(message: Message, state: FSMContext):
    description = message.text.strip()
    await state.update_data(description=description)
    await message.answer("Добавьте фотографию курса (отправьте фото) или отправьте /skip чтобы пропустить")
    await state.set_state(CourseStates.waiting_for_photo)


@dp.message(CourseStates.waiting_for_photo, F.photo | F.text)
async def course_waiting_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    editing_course_id = data.get("editing_course_id")

    photo_file_id = None
    if message.photo:
        photo_file_id = message.photo[-1].file_id
    elif message.text and message.text.strip().lower() == "/skip":
        photo_file_id = None
    else:
        await message.answer("Отправьте фото или /skip")
        return

    if editing_course_id:
        try:
            if photo_file_id:
                await services.set_course_photo(db_pool, editing_course_id, photo_file_id)
                await message.answer("✅ Фото курса обновлено.")
            else:
                await message.answer("❌ Фото не было отправлено.")
        except Exception as exc:
            await message.answer(f"❌ Ошибка при обновлении фото: {exc}")
        await state.clear()
        return

    lang = data.get("lang")
    slug = data.get("slug")
    title = data.get("title")
    description = data.get("description")

    if not all([lang, slug, title]):
        await message.answer("❌ Не хватает данных для создания курса. Начните заново.")
        await state.clear()
        return

    try:
        course_id = await services.create_course(
            db_pool,
            slug,
            lang,
            title,
            description or "",
            photo_file_id,
        )
    except Exception as exc:
        await message.answer(f"❌ Ошибка при создании курса: {exc}")
        await state.clear()
        return

    await state.clear()
    await message.answer(f"✅ Курс создан (ID: {course_id}).")


@dp.callback_query(F.data.startswith("admin_course:"))
async def admin_course_view(callback: CallbackQuery):
    if not await services.is_admin(db_pool, callback.from_user.id):
        await safe_callback_answer(callback, "⚠️ У вас нет прав администратора.", show_alert=True)
        return

    course_id = int(callback.data.split(":", 1)[1])
    course = await services.get_course_by_id(db_pool, course_id)
    if not course:
        await safe_callback_answer(callback, "Курс не найден.", show_alert=True)
        return

    text = f"🎓 {course['title']}\n\n{course['description'] or ''}\n\n(lang: {course['lang']}, slug: {course['slug']})"
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Редактировать информацию", callback_data=f"admin_course_action:edit_info:{course_id}"),
                InlineKeyboardButton(text="🖼️ Изменить фото", callback_data=f"admin_course_action:change_photo:{course_id}"),
            ],
            [
                InlineKeyboardButton(text="🗑 Удалить фото", callback_data=f"admin_course_action:remove_photo:{course_id}"),
                InlineKeyboardButton(text="❌ Удалить курс", callback_data=f"admin_course_action:delete:{course_id}"),
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_manage_courses")],
        ]
    )

    if course["photo"]:
        try:
            await callback.message.answer_photo(photo=course["photo"], caption=text, reply_markup=kb)
        except Exception:
            await safe_edit_message(callback, text, reply_markup=kb)
    else:
        await safe_edit_message(callback, text, reply_markup=kb)

    await safe_callback_answer(callback)


@dp.callback_query(F.data.startswith("admin_course_action:"))
async def admin_course_action(callback: CallbackQuery, state: FSMContext):
    if not await services.is_admin(db_pool, callback.from_user.id):
        await safe_callback_answer(callback, "⚠️ У вас нет прав администратора.", show_alert=True)
        return

    _, action, course_id = callback.data.split(":", 2)
    course_id = int(course_id)

    if action == "edit_info":
        await state.update_data(editing_course_id=course_id)
        await callback.message.answer("Введите новое название курса (или отправьте /skip чтобы не менять):")
        await state.set_state(CourseStates.waiting_for_title)
    elif action == "change_photo":
        await state.update_data(editing_course_id=course_id)
        await callback.message.answer("Отправьте новое фото для курса:")
        await state.set_state(CourseStates.waiting_for_photo)
    elif action == "remove_photo":
        await services.remove_course_photo(db_pool, course_id)
        await safe_callback_answer(callback, "Фото удалено.")
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest:
            pass
    elif action == "delete":
        await services.delete_course(db_pool, course_id)
        await safe_callback_answer(callback, "Курс удалён.")
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest:
            pass
    else:
        await safe_callback_answer(callback)


@dp.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext):
    if not await services.is_admin(db_pool, callback.from_user.id):
        await safe_callback_answer(callback, "⚠️ У вас нет прав администратора.", show_alert=True)
        return

    await safe_edit_message(callback, "📣 Куда отправлять рассылку?", reply_markup=buttons.get_broadcast_mode_keyboard())
    await state.update_data(broadcast_all=False, selected_chat_ids=[])
    await safe_callback_answer(callback)


@dp.callback_query(F.data.startswith("broadcast_target:"))
async def broadcast_target(callback: CallbackQuery, state: FSMContext):
    if not await services.is_admin(db_pool, callback.from_user.id):
        await safe_callback_answer(callback, "⚠️ У вас нет прав администратора.", show_alert=True)
        return

    target = callback.data.split(":", 1)[1]
    if target == "all":
        await state.set_state(BroadcastStates.waiting_for_broadcast)
        await state.update_data(broadcast_all=True, selected_chat_ids=[])
        await callback.message.answer("📣 Теперь отправьте текст или фото для рассылки по всем группам.\n\nДля отмены напишите /cancel")
        await safe_callback_answer(callback)
        return

    chats = await services.get_registered_chats(db_pool)
    if not chats:
        await safe_callback_answer(callback, "📭 Нет подключённых групп.", show_alert=True)
        return

    await state.set_state(BroadcastStates.waiting_for_broadcast)
    await state.update_data(broadcast_all=False, selected_chat_ids=[])
    await render_broadcast_selection(callback, state)


async def render_broadcast_selection(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected_ids = {int(item) for item in data.get("selected_chat_ids", [])}
    chats = await services.get_registered_chats(db_pool)
    keyboard = buttons.get_broadcast_group_selection_keyboard(chats, selected_ids)
    await safe_edit_message(
        callback,
        "📣 Выберите группы для рассылки:\n\n✅ — выбрана, ⬜ — не выбрана",
        reply_markup=keyboard,
    )
    await safe_callback_answer(callback)


@dp.callback_query(F.data.startswith("broadcast_toggle:"))
async def broadcast_toggle(callback: CallbackQuery, state: FSMContext):
    if not await services.is_admin(db_pool, callback.from_user.id):
        await safe_callback_answer(callback, "⚠️ У вас нет прав администратора.", show_alert=True)
        return

    chat_id = int(callback.data.split(":", 1)[1])
    data = await state.get_data()
    selected = list(data.get("selected_chat_ids", []))

    if chat_id in selected:
        selected.remove(chat_id)
    else:
        selected.append(chat_id)

    await state.update_data(selected_chat_ids=selected)
    await render_broadcast_selection(callback, state)


@dp.callback_query(F.data == "broadcast_send_selected")
async def broadcast_send_selected(callback: CallbackQuery, state: FSMContext):
    if not await services.is_admin(db_pool, callback.from_user.id):
        await safe_callback_answer(callback, "⚠️ У вас нет прав администратора.", show_alert=True)
        return

    selected = [int(item) for item in (await state.get_data()).get("selected_chat_ids", [])]
    if not selected:
        await safe_callback_answer(callback, "Выберите хотя бы одну группу.", show_alert=True)
        return

    await state.update_data(broadcast_all=False)
    await callback.message.answer("📣 Теперь отправьте текст или фото для выбранных групп.\n\nДля отмены напишите /cancel")
    await state.set_state(BroadcastStates.waiting_for_broadcast)
    await safe_callback_answer(callback)


@dp.message(BroadcastStates.waiting_for_broadcast, F.text | F.photo)
async def process_broadcast_message(message: Message, state: FSMContext):
    if not await services.is_admin(db_pool, message.from_user.id):
        await message.answer("⚠️ У вас нет прав на рассылку.")
        return

    if message.text and message.text.strip().lower() == "/cancel":
        await state.clear()
        await message.answer("❌ Рассылка отменена.")
        return

    text = message.caption if message.photo else message.text
    photo_file_id = message.photo[-1].file_id if message.photo else None

    if not text and not photo_file_id:
        await message.answer("❌ Нечего отправлять. Пришлите текст или фото.")
        return

    state_data = await state.get_data()
    chats = await services.get_broadcast_chat_ids(db_pool) if state_data.get("broadcast_all") else [
        int(item) for item in state_data.get("selected_chat_ids", [])
    ]

    if not chats:
        await state.clear()
        await message.answer("📭 Нет групп для рассылки.")
        return

    sent_count = 0
    failed_count = 0

    for chat_id in chats:
        try:
            if photo_file_id and text:
                await bot.send_photo(chat_id, photo=photo_file_id, caption=text)
            elif photo_file_id:
                await bot.send_photo(chat_id, photo=photo_file_id)
            elif text:
                await bot.send_message(chat_id, text)
            sent_count += 1
        except Exception:
            failed_count += 1

    await state.clear()
    await message.answer(
        f"✅ Рассылка завершена.\n"
        f"Отправлено в {sent_count} чатов.\n"
        f"Не доставлено: {failed_count}."
    )


@dp.callback_query(F.data.startswith("ticket_select:"))
async def ticket_select(callback: CallbackQuery):
    if not await services.is_admin(db_pool, callback.from_user.id):
        await safe_callback_answer(callback, "⚠️ У вас нет прав администратора.", show_alert=True)
        return

    ticket_id = int(callback.data.split(":", 1)[1])
    ticket = await services.get_ticket_by_id(db_pool, ticket_id)
    if not ticket:
        await safe_callback_answer(callback, "⚠️ Обращение не найдено.", show_alert=True)
        return

    message_text = (
        f"🧾 *Обращение #{ticket['ticket_id']}*\n\n"
        f"👤 *От:* {ticket['user_name']} (ID: `{ticket['user_id']}`)\n"
        f"🕒 *Дата:* {ticket['created_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
        f"📝 *Текст:*\n_{ticket['question']}_"
    )

    if ticket.get("photo"):
        try:
            await callback.message.answer_photo(
                photo=ticket["photo"],
                caption=message_text,
                parse_mode="Markdown",
                reply_markup=buttons.get_ticket_detail_keyboard(ticket_id),
            )
            await safe_callback_answer(callback)
            return
        except Exception:
            pass

    await safe_edit_message(
        callback,
        message_text,
        parse_mode="Markdown",
        reply_markup=buttons.get_ticket_detail_keyboard(ticket_id),
    )
    await safe_callback_answer(callback)


@dp.message(Command("help"))
async def cmd_help(message: Message):
    if is_group_chat(message.chat):
        return

    await message.answer(
        "📚 *Инструкция по использованию бота SoftClub Support*\n\n"
        "Этот бот — прямая связь с администрацией учебного центра.\n\n"
        "👉 Чтобы отправить вопрос, отзыв или жалобу, нажмите /report.\n"
        "👉 Чтобы перезапустить бота, нажмите /start.\n"
        "👉 Чтобы посмотреть информацию про курсы, используйте /courses",
        parse_mode="Markdown",
    )


@dp.message(Command("report"))
async def cmd_report(message: Message, state: FSMContext):
    if is_group_chat(message.chat):
        return

    await services.save_or_update_user(db_pool, message.from_user.id, message.from_user.full_name)
    await message.answer("📝 Пожалуйста, напишите ваш вопрос или жалобу в одном текстовом сообщении 👇\n\nДля отмены напишите /cancel")
    await state.set_state(ReportStates.waiting_for_question)


@dp.message(Command("cancel"))
@dp.message(Command("cancle"))
async def cancel_report(message: Message, state: FSMContext):
    if is_group_chat(message.chat):
        return

    current_state = await state.get_state()
    if current_state == ReportStates.waiting_for_question:
        await state.clear()
        await message.answer("❌ Вы отменили отправку обращения. Можно начать заново через /report")
        return

    await message.answer("❌ Нет активной формы для отмены. Чтобы отправить обращение, используйте /report")


@dp.message(ReportStates.waiting_for_question, F.text | F.photo)
async def process_question(message: Message, state: FSMContext):
    if is_group_chat(message.chat):
        await state.clear()
        return

    question_text = message.caption if message.photo else message.text
    if not question_text:
        question_text = "Пользователь отправил фото без текста."

    user_id = message.from_user.id
    user_name = message.from_user.full_name
    photo_file_id = message.photo[-1].file_id if message.photo else None

    await state.clear()
    ticket_id = await services.create_ticket(db_pool, user_id, user_name, question_text, photo_file_id)

    await message.answer(
        f"✅ Спасибо! Ваш вопрос принят (ID обращения: #{ticket_id}).\n"
        "Администрация свяжется с вами в ближайшее время. 👍"
    )

    admins = await services.get_all_admins(db_pool)
    if not admins:
        return

    admin_message_text = (
        f"✉️ *Новое обращение #{ticket_id}*\n\n"
        f"👤 *От:* {user_name} (ID: `{user_id}`)\n"
        f"📝 *Текст:*\n_{question_text}_"
    )

    for admin_id in admins:
        try:
            if photo_file_id:
                await bot.send_photo(
                    admin_id,
                    photo=photo_file_id,
                    caption=admin_message_text,
                    parse_mode="Markdown",
                    reply_markup=buttons.get_admin_action_keyboard(ticket_id),
                )
            else:
                await bot.send_message(
                    admin_id,
                    admin_message_text,
                    parse_mode="Markdown",
                    reply_markup=buttons.get_admin_action_keyboard(ticket_id),
                )
        except Exception as exc:
            print(f"Ошибка отправки админу {admin_id}: {exc}")


@dp.callback_query(F.data.startswith("skip_tk:"))
async def process_skip_callback(callback: CallbackQuery):
    if callback.message is None:
        return

    text = callback.message.text or ""
    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=f"{text}\n\n⏩ _Администратор {callback.from_user.full_name} пропустил это обращение._",
        parse_mode="Markdown",
    )
    await callback.answer("Тикет пропущен.")


@dp.callback_query(F.data.startswith("reply_tk:"))
async def process_reply_callback(callback: CallbackQuery, state: FSMContext):
    if not await services.is_admin(db_pool, callback.from_user.id):
        await callback.answer("⚠️ Вы не являетесь администратором.", show_alert=True)
        return

    ticket_id = int(callback.data.split(":", 1)[1])
    ticket = await services.get_ticket_by_id(db_pool, ticket_id)
    if not ticket:
        await callback.answer("⚠️ Обращение не найдено.", show_alert=True)
        return

    if ticket["status"] == "closed":
        await callback.answer("⚠️ На это обращение уже ответили.", show_alert=True)
        try:
            await bot.edit_message_reply_markup(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                reply_markup=None,
            )
        except TelegramBadRequest:
            pass
        return

    await callback.message.answer(f"⌨️ Введите ответ на обращение #{ticket_id}:")
    await state.update_data(answering_ticket_id=ticket_id, original_message_id=callback.message.message_id)
    await state.set_state(AdminStates.waiting_for_answer)
    await callback.answer()


@dp.message(AdminStates.waiting_for_answer, F.text | F.photo)
async def process_admin_answer(message: Message, state: FSMContext):
    # allow admins to reply with text, photo, or both
    text_part = (message.text or "").strip()
    photo_file_id = message.photo[-1].file_id if message.photo else None

    if not text_part and not photo_file_id:
        await message.answer("❌ Ответ не может быть пустым. Отправьте текст или фото.")
        return

    state_data = await state.get_data()
    ticket_id = state_data.get("answering_ticket_id")
    original_message_id = state_data.get("original_message_id")
    admin_id = message.from_user.id
    admin_name = message.from_user.full_name

    await state.clear()

    if ticket_id is None:
        await message.answer("❌ Ошибка: обращение не найдено.")
        return

    ticket = await services.get_ticket_by_id(db_pool, ticket_id)
    if not ticket:
        await message.answer("❌ Ошибка: обращение не найдено.")
        return

    # save ticket close with the text part (if any)
    await services.close_ticket(db_pool, ticket_id, admin_id, text_part or "(ответ приложен в виде фото)")
    await message.answer(f"✅ Ваш ответ на обращение #{ticket_id} успешно отправлен пользователю.")

    try:
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=original_message_id,
            text=f"{ticket['question']}\n\n✅ _Администратор {admin_name} ответил на это обращение._",
            parse_mode="Markdown",
        )
    except TelegramBadRequest:
        pass

    user_reply_caption = None
    if text_part and photo_file_id:
        # prefer using admin text as caption for the photo
        user_reply_caption = f"💬 *Ответ администрации SoftClub по вашему обращению #{ticket_id}*\n\n_{text_part}_"
    elif text_part:
        user_reply_caption = (
            f"💬 *Ответ администрации SoftClub по вашему обращению #{ticket_id}*\n\n_{text_part}_\n\n"
            "Надеемся, мы смогли вам помочь! 😊"
        )

    try:
        if photo_file_id:
            await bot.send_photo(
                ticket["user_id"],
                photo=photo_file_id,
                caption=user_reply_caption or f"💬 Ответ администрации (#{ticket_id})",
                parse_mode="Markdown" if user_reply_caption else None,
            )
        elif user_reply_caption:
            await bot.send_message(ticket["user_id"], user_reply_caption, parse_mode="Markdown")
    except Exception:
        await message.answer("⚠️ Не удалось доставить ответ пользователю.")


async def main():
    global db_pool
    db_pool = await sql.connect()
    await sql.create_tables(db_pool)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())