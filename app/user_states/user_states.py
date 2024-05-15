from aiogram.fsm.state import State, StatesGroup

class Register(StatesGroup):
    number = State()

class Friend(StatesGroup):
    phone = State()

class Resume(StatesGroup):
    resume = State()

class Book(StatesGroup):
    date = State()

    number = State()

    time_interval = State()

    phone = State()
