from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

sex = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Мужской", callback_data="M"),
                                             InlineKeyboardButton(text="Женский", callback_data="W")]
                                            ])

main_func_start = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Дать совет"), KeyboardButton(text="Генерация картинки")]
    ],
    resize_keyboard=True
)
