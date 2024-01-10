import asyncio
import logging

from aiogram import Bot, Dispatcher, types
import os

from aiogram.filters import CommandStart, Command
from dotenv import load_dotenv

from services import find_pair, save_user_to_db, get_users_pair_from_db, delete_user_from_db, setup_database

load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def handle_start(message: types.Message):
    """
    Обработчик команды /start.
    Отправляет приветственное сообщение и инструкции по использованию бота.

    :param message: Объект сообщения от пользователя.
    """

    await message.answer(
        text=f'Привет, {message.from_user.first_name}!'
             f'\nЭто анонимный чат бот, '
             f'где ты можешь найти себе случайного собеседника!'
             f'\nОтправь в чат /find для поиска собеседника',
    )


@dp.message(Command('help'))
async def handle_help(message: types.Message):
    """
    Обработчик команды /help.
    Отправляет пользователю справочную информацию о боте.

    :param message: Объект сообщения от пользователя.
    """

    await message.answer(text='Отправь в чат /find для поиска собеседника')


@dp.message(Command('find'))
async def find_handler(message: types.Message):
    """
    Обработчик команды /find.
    Инициирует поиск собеседника для пользователя.

    :param message: Объект сообщения от пользователя.
    """

    user_id = message.from_user.id
    if get_users_pair_from_db(user_id):
        await bot.send_message(user_id, 'Вы уже находитель в беседе'
                                        '\nОтправьте в чат /next для поиска другого собеседника')
    else:
        pair_id = find_pair(user_id)

        if pair_id:
            save_user_to_db(user_id, pair_id)
            save_user_to_db(pair_id, user_id)

            await bot.send_message(user_id, 'Ваш собеседник найден!'
                                            '\nМожете отправить ему сообщение'
                                            '\n/next - искать нового собеседника'
                                            '\n/stop - завершить диалог')
            await bot.send_message(pair_id, 'Ваш собеседник найден!'
                                            '\nМожете отправить ему сообщение'
                                            '\n/next - искать нового собеседника'
                                            '\n/stop - завершить диалог')
        else:
            save_user_to_db(user_id, None)
            await bot.send_message(user_id, 'Ищу собеседника...')


@dp.message(Command('next'))
async def next_handler(message: types.Message):
    """
    Обработчик команды /next.
    Прерывает текущий диалог и ищет следующего собеседника.

    :param message: Объект сообщения от пользователя.
    """

    user_id = message.from_user.id
    pair_id = get_users_pair_from_db(user_id)

    if pair_id:
        save_user_to_db(user_id, None)
        save_user_to_db(pair_id, None)

        await bot.send_message(user_id, 'Диалог прерван'
                                        '\nИщу следующего собеседника...'
                               )
        await bot.send_message(pair_id, 'Собеседник вышел из беседы'
                                        '\nИщу следующего собеседника...'
                               )

        pair_id = find_pair(user_id)
        save_user_to_db(user_id, pair_id)
        save_user_to_db(pair_id, user_id)

        await bot.send_message(user_id, 'Ваш собеседник найден!'
                                        '\nМожете отправить ему сообщение'
                                        '\n/next - искать нового собеседника'
                                        '\n/stop - завершить диалог')
        await bot.send_message(pair_id, 'Ваш собеседник найден!'
                                        '\nМожете отправить ему сообщение'
                                        '\n/next - искать нового собеседника'
                                        '\n/stop - завершить диалог')

    else:
        await bot.send_message(user_id, 'Отправь в чат /find для поиска собеседника')


@dp.message(Command('stop'))
async def stop_handler(message: types.Message):
    """
    Обработчик команды /stop.
    Завершает поиск собеседника или текущий диалог.

    :param message: Объект сообщения от пользователя.
    """
    user_id = message.from_user.id
    pair_id = get_users_pair_from_db(user_id)

    delete_user_from_db(user_id)

    if pair_id:
        save_user_to_db(pair_id, None)
        await bot.send_message(pair_id, 'Ваш собеседник вышел из беседы')
        response_text = 'Диалог завершен'
    else:
        response_text = 'Поиск завершен'

    await message.answer(response_text)


@dp.message()
async def forward_message(message: types.Message):
    """
    Пересылает сообщения от пользователя его текущему собеседнику.
    Если собеседник не найден, отправляет уведомление пользователю.

    :param message: Объект сообщения от пользователя.
    """

    user_id = message.from_user.id
    pair_id = get_users_pair_from_db(user_id)

    if pair_id:
        await message.send_copy(pair_id)
    else:
        await bot.send_message(user_id, 'К сожалению, собеседник еще не был найден')


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    setup_database()
    asyncio.run(main())
