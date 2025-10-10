from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

reg = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Отправить номер", callback_data="num")]
                                            ])
contact_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📱 Отправить мой номер", request_contact=True)]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)