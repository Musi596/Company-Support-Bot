from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_admin_main_keyboard() -> InlineKeyboardMarkup:
    btn_view = InlineKeyboardButton(
        text="📋 Вопросы и жалобы",
        callback_data="admin_open_tickets"
    )
    btn_broadcast = InlineKeyboardButton(
        text="📣 Рассылка",
        callback_data="admin_broadcast"
    )
    btn_manage_courses = InlineKeyboardButton(
        text="🎓 Курсы",
        callback_data="admin_manage_courses"
    )
    btn_view_groups = InlineKeyboardButton(
        text="👥 Группы",
        callback_data="admin_view_groups"
    )
    return InlineKeyboardMarkup(inline_keyboard=[[btn_view, btn_broadcast], [btn_manage_courses, btn_view_groups]])


def get_group_list_keyboard(chats) -> InlineKeyboardMarkup:
    rows = []
    if chats:
        for chat in chats:
            title = chat['title'] or f"Группа {chat['chat_id']}"
            rows.append([
                InlineKeyboardButton(
                    text=f"🗑️ {title}",
                    callback_data=f"admin_group_delete:{chat['chat_id']}"
                )
            ])
    else:
        rows.append([
            InlineKeyboardButton(text="📭 Нет подключённых групп", callback_data="admin_view_groups")
        ])

    rows.append([
        InlineKeyboardButton(text="🔙 Назад в админку", callback_data="admin_open_tickets")
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_broadcast_mode_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🌍 Все группы", callback_data="broadcast_target:all"),
            InlineKeyboardButton(text="✅ Выбрать группы", callback_data="broadcast_target:custom")
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_open_tickets")]
    ])


def get_broadcast_group_selection_keyboard(chats, selected_ids) -> InlineKeyboardMarkup:
    rows = []
    selected_set = {int(x) for x in selected_ids}

    for chat in chats:
        title = chat['title'] or f"Группа {chat['chat_id']}"
        mark = "✅" if int(chat['chat_id']) in selected_set else "⬜"
        rows.append([
            InlineKeyboardButton(
                text=f"{mark} {title}",
                callback_data=f"broadcast_toggle:{chat['chat_id']}"
            )
        ])

    rows.append([
        InlineKeyboardButton(text="🚀 Отправить выбранным", callback_data="broadcast_send_selected"),
        InlineKeyboardButton(text="🌍 Все группы", callback_data="broadcast_target:all")
    ])
    rows.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_broadcast")
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)

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

def get_courses_language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇹🇯 Тоҷикӣ", callback_data="courses_lang:tj"),
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="courses_lang:ru")
        ],
        [
            InlineKeyboardButton(text="🇬🇧 English", callback_data="courses_lang:en")
        ]
    ])

def get_courses_course_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔙 Назад к выбору языка", callback_data="courses_menu")
    ]])

def get_courses_detail_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔙 Назад к списку курсов", callback_data=f"courses_list:{lang}"),
            InlineKeyboardButton(text="🌐 Выбор языка", callback_data="courses_menu")
        ]
    ])

def get_courses_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔙 Назад к выбору языка", callback_data="courses_menu")
    ]])
