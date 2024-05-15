from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

get_number = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Отправить номер', request_contact=True)]],
                                 resize_keyboard=True, one_time_keyboard=True)

start = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Да!', callback_data = 'yes')]])

async def make_table_keyboard(tables):
    # Создаем список кнопок
    buttons = [
        InlineKeyboardButton(text=f"Стол {table}", callback_data=f"{table}") 
        for table in range(1, tables + 1)
    ]

    # Группируем кнопки в строки по три кнопки в каждой (или любом другом количестве по вашему выбору)
    keyboard_layout = [buttons[i:i + 3] for i in range(0, len(buttons), 3)]

    # Создаем клавиатуру с этими строками кнопок
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_layout)
    return keyboard

