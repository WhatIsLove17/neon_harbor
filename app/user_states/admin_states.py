from aiogram.fsm.state import State, StatesGroup

class Notify(StatesGroup):
    post = State()

class Post(StatesGroup):
    welcome_post = State()

class BarMenu(StatesGroup):
    bar_menu = State()

class Menu(StatesGroup):
    menu = State()

class Places(StatesGroup):
    cnt = State()

    text = State()

class Book(StatesGroup):
    book_info = State()

class Reservs(StatesGroup):
    date = State()

class RemoveBook(StatesGroup):
    book_info = State()

class AddPromo(StatesGroup):
    name = State()
    desc = State()

class UsePromo(StatesGroup):
    name = State()

class ChangeScores(StatesGroup):
    info = State()