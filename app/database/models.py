from sqlalchemy import BigInteger, String, ForeignKey, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine

engine = create_async_engine(url='sqlite+aiosqlite:///db.sqlite3')

async_session = async_sessionmaker(engine)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class Promocode(Base):
    __tablename__ = 'promo_codes'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(25), unique=True)
    description: Mapped[str] = mapped_column(String(100))
    used_flg: Mapped[bool] = mapped_column()

class Reservation(Base):
    __tablename__ = 'reservations'

    id: Mapped[int] = mapped_column(primary_key=True)
    reservation_start_time = mapped_column(DateTime)
    reservation_end_time = mapped_column(DateTime)
    reservation_user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    reservation_place_id: Mapped[int] = mapped_column()

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id = mapped_column(BigInteger)
    login: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(50))
    phone: Mapped[str] = mapped_column(String(15), unique=True)
    scores: Mapped[int] = mapped_column()

async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)