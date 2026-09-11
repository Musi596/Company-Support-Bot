import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from bot import services, buttons, sql
from bot.fsm import ReportStates, AdminStates, CourseStates, BroadcastStates

API_TOKEN = os.getenv('API_TOKEN')
if not API_TOKEN:
    raise RuntimeError('API_TOKEN is not set in environment')

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


def is_group_chat(chat) -> bool:
    return chat.type in {'group', 'supergroup', 'channel'}


@dp.message(Command("add_group"))
async def add_group_to_broadcast(message: Message):
    if message.chat.type not in {'group', 'supergroup', 'channel'}:
        await message.answer("⚠️ Вы не находитесь в группе. Команда /add_group доступна только внутри группы.")
        return

    pool = db_pool
    if not await services.is_admin(pool, message.from_user.id):
        await message.answer("⚠️ Только администратор бота может подключать эту группу к рассылке.")
        return

    await services.save_or_update_chat(
        pool,
        message.chat.id,
        message.chat.type,
        message.chat.title or message.chat.username
    )

    await message.answer(
        "✅ Группа добавлена в список для рассылок. "
        "Теперь бот сможет отправлять сюда сообщения."
    )


@dp.message(Command("courses"))
async def cmd_courses(message: Message):
    if is_group_chat(message.chat):
        return

    await message.answer(
        "Выберите язык, на котором хотите узнать о курсах:",
        reply_markup=buttons.get_courses_language_keyboard()
    )


@dp.callback_query(F.data == "courses_menu")
async def courses_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "Выберите язык, на котором хотите узнать о курсах:",
        reply_markup=buttons.get_courses_language_keyboard()
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("courses_lang:"))
async def courses_language(callback: CallbackQuery):
    lang = callback.data.split(":")[1]
    language_names = {
        "tj": "Тоҷикӣ",
        "ru": "Русский",
        "en": "English",
    }
    titles = {
        "tj": "Выберите курс на языке Тоҷикӣ:",
        "ru": "Выберите курс:",
        "en": "Choose a course:",
    }

    pool = db_pool
    courses = await services.get_courses_by_lang(pool, lang)

    if not courses:
        await callback.message.edit_text(
            "Пока нет курсов для выбранного языка.",
            reply_markup=buttons.get_courses_back_keyboard()
        )
        await callback.answer()
        return

    rows = []
    current = []
    for c in courses:
        current.append(InlineKeyboardButton(text=c['title'], callback_data=f"courses_course:{lang}:{c['slug']}"))
        if len(current) == 2:
            rows.append(current)
            current = []
    if current:
        rows.append(current)

    rows.append([InlineKeyboardButton(text="🔙 Назад к выбору языка", callback_data="courses_menu")])

    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    await callback.message.edit_text(titles.get(lang, "Выберите курс:"), reply_markup=kb)
    await callback.answer()


