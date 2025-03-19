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

    for i, option in enumerate(answer_options):
        builder.add(
            types.InlineKeyboardButton(text=option, callback_data=f"answer_{i}")
        )

    builder.adjust(1)
    return builder.as_markup()


async def clear_kb_markup(callback: types.CallbackQuery):
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None,
    )


async def show_user_answer(callback: types.CallbackQuery, answer: str):
    message_text = callback.message.text + f"\nВаш ответ: {answer}"
    await callback.bot.edit_message_text(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        text=message_text,
    )


async def next_question(
    current_question_index: int, message: types.Message, user_id: int
):
    current_question_index += 1
    await db.update_quiz_index(user_id, current_question_index)

    if current_question_index < len(quiz_data):
        await get_question(message, user_id)
    else:
        await end_quiz(user_id, message)


async def end_quiz(user_id: int, message: types.Message):
    score = await db.get_score(user_id)
    await db.save_result(user_id, score)
    await message.answer(f"Квиз завершен! Ваш результат: {score}/{len(quiz_data)}")


@dp.callback_query(F.data.startswith("answer_"))
async def handle_answer(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    message = callback.message

    user_answer = int(callback.data[-1])

    current_question_index = await db.get_quiz_index(user_id)
    current_question = quiz_data[current_question_index]
    correct_option = current_question["correct_option"]

    user_answer_text = current_question["options"][user_answer]
    correct_option_text = current_question["options"][correct_option]

    await clear_kb_markup(callback)
    await show_user_answer(callback, user_answer_text)

    if user_answer == correct_option:
        await db.increment_score(user_id)
        await message.answer("Верно!")
    else:
        await message.answer(f"Неправильно. Правильный ответ: {correct_option_text}")

    await next_question(current_question_index, message, user_id)


async def get_question(message: types.Message, user_id: int):
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
    await db.reset_score(user_id)
    await db.update_quiz_index(user_id, 0)
    await get_question(message, user_id)


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = ReplyKeyboardBuilder()

    builder.add(types.KeyboardButton(text="Начать игру"))
    builder.add(types.KeyboardButton(text="Статистика игроков"))

    kb = builder.as_markup(resize_keyboard=True)

    await message.answer("Добро пожаловать в квиз!", reply_markup=kb)


@dp.message(F.text == "Начать игру")
@dp.message(Command("quiz"))
async def cmd_quiz(message: types.Message):
    await message.answer("Давайте начнем квиз!")
    await new_quiz(message)


@dp.message(F.text == "Статистика игроков")
@dp.message(Command("statistics"))
async def cmd_stats(message: types.Message):
    stats = await db.get_all_results()

    if not stats:
        await message.answer("Пока нет данных о прохождении квиза.")
        return

    stats_message = "Статистика игроков:\n"

    user_number = 1
    for user_id, result in stats:
        user = await bot.get_chat(user_id)
        username = user.username
        if len(username.strip()) == 0:
            username = "Неизвестный"

        stats_message += f"{user_number}. {username}: {result}/{len(quiz_data)}\n"

        user_number += 1

    await message.answer(stats_message)


@dp.message()
async def unknown_message(message: types.Message):
    await message.answer("Я тебя не понимаю. Воспользуйся командами или кнопками в сообщении!")


async def main():
    await db.create_table()
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Ignore Ctrl+C exception to keep terminal clear
        logging.warning("Program stopped by Ctrl + C")
