from aiogram import F, Router
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from app.user_states.admin_states import Notify, Post, BarMenu, Menu, Places, Book, Reservs, RemoveBook, AddPromo, UsePromo, ChangeScores
from aiogram import Bot
import app.core.entities_service as entities_service
import app.core.promo_service as promo_service
import app.core.reservation_service as reserv_service
import app.database.requests as requests

admin_router = Router()
ADMIN_CHAT_ID = -4111710014

HELP = """
/change_scores - изменить количество баллов у гостя
/use_promo - использовать промокод
/add_promo - добавить промокоды
/remove_book - удалить бронь столика
/get_reservs - посмотреть бронь столов
/add_book - добавить бронь столика
/notify - рассылка зарегистрированным пользователям
/welcome_post - изменить welcome пост
/change_bar_menu - изменить bar-menu пост
/change_menu - изменить menu пост
/change_places - изменить пост со столиками
"""

@admin_router.message(Command('help'))
async def change_scores(message: Message):
    if message.chat.id == ADMIN_CHAT_ID:
        await message.answer(HELP)

@admin_router.message(Command('change_scores'))
async def change_scores(message: Message, state: FSMContext):
    if message.chat.id == ADMIN_CHAT_ID:
        await message.answer('Чтобы изменить баллы клиента, введите его номер и изменение баллов')
        await message.answer('Пример:\n79504021069 +100\n79504021069 -1200')
        await state.set_state(ChangeScores.info)

@admin_router.message(ChangeScores.info)
async def save_scores_info(message: Message, state: FSMContext):
    if message.chat.id == ADMIN_CHAT_ID:
        phone, scores = message.text.split(' ')

        res = await requests.change_scores(phone=phone, scores=int(scores))
        if res:
            await message.answer('Баллы успешно изменены')
        else:
            await message.answer('Не удалось изменить баллы')

@admin_router.message(Command('use_promo'))
async def use_promo(message: Message, state: FSMContext):
    if message.chat.id == ADMIN_CHAT_ID:
        await message.answer('Чтобы использовать промокод, введите его название ответом на это сообщение')
        await message.answer('Пример:\nNEON_126517')
        await state.set_state(UsePromo.name)

@admin_router.message(UsePromo.name)
async def use_promo_name(message: Message, state: FSMContext):
    if message.chat.id == ADMIN_CHAT_ID:

        res = await promo_service.use_promo(message.text)
        if res:
            await message.answer('Промокод успешно использован:')
            await message.answer(f'Подарок: {res}')
        else:
            await message.answer('Промокод уже был использован')

        await state.clear()

@admin_router.message(Command('add_promo'))
async def add_promo(message: Message, state: FSMContext):
    if message.chat.id == ADMIN_CHAT_ID:
        await message.answer('Для регистрации промокодов в ответ на сообщение пришлите их названия')
        await message.answer('Пример:\nNEON_126517\nNEON126518\nWELCOME_COCKTAIL_1')
        await state.set_state(AddPromo.name)

@admin_router.message(AddPromo.name)
async def save_promo_name(message: Message, state: FSMContext):
    if message.chat.id == ADMIN_CHAT_ID:
        await message.answer('Теперь нужно описания подарка (Ответом на это сообщение)')
        await state.update_data(name = message.text)
        await state.set_state(AddPromo.desc)

@admin_router.message(AddPromo.desc)
async def save_promo_desc(message: Message, state: FSMContext):
    if message.chat.id == ADMIN_CHAT_ID:
        data = await state.get_data()

        await promo_service.add_promo(data['name'], message.text)
        await state.clear()
        await message.answer('Промокоды успешно добавлены')

@admin_router.message(Command('remove_book'))
async def remove_book(message: Message, state: FSMContext):
    if message.chat.id == ADMIN_CHAT_ID:
        await message.answer('Для удаления брони ответьте на это сообщение данными (Пример):\n\
Стол №2 Завтра 14:00')
        await state.set_state(RemoveBook.book_info)

@admin_router.message(RemoveBook.book_info)
async def save_remove_book(message: Message, state: FSMContext):
    if message.chat.id == ADMIN_CHAT_ID:
        if await reserv_service.admin_remove_booking(message.text):
            await message.answer('Запись успешно удалена')
        else:
            await message.answer('Произошла ошибка')
        
        await state.clear()

