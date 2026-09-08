import asyncio
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, BotCommand
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import sql
import services
import buttons

load_dotenv()

bot = Bot(token=os.getenv('API_TOKEN'))
dp = Dispatcher()

class ReportStates(StatesGroup):
    waiting_for_question = State()

class AdminStates(StatesGroup):
    waiting_for_answer = State()

@dp.message(CommandStart())
async def cmd_start(message: Message):
    pool = dp['db_pool']
    await services.save_or_update_user(pool, message.from_user.id, message.from_user.full_name)
    
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

@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer("📚 *Инструкция по использованию бота SoftClub Support*\n\n"
                         "Этот бот — прямая связь с администрацией учебного центра.\n\n"
                         "👉 Чтобы отправить вопрос, отзыв или жалобу, нажмите /report.\n"
                         "👉 Чтобы перезапустить бота, нажмите /start.",parse_mode='Markdown')

@dp.message(Command("report"))
async def cmd_report(message: Message, state: FSMContext):
    pool = dp['db_pool']
    await services.save_or_update_user(pool, message.from_user.id, message.from_user.full_name)
    await message.answer("📝 Пожалуйста, напишите ваш вопрос или жалобу в одном текстовом сообщении 👇")
    await state.set_state(ReportStates.waiting_for_question)

@dp.message(ReportStates.waiting_for_question, F.text)
async def process_question(message: Message, state: FSMContext):
    pool = dp['db_pool']
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
    pool = dp['db_pool']
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
    pool = dp['db_pool']
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
    pool = await sql.connect()
    dp['db_pool'] = pool
    await sql.create_tables(pool)
    
    await bot.set_my_commands([
        BotCommand(command="start", description="Перезапустить бота"),
        BotCommand(command="help", description="Инструкция"),
        BotCommand(command="report", description="Отправить обращение")
    ])
    
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())