from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram import Router, F, Bot
import asyncio
import datetime
from app.middleware import LoggingMiddleware
from app import keyboards as kb
from config import TOKEN
import sqlite3


conn = sqlite3.connect("users.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_num TEXT,
    trial BOOlEAN DEFAULT 1
)
""")


bot = Bot(token=TOKEN)

router = Router()

router.message.middleware(LoggingMiddleware())


@router.message(CommandStart())
async def start_cmd(message: Message):
    await message.answer("Привет, зарегестрируйтеесь пожалуйста.", reply_markup=kb.reg)


@router.message(Command("check"))
async def check_trial(message: Message):
    await is_trial_over()
    await message.answer("")


@router.callback_query(F.data == "num")
async def ask_contact(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "Пожалуйста, поделись своим номером телефона:", reply_markup=kb.contact_keyboard
    )


async def trial_timer(chat_id, user_number):
    await asyncio.sleep(3)
    await bot.send_message(chat_id=chat_id, text="Пробный период капут")
    cursor.execute("UPDATE users SET trial = 0 WHERE user_num = ?", (user_number,))
    conn.commit()


async def is_trial_over(user_number):
    cursor.execute("SELECT trial FROM users WHERE user_num = ?", (user_number,))
    result = cursor.fetchone()
    if result:
        return True
    return False


@router.message(F.contact)
async def get_num(message: Message):
    a = message.contact.phone_number
    cursor.execute("INSERT OR IGNORE INTO users (user_num) VALUES (?)", (a,))
    conn.commit()
    await trial_timer(message.chat.id, a)
