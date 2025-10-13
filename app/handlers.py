from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram import Router, F, Bot
import asyncio
from app.middleware import LoggingMiddleware
from config import TOKEN
import sqlite3
from gpt4all import GPT4All

conn = sqlite3.connect("users.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_ID BIGINT PRIMARY KEY,
    trial BOOLEAN DEFAULT 1
)
""")

model = GPT4All("mistral-7b-instruct-v0.1.Q4_0.gguf",
                model_path="C:/Users/archi/gpt4all/models")

bot = Bot(token=TOKEN)

router = Router()

router.message.middleware(LoggingMiddleware())


@router.message(CommandStart())
async def start_cmd(message: Message):
    await message.answer("Привет, я крутой бот.")
    a = message.from_user.id
    cursor.execute("SELECT trial FROM users WHERE user_ID = ?", (a,))
    result = cursor.fetchone()
    if result is None:
        cursor.execute("INSERT INTO users (user_ID) VALUES (?)", (a,))
        conn.commit()
        await message.answer("Пробный период — 3 дня ⏳.")
        await asyncio.create_task(trial_timer(message.chat.id, a))
    elif result[0] == 1:
        await message.answer("⚠️ Пробный период ещё идёт.")
    else:
        await message.answer("❌ Пробный период уже закончился.")
    conn.commit()


@router.message(Command("check"))
async def check_trial(message: Message):
    cursor.execute("SELECT trial FROM users WHERE user_ID = ?", (message.from_user.id,))
    result = cursor.fetchone()
    if result[0] == 1:
        await message.answer("⚠️ Пробный период ещё идёт.")
    else:
        await message.answer("❌ Пробный период уже закончился.")


async def trial_timer(chat_id, user_id):
    await asyncio.sleep(10)
    await bot.send_message(chat_id=chat_id, text="❌ Пробный период закончился.")
    cursor.execute("UPDATE users SET trial = 0 WHERE user_ID = ?", (user_id,))
    conn.commit()


@router.message(F.text)
async def smth(message: Message):
    a = message.text
    response = await asyncio.to_thread(model.generate, f"Придумай сказку о {a}. Она должна быть не больше 200 токенов. Не озвучивай свои мысли.", max_tokens=999)
    await message.answer(response)
