import os
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv


# Загрузка переменных окружения из файла .env
load_dotenv()

# Получение значения токена из переменной окружения
token = os.getenv("TOKEN")

bot = Bot(token=token)

logging.basicConfig(level=logging.DEBUG)

bot = Bot(token=token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

engine = create_engine('sqlite:///messages.db')
Session = sessionmaker(bind=engine)
Base = declarative_base()


class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    username = Column(String(255))
    text = Column(Text)
    timestamp = Column(DateTime, default=datetime.now)


Base.metadata.create_all(engine)

# ID пользователей, которым разрешено использовать кнопку "Удалить данные из БД"
allowed_user_ids = [313631318]


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    btn1 = types.KeyboardButton("👋 Поздороваться")
    btn2 = types.KeyboardButton("❓ Задать вопрос")
    markup.add(btn1, btn2)
    await message.answer(text="Привет, {0.first_name}! Я тестовый бот базы данных с кнопками".format(message.from_user),
                         reply_markup=markup)


@dp.message_handler(content_types=['text'])
async def func(message: types.Message, state: FSMContext):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)

    if not message.is_command():
        session = Session()
        new_message = Message(user_id=message.from_user.id, username=message.from_user.username,
                              text=message.text)
        session.add(new_message)
        session.commit()

    if message.text == "👋 Поздороваться":
        await message.answer(text="Привет.. Спасибо что заглянул!=*")
    elif message.text == "❓ Задать вопрос":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        btn1 = types.KeyboardButton("Как меня зовут?")
        btn2 = types.KeyboardButton("А что я могу?")
        back = types.KeyboardButton("🏠 Вернуться в главное меню")
        markup.add(btn1, btn2, back)

        await message.answer(text="Задай мне вопрос", reply_markup=markup)
    elif message.text == "Как меня зовут?":
        await message.answer(
            text="Ну что же ты, твое имя {0.first_name}!".format(message.from_user),
            reply_markup=markup)
    elif message.text == "А что я могу?":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        btn3 = types.KeyboardButton("📚 Посмотреть последние 5 записей")
        back = types.KeyboardButton("🏠 Вернуться в главное меню")

        # Проверяем, разрешен ли пользователь использовать кнопку "Удалить данные из БД"
        if message.from_user.id in allowed_user_ids:
            btn4 = types.KeyboardButton("🗑 Удалить данные из БД")
            markup.add(btn3, btn4, back)
        else:
            markup.add(btn3, back)

        await message.answer(text="Выберите действие", reply_markup=markup)
    elif message.text == "🏠 Вернуться в главное меню":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        button1 = types.KeyboardButton("👋 Поздороваться")
        button2 = types.KeyboardButton("❓ Задать вопрос")
        markup.add(button1, button2)
        await message.answer(text="Вы вернулись в главное меню", reply_markup=markup)
    elif message.text == "📚 Посмотреть последние 5 записей":
        session = Session()
        last_messages = session.query(Message).order_by(Message.id.desc()).limit(5).all()
        response = "Последние 5 записей:\n\n"
        for msg in last_messages:
            response += f"{msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')}, {msg.username},: {msg.text}\n"
        await message.answer(response)
    elif message.text == "🗑 Удалить данные из БД":
        # Проверяем, разрешен ли пользователь использовать кнопку "Удалить данные из БД"
        if message.from_user.id in allowed_user_ids:
            session = Session()
            session.query(Message).delete()
            session.commit()
            await message.answer("Данные успешно удалены из БД!")
        else:
            await message.answer("У вас нет разрешения на выполнение этой операции.")
    else:
        await message.answer(text="Ладно.")


if __name__ == '__main__':
    from aiogram import executor

    executor.start_polling(dp, skip_updates=True)
