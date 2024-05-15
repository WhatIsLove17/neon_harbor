from aiogram import F, Router, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from app.user_states.user_states import Register, Book, Friend, Resume
import app.core.reservation_service as reserv_service
import string
import app.database.requests as requests
import random
import app.keyboards.user_keyboards as kb
from app.handlers.admin_handlers import ADMIN_CHAT_ID

from app.core.entities_service import get_welcome_post, get_menu_bar, get_menu, get_places, get_places_count
from app.core.posts import Post

user_router = Router()

@user_router.message(Command('resume'))
async def resume(message: Message, state: FSMContext):
    await state.set_state(Resume.resume)
    await message.answer("Привет, отправь нам свое резюме в формате pdf, мы рассмотрим и свяжемся")

@user_router.message(Resume.resume)
async def get_resume(message: Message, state: FSMContext):
    
    if message.document:
        file_id = message.document.file_id
        await message.bot.send_document(ADMIN_CHAT_ID, document=file_id, caption='Резюме потенциального сотрудника')
        await message.answer("Спасибо, мы скоро с вами свяжемся!")
        await state.clear()
    else:
        await message.answer("Кажется, с документом что-то не так")

@user_router.message(Command('friend'))
async def friend(message: Message, state: FSMContext):
    await state.set_state(Friend.phone)

    await message.answer("Отправь номер друга, который посоветовал тебе наш чат, мы начислим ему баллы :D")

@user_router.message(Friend.phone)
async def friend_phone(message: Message, state: FSMContext):
    res = await requests.change_scores(phone=message.text, scores=500)

    if res:
        await message.answer('Нашли друга, зачислили ему баллов)')
    else:
        await message.answer('Не удалось найти друга(')
    
    await state.clear()


@user_router.message(Command('scores'))
async def get_scores(message: Message):
    user = await requests.get_user_by_chat_id(message.chat.id)
    if user:
        await message.answer(f'У вас {user.scores} баллов, они копятся при каждой покупке в баре :D')
    else:
        await message.answer(f'Вы еще не зарегистрированы, воспользуйтесь командой /start')

@user_router.message(Command('rem_book'))
async def remove_book(message: Message):
    await reserv_service.remove_booking_by_chat_id(message.chat.id, message.bot)

    await message.answer('Ваши брони успешно удалены')

@user_router.message(Command('start'))
async def send_welcome_post(message: Message):
    welcome_post = await get_welcome_post()
    await send_post(message, welcome_post, kb.start)

@user_router.message(Command('bar_menu'))
async def send_bar_menu_post(message: Message):

    bar_menu_post = await get_menu_bar()
    await send_post(message, bar_menu_post)

@user_router.message(Command('menu'))
async def send_bar_menu_post(message: Message):

    menu_post = await get_menu()
    await send_post(message, menu_post)

@user_router.message(Command('book'))
async def book_table(message: Message, state: FSMContext):
    inline_keyboard = []

    options = await reserv_service.generate_week_dates()
    for option in options:
        button = InlineKeyboardButton(text=option, callback_data=f"{option}")
        inline_keyboard.append([button])  # Помещаем кнопку в отдельный список, так как каждая кнопка - это ряд
    keyboard = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
    await state.set_state(Book.date)
    await message.answer("Выберите день для брони:", reply_markup=keyboard)


@user_router.callback_query(Book.date)
async def choose_date(callback_query: CallbackQuery, state: FSMContext):
    await state.update_data(date=callback_query.data)

    booking = await reserv_service.get_slots(callback_query.data)
    keyboard = await kb.make_table_keyboard(await get_places_count())  # Создаем клавиатуру со списком столов

    await state.set_state(Book.number)

    # Отправляем сообщение с доступными слотами и запрашиваем выбор стола
    await send_post(callback_query.message, await get_places())
    await callback_query.answer('Держи бронь')
    await callback_query.message.answer(text=booking)
    await callback_query.message.answer("Какой столик выберем?", reply_markup=keyboard)

@user_router.callback_query(Book.number)
async def choose_table(callback_query: CallbackQuery, state: FSMContext):
    await state.update_data(number=callback_query.data)
    await callback_query.answer('Столик выбран')

    await state.set_state(Book.time_interval)

    # Отправляем сообщение с доступными слотами и запрашиваем выбор стола
    await callback_query.message.answer("Какой интервал бронируем? Бар работает с 19:00 до 05:00 (Например: 20:00 - 01:30)")

@user_router.message(Book.time_interval)
async def choose_interval(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(time_interval=message.text)

    user_phone = await reserv_service.get_user_number(message.chat.id)

    if not user_phone and not message.contact:
        await state.set_state(Book.phone)
        await message.answer('Для брони нужен ваш номер телефона', reply_markup=kb.get_number)
    else:
        await choose_interval_with_phone(message, state, bot, user_phone)

@user_router.message(Book.phone)
async def choose_interval_with_phone(message: Message, state: FSMContext, bot: Bot, phone = None):
    data = await state.get_data()

    time_inter = data['time_interval']
    start_time_str, end_time_str = time_inter.replace(' ', '').split('-')
    date = data['date']
    phone_number = phone if phone else message.contact.phone_number
    table_number = data['number']


    if not phone:
        success = await requests.register_user(number=phone_number, chat_id=message.chat.id, user_name=message.from_user.first_name)

        if not success and not phone:
            message.answer('Пользователь с таким номером уже существует, воспользуйтесь командой /start')
            raise Exception('Пользователь с таким номером уже существует')

    await state.clear()

    await reserv_service.add_booking(bot=bot, phone=phone_number, table_number=table_number, date_str=date, start_time_str=start_time_str,
                                        end_time_str=end_time_str)
    
    await message.answer(f"Столик №{table_number} успешно забронирован на {start_time_str} - {end_time_str}  ({date})")


@user_router.callback_query(F.data == 'yes')
async def welcome_button(callback: CallbackQuery, state: FSMContext):
    if callback.data == 'yes':
        await callback.answer('Супер!')
        await callback.message.answer('Супер, отправь, пожалуйста, свой номер телефона по кнопке',
                                      reply_markup=kb.get_number)
        await state.set_state(Register.number)

@user_router.message(Register.number, F.contact)
async def get_number(message: Message, state: FSMContext):
    number = message.contact.phone_number
    name = 'NEON_' + ''.join(random.choices(string.ascii_uppercase +
                        string.digits, k=6))
    
    success = await requests.register_user(number=number, chat_id=message.chat.id, user_name=message.from_user.first_name, name=name, description='Коктейль')
    if success:
        await message.answer('Все четко! Вот твой промокод, дай его бармену, чтобы получить напиток')
        await message.answer(name)
    else:
        await message.answer('Кажется, пользователь с таким номером уже существует(')
    
    await state.clear()

async def send_post(message: Message, post: Post, kb=None):
    if post.photo:
        if post.text:
            await message.answer_photo(photo=post.photo, caption=post.text, reply_markup=kb)
        else:
            await message.answer_photo(photo=post.photo, reply_markup=kb)
    elif post.video:
        if post.text:
            await message.answer_video(video=post.video, caption=post.text, reply_markup=kb)
        else:
            await message.answer_video(video=post.video, reply_markup=kb)
    elif post.doc:
        if post.text:
            await message.answer_document(document=post.doc, caption=post.text, reply_markup=kb)
        else:
            await message.answer_document(document=post.doc, reply_markup=kb)
    else:
        await message.answer(post.text, reply_markup=kb)