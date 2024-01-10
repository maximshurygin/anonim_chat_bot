import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Параметры подключения к базе данных
connection = psycopg2.connect(
    host=os.getenv('DB_HOST'),
    database=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD')
)


def setup_database():
    """
    Создает таблицу в базе данных, если она еще не существует.

    Эта функция создает таблицу `users` с двумя столбцами: `user_id` и `pair_id`.
    `user_id` является первичным ключом и хранит идентификатор пользователя Telegram.
    `pair_id` хранит идентификатор собеседника пользователя в чате.

    Если таблица уже существует, функция не производит никаких изменений в базе данных.
    """

    with connection.cursor() as cursor:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
        user_id BIGINT PRIMARY KEY,
        pair_id BIGINT
        );
        """)
        connection.commit()


def find_pair(except_user_id):
    """
    Находит случайного пользователя, который не является текущим пользователем и у которого нет пары.

    :param except_user_id: ID пользователя, исключаемого из поиска.
    :return: ID найденного пользователя или None, если такой пользователь не найден.
    """

    with connection.cursor() as cursor:
        query = """
        SELECT user_id FROM users
        WHERE user_id != %s AND pair_id IS NULL
        ORDER BY RANDOM()
        LIMIT 1
        """
        cursor.execute(query, (except_user_id,))

        result = cursor.fetchone()
    return result[0] if result else None


def save_user_to_db(id_1, id_2):
    """
     Сохраняет или обновляет пару пользователей в базе данных.

     :param id_1: ID первого пользователя.
     :param id_2: ID второго пользователя, который является парой для первого.
     """

    with connection.cursor() as cursor:
        query = """
        INSERT INTO users (user_id, pair_id) VALUES (%s, %s)
        ON CONFLICT (user_id) DO UPDATE
        SET pair_id = EXCLUDED.pair_id
        """
        cursor.execute(query, (id_1, id_2))
    connection.commit()


def get_users_pair_from_db(user_id):
    """
    Получает ID пары для заданного пользователя.

    :param user_id: ID пользователя, для которого необходимо найти пару.
    :return: ID пары пользователя или None, если пара отсутствует.
    """

    with connection.cursor() as cursor:
        query = """
        SELECT pair_id FROM users WHERE user_id = %s
        """
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        return result[0] if result else None


def delete_user_from_db(user_id):
    """
    Удаляет пользователя из базы данных.

    :param user_id: ID пользователя, который нужно удалить.
    """

    with connection.cursor() as cursor:
        query = """
        DELETE FROM users WHERE user_id = %s
        """
        cursor.execute(query, (user_id,))
    connection.commit()
