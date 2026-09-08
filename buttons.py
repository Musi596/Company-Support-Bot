from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_admin_action_keyboard(ticket_id: int) -> InlineKeyboardMarkup:
    btn_reply = InlineKeyboardButton(text="💬 Ответить", callback_data=f"reply_tk:{ticket_id}")
    btn_skip = InlineKeyboardButton(text="⏩ Пропустить", callback_data=f"skip_tk:{ticket_id}")
    return InlineKeyboardMarkup(inline_keyboard=[[btn_reply, btn_skip]])