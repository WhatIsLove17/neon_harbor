import jsonpickle
from app.core.posts import Post
from aiogram.types import Message
from aiogram import Bot
import app.database.requests as requests
import json

welcome_post = Post(
    text="Привет! Я чат-бот клуба «Неоновая Гавань»!🥳\n\
Насколько мне известно, ты из тех, кто любит хороший отдых.\n\
Хочешь получить промокод на коктейль?",
)

bar_menu = Post(
    text="БАРНОЕ МЕНЮ!!!",
)

menu = Post(
    text="А вот и покушать!",
)

places = Post(
    text="Давай посмотрим бронь столиков:",
)

places_cnt = 10

async def get_welcome_post():
    return welcome_post

async def get_menu_bar():
    return bar_menu

async def get_menu():
    return menu

async def get_places():
    return places

async def get_places_count():
    return places_cnt

async def get_core_entities():

    global welcome_post, bar_menu, menu, places, places_cnt

    try:
        with open('welcome_post.json') as f:
            welcome_post = jsonpickle.decode(json.loads(f.read()))

        with open('bar_menu.json') as f:
            bar_menu = jsonpickle.decode(json.loads(f.read()))

        with open('menu.json') as f:
            menu = jsonpickle.decode(json.loads(f.read()))

        with open('places.json') as f:
            places = jsonpickle.decode(json.loads(f.read()))

        with open('places_cnt.json') as f:
            places_cnt = jsonpickle.decode(json.loads(f.read()))
    except OSError:
        pass

async def save_welcome_post():
    with open('welcome_post.json', 'w') as f:
        json.dump(jsonpickle.dumps(welcome_post), f)

async def save_bar_menu():
    with open('bar_menu.json', 'w') as f:
        json.dump(jsonpickle.dumps(bar_menu), f)

async def save_menu():
    with open('menu.json', 'w') as f:
        json.dump(jsonpickle.dumps(menu), f)

async def save_places():
    with open('places.json', 'w') as f:
        json.dump(jsonpickle.dumps(places), f)

async def save_places_cnt():
    with open('save_places_cnt.json', 'w') as f:
        json.dump(jsonpickle.dumps(places_cnt), f)

async def send_post_all_users(message: Message, bot: Bot):
    message_text = message.caption if message.caption else message.text
    photo_id = message.photo[-1].file_id if message.photo else None
    video_id = message.video.file_id if message.video else None
    doc_id = message.document.file_id if message.document else None

    for user in await requests.get_all_users():
        try:
            if photo_id:
                if message_text:
                    await bot.send_photo(chat_id=user.chat_id, photo=photo_id, caption=message_text)
                else:
                    await bot.send_photo(chat_id=user.chat_id, photo=photo_id)
            elif video_id:
                if message_text:
                    await bot.send_video(chat_id=user.chat_id, video=video_id, caption=message_text)
                else:
                    await bot.send_video(chat_id=user.chat_id, video=video_id)
            elif doc_id:
                if message_text:
                    await bot.send_document(chat_id=user.chat_id, document=doc_id, caption=message_text)
                else:
                    await bot.send_document(chat_id=user.chat_id, document=doc_id)
            else:
                await bot.send_message(user.chat_id, message_text)
        except Exception as e:
            message.answer('Не получилось отправить пользователям пост:\n' + e)

async def change_welcome_post(message: Message):
    global welcome_post

    welcome_post = await get_ids(message)
    await save_welcome_post()

async def change_bar_menu(message: Message):
    global bar_menu

    bar_menu = await get_ids(message)
    await save_bar_menu()

async def change_menu(message: Message):
    global menu

    menu = await get_ids(message)
    await save_menu()

async def change_places(message: Message):
    global places

    places = await get_ids(message)
    await save_places()

async def change_places_cnt(message: Message):
    global places_cnt

    try:
        places_cnt = int(message.text)
    except ValueError:
        print("That's not an int!")

    await save_places_cnt()

async def get_ids(message: Message):
    message_text = message.caption if message.caption else message.text
    photo_id = message.photo[-1].file_id if message.photo else None
    video_id = message.video.file_id if message.video else None
    doc_id = message.document.file_id if message.document else None

    return Post(text=message_text, photo=photo_id, video=video_id, doc=doc_id)