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
    btn_manage_courses = InlineKeyboardButton(
        text="🎓 Управление курсами",
        callback_data="admin_manage_courses"
    )
    return InlineKeyboardMarkup(inline_keyboard=[[btn_view], [btn_broadcast], [btn_manage_courses]])


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
    course_labels = {
        "tj": {
            "ai": "1️⃣ AI Fundamentals",
            "programming": "2️⃣ Программирование с 0",
            "python": "3️⃣ Python",
            "frontend": "4️⃣ Frontend",
            "golang": "5️⃣ Golang",
            "csharp": "6️⃣ C#",
            "mobile": "7️⃣ Mobile",
            "design": "8️⃣ Design & UX/UI",
            "office": "9️⃣ Компьютерная грамотность"
        },
        "ru": {
            "ai": "1️⃣ Основы AI",
            "programming": "2️⃣ Программирование с 0",
            "python": "3️⃣ Python",
            "frontend": "4️⃣ Frontend",
            "golang": "5️⃣ Golang",
            "csharp": "6️⃣ C#",
            "mobile": "7️⃣ Mobile",
            "design": "8️⃣ Design & UX/UI",
            "office": "9️⃣ Компьютерная грамотность"
        },
        "en": {
            "ai": "1️⃣ AI Fundamentals",
            "programming": "2️⃣ Programming from Scratch",
            "python": "3️⃣ Python",
            "frontend": "4️⃣ Frontend",
            "golang": "5️⃣ Golang",
            "csharp": "6️⃣ C#",
            "mobile": "7️⃣ Mobile",
            "design": "8️⃣ Design & UX/UI",
            "office": "9️⃣ Computer Basics"
        }
    }

    rows = []
    current_row = []
    for course_id, label in course_labels.get(lang, {}).items():
        current_row.append(
            InlineKeyboardButton(
                text=label,
                callback_data=f"courses_course:{lang}:{course_id}"
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