@dp.callback_query(F.data.startswith("courses_list:"))
async def courses_list(callback: CallbackQuery):
    lang = callback.data.split(":")[1]
    titles = {
        "tj": "Выберите курс на языке Тоҷикӣ:",
        "ru": "Выберите курс:",
        "en": "Choose a course:",
    }

    pool = db_pool
    courses = await services.get_courses_by_lang(pool, lang)

    if not courses:
        await callback.message.edit_text(
            "Пока нет курсов для выбранного языка.",
            reply_markup=buttons.get_courses_back_keyboard()
        )
        await callback.answer()
        return

    rows = []
    current = []
    for c in courses:
        current.append(InlineKeyboardButton(text=c['title'], callback_data=f"courses_course:{lang}:{c['slug']}"))
        if len(current) == 2:
            rows.append(current)
            current = []
    if current:
        rows.append(current)

    rows.append([InlineKeyboardButton(text="🔙 Назад к выбору языка", callback_data="courses_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=rows)

    await callback.message.edit_text(titles.get(lang, "Выберите курс:"), reply_markup=kb)
    await callback.answer()


@dp.callback_query(F.data.startswith("courses_course:"))
async def courses_detail(callback: CallbackQuery):
    _, lang, course_id = callback.data.split(":", 2)
    pool = db_pool
    course = await services.get_course_by_slug(pool, course_id, lang)
    if course:
        text = course['description'] or course['title']
        kb = buttons.get_courses_detail_keyboard(lang)
        if course['photo']:
            try:
                await callback.message.answer_photo(photo=course['photo'], caption=text, reply_markup=kb)
                await callback.answer()
                return
            except Exception:
                pass
        await callback.message.edit_text(text, reply_markup=kb)
        await callback.answer()
        return
    await callback.answer("Курс не найден.", show_alert=True)


@dp.message(CommandStart())
async def cmd_start(message: Message):
    if is_group_chat(message.chat):
        return

    pool = db_pool
    await services.save_or_update_user(pool, message.from_user.id, message.from_user.full_name)

    is_admin = await services.is_admin(pool, message.from_user.id)
    if is_admin:
        await message.answer_sticker(
            sticker='CAACAgIAAxkBAAER3dRqns8OAAFAJ_41_64myZOJ35l9DIQAAkaFAAJtfQABSYjWiVDXg4rkPQQ'
        )
        await message.answer(
            "👑 *Добро пожаловать, администратор!*\n\n"
            "Вы можете просматривать новые вопросы и жалобы, отвечать на них и закрывать обращения.",
            parse_mode="Markdown",
            reply_markup=buttons.get_admin_main_keyboard()
        )
        return

    await message.answer_sticker(
        sticker='CAACAgIAAxkBAAER3dRqns8OAAFAJ_41_64myZOJ35l9DIQAAkaFAAJtfQABSYjWiVDXg4rkPQQ'
    )

    await message.answer(
        "✨ *Добро пожаловать в SoftClub!* 🚀\n\n"
        "Рады видеть вас в нашем учебном центре программирования! "
        "Мы создаем условия для эффективного старта и развития в IT.\n\n"
        "📌 *Основные команды:*\n\n"
        "📚 /help — Узнать о SoftClub и боте\n"
        "📝 /report — Отправить вопрос или жалобу администрации\n\n"
        "💡 _Выберите нужную команду выше или введите её._",
        parse_mode="Markdown"
    )


@dp.callback_query(F.data == "admin_open_tickets")
async def admin_open_tickets(callback: CallbackQuery):
    pool = db_pool
    admin_id = callback.from_user.id

    if not await services.is_admin(pool, admin_id):
        await callback.answer("⚠️ У вас нет прав администратора.", show_alert=True)
        return

    tickets = await services.get_open_tickets(pool)
    if not tickets:
        await callback.message.edit_text(
            "📭 Нет новых вопросов и жалоб. Все обращения уже закрыты.",
            reply_markup=buttons.get_admin_main_keyboard()
        )
        await callback.answer("Нет новых обращений.")
        return

    ticket_lines = []
    for ticket in tickets:
        preview = ticket['question'].replace('\n', ' ')[:70]
        if len(ticket['question']) > 70:
            preview += '...'
        ticket_lines.append(f"#{ticket['ticket_id']} • {ticket['user_name']} • {preview}")

    text = "📋 *Неотвеченные вопросы и жалобы:*\n\n" + "\n".join(ticket_lines)
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=buttons.get_admin_ticket_list_keyboard(tickets))
    await callback.answer()


@dp.callback_query(F.data == "admin_manage_courses")
async def admin_manage_courses(callback: CallbackQuery):
    pool = db_pool
    admin_id = callback.from_user.id

    if not await services.is_admin(pool, admin_id):
        await callback.answer("⚠️ У вас нет прав администратора.", show_alert=True)
        return

    courses = await services.get_courses_by_lang(pool, 'ru')
    courses += await services.get_courses_by_lang(pool, 'en')
    courses += await services.get_courses_by_lang(pool, 'tj')

    keyboard_rows = []
    keyboard_rows.append([
        InlineKeyboardButton(text="➕ Добавить курс", callback_data="admin_add_course")
    ])

    for c in courses:
        keyboard_rows.append([
            InlineKeyboardButton(text=f"{c['lang']} • {c['slug']} — {c['title']}", callback_data=f"admin_course:{c['course_id']}")
        ])

    keyboard_rows.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_open_tickets")
    ])

    kb = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
    await callback.message.edit_text("🛠 Управление курсами:", reply_markup=kb)
    await callback.answer()


