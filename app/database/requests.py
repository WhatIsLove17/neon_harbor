import random
import string
from datetime import timedelta
from app.database.models import User, Promocode, Reservation
from app.database.models import async_session
from sqlalchemy import select, and_
    
async def register_user(number, chat_id, user_name, name = None, description=None):

    async with async_session() as session:
        user = await session.scalar(select(User).where(User.phone == number))

        if not user:
            login = ''.join(random.choices(string.ascii_lowercase + string.digits, k=32))
            if name:
                session.add(Promocode(name=name, description=description, used_flg = False))

            session.add(User(chat_id=chat_id, login = login, name = user_name, phone = number, scores = 0))
        elif user.chat_id != chat_id:
            user.chat_id = chat_id
        else:
            return False
        
        await session.commit()
        return True
    
async def change_scores(phone, scores):

    async with async_session() as session:
        user = await session.scalar(select(User).where(User.phone == phone))

        if user:
            user.scores += scores
        else:
            return None
        
        await session.commit()
        return True

async def add_promo(names, description):

    async with async_session() as session:
        
        for name in names:
            session.add(Promocode(name=name, description=description, used_flg = False))
        await session.commit()

async def use_promo(name):

    async with async_session() as session:
        
        promo = await session.scalar(select(Promocode).where(Promocode.name == name))
        
        if not promo:
            return None

        promo.used_flg = True
        desc = promo.description

        await session.commit()
        return desc
        
async def add_reservation(user_id, number, start_time, end_time):
    async with async_session() as session:
        # Создаем экземпляр бронирования
        reservation = Reservation(
            reservation_start_time=start_time,
            reservation_end_time=end_time,
            reservation_user_id=user_id,
            reservation_place_id=number
        )
        
        # Добавляем запись о бронировании в БД и коммитим транзакцию
        session.add(reservation)
        await session.commit()


async def get_all_users():
    async with async_session() as session:
        return await session.scalars(select(User))

async def get_user_by_chat_id(chat_id):
    async with async_session() as session:
        return await session.scalar(select(User).where(User.chat_id == chat_id))
    
async def get_user_by_phone(phone):
    async with async_session() as session:
        return await session.scalar(select(User).where(User.phone == phone))

async def get_books_for_date(start_time, end_time):
    async with async_session() as session:
        result = await session.execute(
            select(Reservation)
            .where(
                and_(
                    Reservation.reservation_start_time >= start_time,
                    Reservation.reservation_end_time <= end_time
                )
            )
        )
        return [(res.reservation_start_time, res.reservation_end_time, res.reservation_place_id) for res in result.scalars()]

async def get_books_for_date_and_time(start_time):
    async with async_session() as session:
        results = await session.execute(
            select(Reservation, User)
            .join(User, User.id == Reservation.reservation_user_id)
            .where(
                Reservation.reservation_start_time >= start_time - timedelta(minutes=15),
                Reservation.reservation_start_time >= start_time + timedelta(minutes=15)
            )
        )
        # Обрабатываем результаты запроса; results.all() возвращает список кортежей
        bookings = [
            (
                res[0].reservation_start_time, 
                res[0].reservation_end_time, 
                res[0].reservation_place_id,
                res[1].name, 
                res[1].chat_id
            ) for res in results.all()
        ]
        # Возвращаем обработанный список
        return bookings


async def get_books_for_date_with_users(start_time, end_time):
    async with async_session() as session:
        # Используем select для выбора объектов обоих классов
        results = await session.execute(
            select(Reservation, User)  # Выбираем обе модели 
            .join(User, User.id == Reservation.reservation_user_id)  # Делаем JOIN по id пользователя
            .where(
                and_(
                    Reservation.reservation_start_time >= start_time,
                    Reservation.reservation_end_time <= end_time
                )
            )
        )

        # Обрабатываем результаты запроса; results.all() возвращает список кортежей
        bookings = [(res[0].reservation_start_time, res[0].reservation_end_time, res[0].reservation_place_id, res[1].name, res[1].phone)
                    for res in results.all()]
        # Возвращаем обработанный список
        return bookings

async def remove_book(table_number, start_time):
    async with async_session() as session:
        # Найдем объект бронирования, который соответствует предоставленным критериям
        query = select(Reservation).where(
            and_(
                Reservation.reservation_place_id == table_number,
                Reservation.reservation_start_time == start_time
            )
        )
        result = await session.execute(query)
        reservation = result.scalars().first()
        
        if reservation is not None:
            # Удаляем найденную запись
            await session.delete(reservation)
            await session.commit()
            return True  # Успешное удаление
        else:
            return False  # Запись не найдена

        
async def remove_book_by_user_id(user_id):
    async with async_session() as session:
        query = select(Reservation).where(Reservation.reservation_user_id == user_id)
        result = await session.execute(query)
        reservations = result.scalars().all()
        
        if reservations:
            # Удаляем найденные записи
            for reservation in reservations:
                await session.delete(reservation)
            await session.commit()
            return reservations  # Возвращаем список удаленных бронирований
        else:
            return None  # Запись не найдена
