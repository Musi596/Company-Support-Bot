import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import sql
import services
import buttons

load_dotenv()

bot = Bot(token=os.getenv('API_TOKEN'))
dp = Dispatcher()
db_pool = None

class ReportStates(StatesGroup):
    waiting_for_question = State()

class AdminStates(StatesGroup):
    waiting_for_answer = State()

class BroadcastStates(StatesGroup):
    waiting_for_broadcast = State()


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

    if lang == "tj":
        text = """🚀 Омӯзиши IT ва Технологияҳои Муосир!

Ояндаи худро аз ҳамин имрӯз созед! Мо барои шумо курсҳои актуалӣ ва пурмуҳтаворо омода намудем, ки дар онҳо на танҳо барномасозиву дизайн, балки истифодаи AI-ро низ меомӯзед.

1️⃣ Курси Асосҳои AI
- Тарзи дурусти навиштани Prompt
- Кор бо ChatGPT, Claude ва Gemini
- Автоматизатсия: Zapier, Make, n8n
- Моделҳои офлайн AI (LLaMA)
- Сохтани AI Agent-и шахсӣ
- AI барои кор бо матн, сурат ва видео
Давомнокӣ: 1 моҳ | Дарсҳо: 3 рӯз дар як ҳафта | Вақт: 18:00 – 20:00

2️⃣ Барномасозӣ аз 0
- C++
- HTML/CSS & GitHub
- Истифодаи AI барои омӯзиш
Давомнокӣ: 2 моҳ | Дарсҳо: 6 рӯз дар як ҳафта | Вақт: 16:00 – 18:00 | 18:00 – 20:00

3️⃣ Курси Python
- Python & PostgreSQL
- Telegram Bot & FastAPI
- Django REST Framework
- Clean Architecture
- AI Tools: ChatGPT, Claude, Gemini, Stitch AI, MCP Servers
Давомнокӣ: 5 моҳ | Дарсҳо: 6 рӯз дар як ҳафта | Вақт: 16:00 – 18:00 | 18:00 – 20:00

4️⃣ Курси Frontend
- JavaScript & React
- TypeScript & Next.js
- Clean Architecture
- AI Tools
Давомнокӣ: 5 моҳ | Дарсҳо: 6 рӯз дар як ҳафта | Вақт: 16:00 – 18:00 | 18:00 – 20:00

5️⃣ Курси Golang
- Golang & PostgreSQL
- Clean Architecture
- Microservices (gRPC) & Redis
- Deployment and DevOps foundation
- RabbitMQ & AI Tools
Давомнокӣ: 5 моҳ | Дарсҳо: 6 рӯз дар як ҳафта | Вақт: 18:00 – 20:00

6️⃣ Курси C#
- C# & PostgreSQL
- .NET Framework
- Clean Architecture
- AI Tools
Давомнокӣ: 5 моҳ | Дарсҳо: 6 рӯз дар як ҳафта | Вақт: 16:00 – 18:00 | 18:00 – 20:00

7️⃣ Mobile Development
- Dart & Flutter
- State Management
- Clean Architecture
- AI Tools
Давомнокӣ: 4 моҳ | Дарсҳо: 6 рӯз дар як ҳафта | Вақт: 16:00 – 18:00 | 18:00 – 20:00

8️⃣ Graphic Design & UX/UI
- Photoshop, CorelDRAW, Illustrator
- Blender, After Effects
- Figma
- Canva ва AI tools барои дизайнерҳо
Давомнокӣ: 4 моҳ | Дарсҳо: 6 рӯз дар як ҳафта | Вақт: 16:00 – 18:00 | 18:00 – 20:00

9️⃣ Компьютерная грамотность для сотрудников
- Word, Excel, PowerPoint
- Google Docs ва Canva
- Keyboard Skills
- AI дар фаъолияти корӣ
- Автоматизатсияи офисӣ
Давомнокӣ: 1 моҳ | Дарсҳо: 6 рӯз дар як ҳафта | Вақт: 14:00 – 16:00 | 16:00 – 18:00 | 18:00 – 20:00

🔗 Барои сабти ном ба линки дар шапкаи профил гузаред.
📩 Саволҳо доред? /report нависед диҳед ва мо бо омодагӣ ба шумо дар саволи шумо кӯмак хоҳем кард."""
    elif lang == "ru":
        text = """🚀 Обучение IT и Современным Технологиям!

Создай свое будущее уже сегодня! Мы подготовили актуальные и насыщенные курсы, где вы освоите не только программирование и дизайн, но и работу с AI.

1️⃣ Основы AI
- Prompt Engineering
- Работа с ChatGPT, Claude и Gemini
- Автоматизация: Zapier, Make, n8n
- Офлайн-модели (LLaMA)
- Создание собственного AI-агента
- AI для текста, изображений и видео
Длительность: 1 месяц | Занятия: 3 дня в неделю | Время: 18:00 – 20:00

2️⃣ Программирование с 0
- C++
- HTML/CSS & GitHub
- Использование AI для обучения
Длительность: 2 месяца | Занятия: 6 дней в неделю | Время: 16:00 – 18:00 | 18:00 – 20:00

3️⃣ Python Course
- Python & PostgreSQL
- Telegram Bot & FastAPI
- Django REST Framework
- Clean Architecture
- AI Tools: ChatGPT, Claude, Gemini, Stitch AI, MCP Servers
Длительность: 5 месяцев | Занятия: 6 дней в неделю | Время: 16:00 – 18:00 | 18:00 – 20:00

4️⃣ Frontend Course
- JavaScript & React
- TypeScript & Next.js
- Clean Architecture
- AI Tools
Длительность: 5 месяцев | Занятия: 6 дней в неделю | Время: 16:00 – 18:00 | 18:00 – 20:00

5️⃣ Golang Course
- Golang & PostgreSQL
- Clean Architecture
- Microservices (gRPC) & Redis
- Deployment and DevOps
- RabbitMQ & AI Tools
Длительность: 5 месяцев | Занятия: 6 дней в неделю | Время: 18:00 – 20:00

6️⃣ C# Course
- C# & PostgreSQL
- .NET Framework
- Clean Architecture
- AI Tools
Длительность: 5 месяцев | Занятия: 6 дней в неделю | Время: 16:00 – 18:00 | 18:00 – 20:00

7️⃣ Mobile Development
- Dart & Flutter
- State Management
- Clean Architecture
- AI Tools
Длительность: 4 месяца | Занятия: 6 дней в неделю | Время: 16:00 – 18:00 | 18:00 – 20:00

8️⃣ Graphic Design & UX/UI
- Photoshop, CorelDRAW, Illustrator
- Blender, After Effects
- Figma
- Canva и AI инструменты для дизайнеров
Длительность: 4 месяца | Занятия: 6 дней в неделю | Время: 16:00 – 18:00 | 18:00 – 20:00

9️⃣ Компьютерная грамотность для сотрудников
- Word, Excel, PowerPoint
- Google Docs и Canva
- Навыки работы с клавиатурой
- AI в ежедневной работе
- Автоматизация офисных задач
Длительность: 1 месяц | Занятия: 6 дней в неделю | Время: 14:00 – 16:00 | 16:00 – 18:00 | 18:00 – 20:00

🔗 Для регистрации переходите по ссылке в шапке профиля!
📩 Есть вопросы? Напишите /report и ваш вопрос будет рады помочь"""
    else:
        text = """🚀 Master IT & Modern Technologies!

Build your future today! We have prepared comprehensive, up-to-date courses where you will master not only programming and design, but also AI tools.

1️⃣ Fundamentals of AI
- Prompt Engineering
- ChatGPT, Claude, and Gemini
- Automation: Zapier, Make, n8n
- Offline AI Models (LLaMA)
- Building custom AI agents
- AI for text, image and video processing
Duration: 1 month | Schedule: 3 days per week | Time: 18:00 – 20:00

2️⃣ Programming from Scratch
- C++
- HTML/CSS & GitHub
- AI-powered learning
Duration: 2 months | Schedule: 6 days per week | Time: 16:00 – 18:00 | 18:00 – 20:00

3️⃣ Python Course
- Python & PostgreSQL
- Telegram Bot & FastAPI
- Django REST Framework
- Clean Architecture
- AI Tools: ChatGPT, Claude, Gemini, Stitch AI, MCP Servers
Duration: 5 months | Schedule: 6 days per week | Time: 16:00 – 18:00 | 18:00 – 20:00

4️⃣ Frontend Course
- JavaScript & React
- TypeScript & Next.js
- Clean Architecture
- Developer AI Tools
Duration: 5 months | Schedule: 6 days per week | Time: 16:00 – 18:00 | 18:00 – 20:00

5️⃣ Golang Course
- Golang & PostgreSQL
- Clean Architecture
- Microservices (gRPC) & Redis
- Deployment and DevOps
- RabbitMQ & AI Tools
Duration: 5 months | Schedule: 6 days per week | Time: 18:00 – 20:00

6️⃣ C# Course
- C# & PostgreSQL
- .NET Framework
- Clean Architecture
- AI Tools
Duration: 5 months | Schedule: 6 days per week | Time: 16:00 – 18:00 | 18:00 – 20:00

7️⃣ Mobile Development
- Dart & Flutter
- State Management
- Clean Architecture
- AI Tools
Duration: 4 months | Schedule: 6 days per week | Time: 16:00 – 18:00 | 18:00 – 20:00

8️⃣ Graphic Design & UX/UI
- Photoshop, CorelDRAW, Illustrator
- Blender & After Effects
- Figma
- Canva and AI tools for designers
Duration: 4 months | Schedule: 6 days per week | Time: 16:00 – 18:00 | 18:00 – 20:00

9️⃣ Computer Basics for Employees
- Word, Excel, PowerPoint
- Google Docs & Canva
- Keyboard mastery
- AI in daily work
- Office workflow automation
Duration: 1 month | Schedule: 6 days per week | Time: 14:00 – 16:00 | 16:00 – 18:00 | 18:00 – 20:00

🔗 Click the link in our bio to register!
📩 Have questions? Message /report and we will be happy to help you with your question."""

    await callback.message.edit_text(text, reply_markup=buttons.get_courses_back_keyboard())
    await callback.answer()


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