@dp.callback_query(F.data == "admin_add_course")
async def admin_add_course_start(callback: CallbackQuery, state: FSMContext):
    pool = db_pool
    if not await services.is_admin(pool, callback.from_user.id):
        await callback.answer("⚠️ У вас нет прав администратора.", show_alert=True)
        return

    await callback.message.answer("📥 Введите язык курса (ru / tj / en):")
    await state.set_state(CourseStates.waiting_for_lang)
    await callback.answer()


@dp.message(CourseStates.waiting_for_lang, F.text)
async def course_waiting_lang(message: Message, state: FSMContext):
    lang = message.text.strip().lower()
    if lang not in ('ru', 'tj', 'en'):
        await message.answer("Неверный язык. Введите один из: ru, tj, en")
        return
    await state.update_data(lang=lang)
    await message.answer("Введите уникальный идентификатор курса (slug), например: python или ai")
    await state.set_state(CourseStates.waiting_for_slug)


@dp.message(CourseStates.waiting_for_slug, F.text)
async def course_waiting_slug(message: Message, state: FSMContext):
    slug = message.text.strip()
    await state.update_data(slug=slug)
    await message.answer("Введите заголовок курса (короткое название):")
    await state.set_state(CourseStates.waiting_for_title)


@dp.message(CourseStates.waiting_for_title, F.text)
async def course_waiting_title(message: Message, state: FSMContext):
    title = message.text.strip()
    data = await state.get_data()
    editing_course_id = data.get('editing_course_id')

    if editing_course_id:
        pool = db_pool
        try:
            await services.update_course(pool, editing_course_id, title=title)
            await message.answer("✅ Название курса обновлено.")
        except Exception as e:
            await message.answer(f"❌ Ошибка при обновлении курса: {e}")
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
    pool = db_pool
    data = await state.get_data()
    lang = data.get('lang')
    slug = data.get('slug')
    title = data.get('title')
    description = data.get('description')
    editing_course_id = data.get('editing_course_id')

    photo_file_id = None
    if message.photo:
        photo_file_id = message.photo[-1].file_id
    elif message.text and message.text.strip().lower() == '/skip':
        photo_file_id = None
    else:
        await message.answer("Отправьте фото или /skip")
        return

    if editing_course_id:
        try:
            if photo_file_id:
                await services.set_course_photo(pool, editing_course_id, photo_file_id)
                await message.answer("✅ Фото курса обновлено.")
            else:
                await message.answer("❌ Фото не было отправлено.")
        except Exception as e:
            await message.answer(f"❌ Ошибка при обновлении фото: {e}")
        await state.clear()
        return

    try:
        course_id = await services.create_course(pool, slug, lang, title, description, photo_file_id)
    except Exception as e:
        await message.answer(f"❌ Ошибка при создании курса: {e}")
        await state.clear()
        return

    await state.clear()
    await message.answer(f"✅ Курс создан (ID: {course_id}).")


@dp.callback_query(F.data.startswith("admin_course:"))
async def admin_course_view(callback: CallbackQuery):
    pool = db_pool
    admin_id = callback.from_user.id
    if not await services.is_admin(pool, admin_id):
        await callback.answer("⚠️ У вас нет прав администратора.", show_alert=True)
        return

    course_id = int(callback.data.split(":", 1)[1])
    course = await services.get_course_by_id(pool, course_id)
    if not course:
        await callback.answer("Курс не найден.", show_alert=True)
        return

    text = f"🎓 {course['title']}\n\n{course['description'] or ''}\n\n(lang: {course['lang']}, slug: {course['slug']})"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Редактировать информацию", callback_data=f"admin_course_action:edit_info:{course_id}"), InlineKeyboardButton(text="🖼️ Изменить фото", callback_data=f"admin_course_action:change_photo:{course_id}")],
        [InlineKeyboardButton(text="🗑 Удалить фото", callback_data=f"admin_course_action:remove_photo:{course_id}"), InlineKeyboardButton(text="❌ Удалить курс", callback_data=f"admin_course_action:delete:{course_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_manage_courses")]
    ])

    if course['photo']:
        try:
            await callback.message.answer_photo(photo=course['photo'], caption=text, reply_markup=kb)
        except Exception:
            await callback.message.edit_text(text, reply_markup=kb)
    else:
        await callback.message.edit_text(text, reply_markup=kb)

    await callback.answer()


