import json
import tomllib
import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram import F

from quiz_database import QuizDatabase

logging.basicConfig(level=logging.INFO)

CONFIG_NAME = "config.toml"

with open(CONFIG_NAME, "rb") as f:
    config = tomllib.load(f)

DB_NAME = config["DB"]["NAME"]
API_TOKEN = config["BOT"]["API_TOKEN"]

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
db = QuizDatabase(DB_NAME)

with open("quiz_data.json", "r", encoding="utf-8") as f:
    quiz_data = json.load(f)


def generate_options_keyboard(answer_options: list, right_answer):
    builder = InlineKeyboardBuilder()

    for option in answer_options:
        builder.add(
            types.InlineKeyboardButton(
                text=option,
                callback_data="right_answer"
                if option == right_answer
                else "wrong_answer",
            )
        )

    builder.adjust(1)
    return builder.as_markup()


@dp.callback_query(F.data == "right_answer")
async def right_answer(callback: types.CallbackQuery):
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None,
    )

    await callback.message.answer("Верно!")
    current_question_index = await db.get_quiz_index(callback.from_user.id)
    current_question_index += 1
    await db.update_quiz_index(callback.from_user.id, current_question_index)

    if current_question_index < len(quiz_data):
        await get_question(callback.message, callback.from_user.id)
    else:
        await callback.message.answer("Это был последний вопрос. Квиз завершен!")


@dp.callback_query(F.data == "wrong_answer")
async def wrong_answer(callback: types.CallbackQuery):
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None,
    )

    current_question_index = await db.get_quiz_index(callback.from_user.id)
    correct_option = quiz_data[current_question_index]["correct_option"]

    await callback.message.answer(
        f"Неправильно. Правильный ответ: {quiz_data[current_question_index]['options'][correct_option]}"
    )

    current_question_index += 1
    await db.update_quiz_index(callback.from_user.id, current_question_index)

    if current_question_index < len(quiz_data):
        await get_question(callback.message, callback.from_user.id)
    else:
        await callback.message.answer("Это был последний вопрос. Квиз завершен!")


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="Начать игру"))
    await message.answer(
        "Добро пожаловать в квиз!", reply_markup=builder.as_markup(resize_keyboard=True)
    )


async def get_question(message: types.Message, user_id: str):
    current_question_index = await db.get_quiz_index(user_id)
    correct_index = quiz_data[current_question_index]["correct_option"]
    opts = quiz_data[current_question_index]["options"]
    kb = generate_options_keyboard(opts, opts[correct_index])
    await message.answer(
        f"{current_question_index + 1}. {quiz_data[current_question_index]['question']}",
        reply_markup=kb,
    )


async def new_quiz(message: types.Message):
    user_id = message.from_user.id
    await db.update_quiz_index(user_id, 0)
    await get_question(message, user_id)


@dp.message(F.text == "Начать игру")
@dp.message(Command("quiz"))
async def cmd_quiz(message: types.Message):
    await message.answer("Давайте начнем квиз!")
    await new_quiz(message)


async def main():
    await db.create_table(DB_NAME)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
