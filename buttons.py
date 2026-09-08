from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_admin_main_keyboard() -> InlineKeyboardMarkup:
    btn_view = InlineKeyboardButton(
        text="📋 Посмотреть вопросы и жалобы",
        callback_data="admin_open_tickets"
    )
    btn_broadcast = InlineKeyboardButton(
        text="📣 Рассылка",
        callback_data="admin_broadcast"
    )
    return InlineKeyboardMarkup(inline_keyboard=[[btn_view], [btn_broadcast]])


def get_admin_action_keyboard(ticket_id: int) -> InlineKeyboardMarkup:
    btn_reply = InlineKeyboardButton(text="💬 Ответить", callback_data=f"reply_tk:{ticket_id}")
    btn_skip = InlineKeyboardButton(text="⏩ Пропустить", callback_data=f"skip_tk:{ticket_id}")
    return InlineKeyboardMarkup(inline_keyboard=[[btn_reply, btn_skip]])


def get_admin_ticket_list_keyboard(tickets) -> InlineKeyboardMarkup:
    keyboard = []
    for ticket in tickets:
        keyboard.append([
            InlineKeyboardButton(
                text=f"#{ticket['ticket_id']} — {ticket['user_name']}",
                callback_data=f"ticket_select:{ticket['ticket_id']}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_ticket_detail_keyboard(ticket_id: int) -> InlineKeyboardMarkup:
    btn_reply = InlineKeyboardButton(text="💬 Ответить", callback_data=f"reply_tk:{ticket_id}")
    btn_back = InlineKeyboardButton(text="🔙 Назад", callback_data="admin_open_tickets")
    return InlineKeyboardMarkup(inline_keyboard=[[btn_reply], [btn_back]])