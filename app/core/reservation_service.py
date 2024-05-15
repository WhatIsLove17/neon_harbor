import app.database.requests as requests
from app.core.entities_service import get_places_count
from datetime import datetime, timedelta, time
from app.handlers.admin_handlers import ADMIN_CHAT_ID
from aiogram import Bot
import re

OPEN_TIME = time(19, 0)  # Время открытия
CLOSE_TIME = time(8, 0)  # Время закрытия
SLOT_DURATION = timedelta(minutes=30)  # Продолжительность слота

async def remove_booking_by_chat_id(chat_id, bot: Bot):
    user = await requests.get_user_by_chat_id(chat_id)

    removed_slots = await requests.remove_book_by_user_id(user.id)

    if removed_slots:
        for removed_slot in removed_slots:
            await bot.send_message(ADMIN_CHAT_ID, f'Удалена запись:\nСтол №{removed_slot.reservation_place_id} \
{removed_slot.reservation_start_time.time()}-{removed_slot.reservation_end_time.time()} ({removed_slot.reservation_start_time.date()})')


async def check_upcoming_reservations(bot: Bot):
    time_in_two_hours = datetime.now() + timedelta(hours=2)

    reserved_slots = await requests.get_books_for_date_and_time(time_in_two_hours)

    for start_time, end_time, table_id, name, chat_id in reserved_slots:
        await bot.send_message(chat_id, f'Привет, {name}, напоминаем о брони через 2 часа, ваш стол - {table_id}')


async def admin_remove_booking(message):
    # Используем регулярное выражение для извлечения данных
    pattern = r"Стол №\s*(\d+)\s+(\w+)\s+(\d{2}:\d{2})"
    match = re.match(pattern, message.strip())
    if match:
        table_number = int(match.group(1))
        date_info = await convert_to_dates(match.group(2))
        start_time = datetime.strptime(match.group(3), "%H:%M").time()
    else:
        raise ValueError("Недостаточно данных для создания брони. Проверьте формат сообщения.")

    return await requests.remove_book(table_number, date_info, start_time)

async def admin_get_slots_by_day(date_str):
    date = await convert_to_dates(date_str)

    reserved_slots = await requests.get_books_for_date_with_users(start_time=datetime.combine(date, OPEN_TIME), 
                                                       end_time=datetime.combine(date + timedelta(days=1), CLOSE_TIME))

    text = f'Бронь за {date_str}:'
    for table in range(1, await get_places_count() + 1):
        
        text += f'\nСтол №{table}:\n'
        for start_time, end_time, table_id, name, phone in reserved_slots:
            if (table_id == table):
                text += f'{start_time.time()} - {end_time.time()} {name} - {phone}\n'

    return text


async def admin_add_booking(bot, message):
    # Используем регулярное выражение для извлечения данных
    pattern = r"Стол №\s*(\d+)\s+(\w+)\s+(\d{2}:\d{2})-(\d{2}:\d{2})\s+(\d{11})\s+(.+)"
    match = re.match(pattern, message.strip())
    if match:
        table_number = int(match.group(1))
        date_info = match.group(2)
        start_time = match.group(3)
        end_time = match.group(4)
        phone_number = match.group(5)
        customer_name = match.group(6).strip()  # Удаляем лишние пробелы вокруг имени
    else:
        raise ValueError("Недостаточно данных для создания брони. Проверьте формат сообщения.")

    # Преобразуем строки времени в объекты времени
    succes = await requests.register_user(number=phone_number, chat_id=0, user_name=customer_name)

    if succes:
        await add_booking(bot, phone_number, table_number, date_info, start_time, end_time)
    

async def add_booking(bot: Bot, phone, table_number, date_str, start_time_str, end_time_str):
    # Конвертация входных данных в дату и время
    date = await convert_to_dates(date_str)

    start_time_w_dt = datetime.strptime(start_time_str, "%H:%M").time()
    start_time = datetime.combine(date if start_time_w_dt >= OPEN_TIME else date + timedelta(days=1), start_time_w_dt)

    end_time_w_dt = datetime.strptime(end_time_str, "%H:%M").time()
    end_time = datetime.combine(date if end_time_w_dt >= OPEN_TIME else date + timedelta(days=1), end_time_w_dt)
    print(start_time.time(), end_time.time())


    if not (start_time >= datetime.combine(date, OPEN_TIME) and end_time <= datetime.combine(date + timedelta(days=1), CLOSE_TIME)):
        raise Exception('Нельзя забронировать столик в нерабочие часы')
    
    print(datetime.combine(date, OPEN_TIME))
    print(datetime.combine(date + timedelta(days=1), CLOSE_TIME))
    # Получаем все забронированные слоты на этот день и проверяем доступность выбранного
    reserved_slots = await requests.get_books_for_date(start_time=datetime.combine(date, OPEN_TIME), 
                                                       end_time=datetime.combine(date + timedelta(days=1), CLOSE_TIME))
    
    print(type(table_number))
    for start_time_, end_time_, table_id in reserved_slots:
        print(start_time_, end_time_)
        if table_id == int(table_number):
            if (start_time_ <= start_time < end_time_) or \
               (start_time_ < end_time <= end_time_):
                raise Exception('Это время уже занято')

    user = await requests.get_user_by_phone(phone)
    await requests.add_reservation(number=table_number, start_time=start_time, end_time=end_time, user_id=user.id)

    await bot.send_message(ADMIN_CHAT_ID, f'Добавлена новая бронь:\nСтол №{table_number} {date_str} {start_time_str}-{end_time_str} {user.phone} {user.name}')

async def get_user_number(chat_id):
    user = await requests.get_user_by_chat_id(chat_id)
    if user:
        return user.phone

    return None

async def get_slots(date_str):
    date = await convert_to_dates(date_str)  # Преобразование строки в объект datetime.date
    reserved_slots = await requests.get_books_for_date(start_time=datetime.combine(date, OPEN_TIME), 
                                                       end_time=datetime.combine(date + timedelta(days=1), CLOSE_TIME))
    
    
    text = f'Бронь за {date_str}:'
    for table in range(1, await get_places_count() + 1):
        
        text += f'\nСтол №{table}:\n'
        for start_time, end_time, table_id in reserved_slots:
            if (table_id == table):
                text += f'{start_time.time()} - {end_time.time()}\n'

    return text


async def merge_time_slots(slots):
    if not slots:
        return []
    
    # Сортировка по начальному времени каждого слота
    slots.sort()
    merged_slots = [slots[0]]

    for current in slots[1:]:
        last = merged_slots[-1]
        # Если текущий слот начинается сразу после последнего, объединяем их
        if last[1] == current[0]:
            merged_slots[-1] = (last[0], current[1])
        else:
            merged_slots.append(current)
    
    return merged_slots

async def generate_week_dates():
    base_date = datetime.now()
    dates = ["Сегодня", "Завтра"]

    # Генерируем последующие даты
    for i in range(2, 7):
        next_date = base_date + timedelta(days=i)
        dates.append(next_date.strftime("%d.%m"))

    return dates

async def get_books(target_date):
    reservations = await requests.get_books_for_date(await convert_to_dates(target_date))

    return reservations

async def convert_to_dates(date_str):
    today = datetime.now().date()  # Получение текущей даты
    
    if date_str == "Сегодня":
        return today
    elif date_str == "Завтра":
        return today + timedelta(days=1)
    else:
        # Строка должна быть в формате "dd.mm"
        day, month = map(int, date_str.split('.'))
        year = today.year
        # Обрабатываем случай, когда дата относится к следующему году
        if month < today.month or (month == today.month and day < today.day):
            year += 1
        return datetime(year, month, day).date()