@dp.callback_query(F.data.startswith("admin_course_action:"))
async def admin_course_action(callback: CallbackQuery, state: FSMContext):
    pool = db_pool
    admin_id = callback.from_user.id
    if not await services.is_admin(pool, admin_id):
        await callback.answer("⚠️ У вас нет прав администратора.", show_alert=True)
        return

    _, action, course_id = callback.data.split(":", 2)
    course_id = int(course_id)

    if action == 'edit_info':
        await state.update_data(editing_course_id=course_id)
        await callback.message.answer("Введите новое название курса (или отправьте /skip чтобы не менять):")
        await state.set_state(CourseStates.waiting_for_title)
    elif action == 'change_photo':
        await state.update_data(editing_course_id=course_id)
        await callback.message.answer("Отправьте новое фото для курса:")
        await state.set_state(CourseStates.waiting_for_photo)
    elif action == 'remove_photo':
        await services.remove_course_photo(pool, course_id)
        await callback.answer("Фото удалено.")
        await callback.message.edit_reply_markup(reply_markup=None)
    elif action == 'delete':
        await services.delete_course(pool, course_id)
        await callback.answer("Курс удалён.")
        await callback.message.edit_reply_markup(reply_markup=None)
    else:
        await callback.answer()


@dp.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext):
    pool = db_pool
    admin_id = callback.from_user.id

    if not await services.is_admin(pool, admin_id):
        await callback.answer("⚠️ У вас нет прав администратора.", show_alert=True)
        return

    await callback.message.answer(
        "📣 Отправьте сообщение для рассылки по всем группам, где есть бот.\n\n"
        "Можно отправить: \n"
        "- только текст;\n"
        "- только фото;\n"
        "- фото с текстом в подписи.\n\n"
        "Для отмены напишите /cancel"
    )
    await state.set_state(BroadcastStates.waiting_for_broadcast)
    await callback.answer()


@dp.message(BroadcastStates.waiting_for_broadcast, F.text | F.photo)
async def process_broadcast_message(message: Message, state: FSMContext):
    pool = db_pool
    if not await services.is_admin(pool, message.from_user.id):
        await message.answer("⚠️ У вас нет прав на рассылку.")
        return

    if message.text and message.text.strip().lower() == '/cancel':
        await state.clear()
        await message.answer("❌ Рассылка отменена.")
        return

    text = message.caption if message.photo else message.text
    photo_file_id = message.photo[-1].file_id if message.photo else None

    if not text and not photo_file_id:
        await message.answer("❌ Нечего отправлять. Пришлите текст или фото.")
        return

    chats = await services.get_broadcast_chat_ids(pool)
    if not chats:
        await state.clear()
        await message.answer("📭 В базе нет групп, куда можно отправить рассылку.")
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
    pool = db_pool
    ticket_id = int(callback.data.split(':')[1])

    if not await services.is_admin(pool, callback.from_user.id):
        await callback.answer("⚠️ У вас нет прав администратора.", show_alert=True)
        return

    ticket = await services.get_ticket_by_id(pool, ticket_id)
    if not ticket:
        await callback.answer("⚠️ Обращение не найдено.", show_alert=True)
        return

    message_text = (
        f"🧾 *Обращение #{ticket['ticket_id']}*\n\n"
        f"👤 *От:* {ticket['user_name']} (ID: `{ticket['user_id']}`)\n"
        f"🕒 *Дата:* {ticket['created_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
        f"📝 *Текст:*\n_{ticket['question']}_"
    )
    await callback.message.edit_text(message_text, parse_mode="Markdown", reply_markup=buttons.get_ticket_detail_keyboard(ticket_id))
    await callback.answer()


@dp.message(Command("help"))
async def cmd_help(message: Message):
    if is_group_chat(message.chat):
        return

    await message.answer("📚 *Инструкция по использованию бота SoftClub Support*\n\n"
                         "Этот бот — прямая связь с администрацией учебного центра.\n\n"
                         "👉 Чтобы отправить вопрос, отзыв или жалобу, нажмите /report.\n"
                         "👉 Чтобы перезапустить бота, нажмите /start.\n"
                         "👉 Чтобы посмотреть информацию про курсы /courses",parse_mode='Markdown')

@dp.message(Command("report"))
async def cmd_report(message: Message, state: FSMContext):
    if is_group_chat(message.chat):
        return

    pool = db_pool
    await services.save_or_update_user(pool, message.from_user.id, message.from_user.full_name)
    await message.answer("📝 Пожалуйста, напишите ваш вопрос или жалобу в одном текстовом сообщении 👇")
    await state.set_state(ReportStates.waiting_for_question)