@admin_router.message(Command('get_reservs'))
async def add_book(message: Message, state: FSMContext):
    if message.chat.id == ADMIN_CHAT_ID:
        inline_keyboard = []

        options = await reserv_service.generate_week_dates()

        for option in options:
            button = InlineKeyboardButton(text=option, callback_data=f"{option}")
            inline_keyboard.append([button])  # Помещаем кнопку в отдельный список, так как каждая кнопка - это ряд
        keyboard = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
        await state.set_state(Reservs.date)
        await message.answer("За какой день хотите вывести бронь:", reply_markup=keyboard)

@admin_router.callback_query(Reservs.date)
async def choose_date(callback_query: CallbackQuery, state: FSMContext):
    await state.update_data(date=callback_query.data)
    await callback_query.answer('Держи бронь')

    booking = await reserv_service.admin_get_slots_by_day(callback_query.data)

    await state.clear()

    await callback_query.message.bot.send_message(ADMIN_CHAT_ID, booking)

@admin_router.message(Command('add_book'))
async def add_book(message: Message, state: FSMContext):
    if message.chat.id == ADMIN_CHAT_ID:
        await message.answer('Для добавления брони ответьте на это сообщение данными (Пример):\n\
Стол №2 Завтра 10:00-14:00 79504920078 Владислав')
        await state.set_state(Book.book_info)

@admin_router.message(Book.book_info)
async def save_book(message: Message, state: FSMContext):
    if message.chat.id == ADMIN_CHAT_ID:
        await reserv_service.admin_add_booking(message.bot, message.text)
        await state.clear()

@admin_router.message(Command('notify'))
async def notify(message: Message, state: FSMContext):
    if message.chat.id == ADMIN_CHAT_ID:
        await message.answer('Какой пост отправим пользователям? (отправь пост ответом на это сообщение)')
        await state.set_state(Notify.post)

@admin_router.message(Notify.post)
async def send_notify(message: Message, bot: Bot, state: FSMContext):
    if message.chat.id == ADMIN_CHAT_ID:
        await state.clear()
        await entities_service.send_post_all_users(message, bot)
        await message.answer('Супер!')

@admin_router.message(Command('welcome_post'))
async def change_welcome_photo(message: Message, state: FSMContext):
    if message.chat.id == ADMIN_CHAT_ID:
        await message.answer('Какой у нас будет welcome-пост? (отправь пост ответом на это сообщение)')
        await state.set_state(Post.welcome_post)

@admin_router.message(Post.welcome_post)
async def welcome_post(message: Message, state: FSMContext):
    if message.chat.id == ADMIN_CHAT_ID:
        await state.clear()
        await entities_service.change_welcome_post(message)
        await message.answer('Супер!')

@admin_router.message(Command('change_bar_menu'))
async def change_bar_menu(message: Message, state: FSMContext):
    if message.chat.id == ADMIN_CHAT_ID:
        await message.answer('Какое меню бара будем использовать? (отправь пост ответом на это сообщение)')
        await state.set_state(BarMenu.bar_menu)

@admin_router.message(BarMenu.bar_menu)
async def bar_menu(message: Message, state: FSMContext):
    if message.chat.id == ADMIN_CHAT_ID:
        await state.clear()
        await entities_service.change_bar_menu(message)
        await message.answer('Супер!')

@admin_router.message(Command('change_menu'))
async def change_menu(message: Message, state: FSMContext):
    if message.chat.id == ADMIN_CHAT_ID:
        await message.answer('Какое меню будем использовать? (отправь пост ответом на это сообщение)')
        await state.set_state(Menu.menu)

@admin_router.message(Menu.menu)
async def menu(message: Message, state: FSMContext):
    if message.chat.id == ADMIN_CHAT_ID:
        await state.clear()
        await entities_service.change_menu(message)
        await message.answer('Супер!')

@admin_router.message(Command('change_places'))
async def change_places(message: Message, state: FSMContext):
    if message.chat.id == ADMIN_CHAT_ID:
        await message.answer('Сколько всего мест будет доступно для брони? (отправь число в ответ на это сообщение)')
        await state.set_state(Places.cnt)

@admin_router.message(Places.cnt)
async def places_cnt(message: Message, state: FSMContext):
    if message.chat.id == ADMIN_CHAT_ID:
        await message.answer('Какую карту столов будем использовать? (отправь пост ответом на это сообщение)')
        await entities_service.change_places_cnt(message)
        await state.set_state(Places.text)

@admin_router.message(Places.text)
async def places(message: Message, state: FSMContext):
    if message.chat.id == ADMIN_CHAT_ID:
        await state.clear()
        await entities_service.change_places(message)
        await message.answer('Супер!')