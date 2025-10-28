import asyncio
import sqlite3
from io import BytesIO
from aiogram import Bot, F, Router
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from app import keyboards as kb
from app.middleware import LoggingMiddleware
# from config import TOKEN, client
import os
import pollinations
from google import genai


API_KEY = os.getenv("API_KEY")

google_api = os.getenv("client")

conn = sqlite3.connect("users.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_ID BIGINT PRIMARY KEY,
    trial BOOLEAN DEFAULT 1
)
""")

client = genai.Client(api_key=google_api)

image_gen = pollinations.Image(nologo=True, width=1920, height=1080, enhance=True)


class UserData(StatesGroup):
    age = State()
    hobby = State()
    profession = State()


class GenState(StatesGroup):
    prompt = State()


bot = Bot(token=API_KEY)  # TOKEN


router = Router()


router.message.middleware(LoggingMiddleware())


@router.message(CommandStart())
async def start_cmd(message: Message):
    await message.answer("Привет, я крутой бот. Жми кнопку снизу.", reply_markup=kb.main_func_start)
    # a = message.from_user.id
    # cursor.execute("SELECT trial FROM users WHERE user_ID = ?", (a,))
    # result = cursor.fetchone()
    # if result is None:
    #     cursor.execute("INSERT INTO users (user_ID) VALUES (?)", (a,))
    #     conn.commit()
    #     await message.answer("Пробный период — 3 дня ⏳.")
    #     await asyncio.create_task(trial_timer(message.chat.id, a))
    # elif result[0] == 1:
    #     await message.answer("⚠️ Пробный период ещё идёт.")
    # else:
    #     await message.answer("❌ Пробный период уже закончился.")
    # conn.commit()


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


@router.message(F.text.lower() == "генерация картинки")
async def image_prompt(message: Message, state: FSMContext):
    await message.answer("Опишите изображение которое вам нужно.")
    await state.set_state(GenState.prompt)


@router.message(GenState.prompt)
async def generate_image(message: Message, state: FSMContext):
    await state.clear()
    try:
        result = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-2.5-flash",
            contents=(
                "Ты — улучшатель промптов."
                "Когда я отправляю тебе любой текст (промпт), ТЫ ДОЛЖЕН:"
                "1. Улучшить его формулировку, сделать её максимально чёткой, логичной"
                " и подходящей для использования в работе с ИИ."
                "2. Перевести улучшенный вариант на английский язык."
                "3. Не добавлять никаких комментариев, пояснений или лишнего текста."
                "В ответе должен быть только улучшенный английский вариант промпта,"
                " без кавычек и без исходного текста."
                f"Вот промпт: {message.text}"
            )
        )
        prompt_en = result.text
    except Exception as e:
        print(f"Ошибка при обращении к Gemini API: {e}")
        await message.answer("⚠️ Сервис генерации перегружен. Попробуйте снова через пару секунд.")
        return
    img = await asyncio.to_thread(image_gen, prompt=prompt_en)
    img_buffer = BytesIO()
    img.save(img_buffer, format="PNG")
    img_buffer.seek(0)
    photo_file = BufferedInputFile(
        file=img_buffer.read(),
        filename="generated_image.png"
    )
    await message.answer_photo(
        photo=photo_file,
        caption="Ваше сгенерированное изображение!"
    )


@router.message(F.text.lower() == "дать совет")
async def smth(message: Message):
    await message.answer("Выберите свой пол", reply_markup=kb.sex)


@router.callback_query(F.data == "M")
async def sex_m(callback: CallbackQuery, state: FSMContext):
    await state.update_data(sex="мужчина")
    await callback.message.edit_text("Круто, теперь напиши возраст.")
    await state.set_state(UserData.age)


@router.callback_query(F.data == "W")
async def sex_w(callback: CallbackQuery, state: FSMContext):
    await state.update_data(sex="женщина")
    await callback.message.edit_text("Круто, теперь напиши возраст.")
    await state.set_state(UserData.age)


@router.message(UserData.age)
async def age(message: Message, state: FSMContext):
    try:
        await state.update_data(age=int(message.text))
    except ValueError:
        await message.answer("Ты не цифры написал. Пиши нормально еще раз.")
        await state.set_state(UserData.age)
        return
    await message.answer("Круто, теперь свое хобби.")
    await state.set_state(UserData.hobby)


@router.message(UserData.hobby)
async def hobby(message: Message, state: FSMContext):
    await state.update_data(hobby=message.text)
    await message.answer("Круто, теперь свою профессию.")
    await state.set_state(UserData.profession)


@router.message(UserData.profession)
async def final_func(message: Message, state: FSMContext):
    await state.update_data(profession=message.text)
    user_data = await state.get_data()
    await state.clear()
    sex = user_data["sex"]
    u_age = user_data["age"]
    u_hobby = user_data["hobby"]
    profession = user_data["profession"]
    response = [await asyncio.to_thread(client.models.generate_content, model="gemini-2.5-flash",
                                        contents=f"Дай совет, который можно всегда вспомнить"
                                                 f" и применить. Он обязательно должен подходить для {sex}."
                                                 f"Совет должен быть около 2-3 предложений."
                                                 f" Не форматируй текст и не используй '*'."
                                        ),
                await asyncio.to_thread(client.models.generate_content, model="gemini-2.5-flash",
                                        contents=f"Дай совет, который можно всегда вспомнить"
                                                 f" и применить. Он обязательно должен подходить для человека {u_age} лет."
                                                 f"Совет должен быть около 2-3 предложений."
                                                 f" Не форматируй текст и не используй '*'."
                                        ),
                await asyncio.to_thread(client.models.generate_content, model="gemini-2.5-flash",
                                        contents=f"Дай совет, который можно всегда вспомнить"
                                                 f" и применить. Он обязательно должен подходить для человека с хобби {u_hobby}."
                                                 f"Совет должен быть около 2-3 предложений."
                                                 f" Не форматируй текст и не используй '*'."
                                        ),
                await asyncio.to_thread(client.models.generate_content, model="gemini-2.5-flash",
                                        contents=f"Дай совет, который можно всегда вспомнить"
                                                 f" и применить. Он обязательно должен подходить для человека с профессией {profession}."
                                                 f"Совет должен быть около 2-3 предложений."
                                                 f" Не форматируй текст и не используй '*'."
                                        ),
                await asyncio.to_thread(client.models.generate_content, model="gemini-2.5-flash",
                                        contents=f"Дай смешной совет, который можно всегда вспомнить,"
                                                 f" улыбнутся и применить. Он обязательно должен подходить для {sex},"
                                                 f" {u_age} лет, с хобби {u_hobby} и по профессии {profession}."
                                                 f"Совет должен быть около 2-3 предложений."
                                                 f" Не форматируй текст и не используй '*'."
                                        )
                ]
    await message.answer(f"Ответ по вашим параметрам: \n{sex}: {response[0].text} \n{u_age} лет: {response[1].text}"
                         f" \n{u_hobby}: {response[2].text} \n{profession}: {response[3].text} "
                         f"\nИ общий совет: {response[4].text}")
    print(f"Ответ по вашим параметрам: \n{sex}: {response[0].text} \n{u_age} лет: {response[1].text}"
          f" \n{u_hobby}: {response[2].text} \n{profession}: {response[3].text}"
          f" \nИ общий совет: {response[4].text}")