@dp.message(ReportStates.waiting_for_question, F.text)
async def process_question(message: Message, state: FSMContext):
    if is_group_chat(message.chat):
        await state.clear()
        return

    pool = db_pool
    question_text = message.text
    user_id = message.from_user.id
    user_name = message.from_user.full_name

    await state.clear()
    ticket_id = await services.create_ticket(pool, user_id, user_name, question_text)

    await message.answer(
        f"✅ Спасибо! Ваш вопрос принят (ID обращения: #{ticket_id}).\n"
        f"Администрация свяжется с вами в ближайшее время. 👍"
    )

    admins = await services.get_all_admins(pool)
    if not admins:
        return

    admin_message_text = (
        f"✉️ *Новое обращение #{ticket_id}*\n\n"
        f"👤 *От:* {user_name} (ID: `{user_id}`)\n"
        f"📝 *Текст:*\n_{question_text}_"
    )

    for admin_id in admins:
        try:
            await bot.send_message(
                admin_id,
                admin_message_text,
                parse_mode="Markdown",
                reply_markup=buttons.get_admin_action_keyboard(ticket_id)
            )
        except Exception as e:
            print(f"Ошибка отправки админу {admin_id}: {e}")

@dp.callback_query(F.data.startswith("skip_tk:"))
async def process_skip_callback(callback: CallbackQuery):
    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=f"{callback.message.text}\n\n⏩ _Администратор {callback.from_user.full_name} пропустил это обращение._",
        parse_mode="Markdown"
    )
    await callback.answer("Тикет пропущен.")

@dp.callback_query(F.data.startswith("reply_tk:"))
async def process_reply_callback(callback: CallbackQuery, state: FSMContext):
    pool = db_pool
    ticket_id = int(callback.data.split(':')[1])
    admin_id = callback.from_user.id
    
    if not await services.is_admin(pool, admin_id):
        await callback.answer("⚠️ Вы не являетесь администратором.", show_alert=True)
        return

    ticket = await services.get_ticket_by_id(pool, ticket_id)
    if ticket['status'] == 'closed':
        await callback.answer("⚠️ На это обращение уже ответили.", show_alert=True)
        await bot.edit_message_reply_markup(chat_id=admin_id, message_id=callback.message.message_id, reply_markup=None)
        return

    await callback.message.answer(f"⌨️ Введите ответ на обращение #{ticket_id}:")
    await state.update_data(answering_ticket_id=ticket_id, original_message_id=callback.message.message_id)
    await state.set_state(AdminStates.waiting_for_answer)
    await callback.answer()

@dp.message(AdminStates.waiting_for_answer, F.text)
async def process_admin_answer(message: Message, state: FSMContext):
    pool = db_pool
    answer_text = message.text
    admin_id = message.from_user.id
    admin_name = message.from_user.full_name

    state_data = await state.get_data()
    ticket_id = state_data.get("answering_ticket_id")
    original_message_id = state_data.get("original_message_id")

    await state.clear()

    ticket = await services.get_ticket_by_id(pool, ticket_id)
    if not ticket:
        await message.answer("❌ Ошибка: обращение не найдено.")
        return
    
    user_id_to_reply = ticket['user_id']
    await services.close_ticket(pool, ticket_id, admin_id, answer_text)

    await message.answer(f"✅ Ваш ответ на обращение #{ticket_id} успешно отправлен пользователю.")
    
    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=original_message_id,
        text=f"{ticket['question']}\n\n✅ _Администратор {admin_name} ответил на это обращение._",
        parse_mode="Markdown"
    )

    user_reply_text = (
        f"💬 *Ответ администрации SoftClub по вашему обращению #{ticket_id}*\n\n"
        f"_{answer_text}_\n\n"
        f"Надеемся, мы смогли вам помочь! 😊"
    )
    
    try:
        await bot.send_message(user_id_to_reply, user_reply_text, parse_mode="Markdown")
    except Exception:
        await message.answer("⚠️ Не удалось доставить ответ пользователю.")

async def main():
    global db_pool
    pool = await sql.connect()
    db_pool = pool
    await sql.create_tables(pool)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())