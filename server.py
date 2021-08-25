#!/usr/bin/env python3
import aiohttp
from aiohttp import web
from aiohttp_session import setup, get_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage
import base64
from cryptography import fernet
from passlib.hash import pbkdf2_sha256

# --- База данных
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.schema import Table, ForeignKey
from sqlalchemy.future import select
from sqlalchemy import Column, Integer, String


DATABASE_URL = "sqlite+aiosqlite:///./chat.db"

Base = declarative_base()

# upr == Users per rooms
# Вспомогательная таблица для реализации пересечения множеств пользователей и комнат
# Необходимая штука для связи многие-ко-многим
_upr = Table('user_per_room', Base.metadata,
             Column('user_id', ForeignKey('users.id')),
             Column('room_id', ForeignKey('rooms.id')))


class User(Base):
    """Таблица с пользователями (и их паролями)
    """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False, unique=True)
    pass_hash = Column(String, nullable=False)


class Room(Base):
    """Комнаты со списками пользователей
    """
    __tablename__ = 'rooms'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    users = relationship("User", secondary=_upr) # Многие-ко-многим


# Утилиты для работы с базой
def create_table(app):
    """Создает таблицы в базе приложения, см. параметр ``DATABASE_URL``
    """
    # Нам нужен синхронный интерфейс к этой функции, поэтому просто оборачиваем.
    # И запускаем через вызов ``asyncio.run``
    async def _create_table(_app):
        print("Создаем таблицы")
        async with _app['DB ENGINE'].begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        print("Создано!")
    asyncio.run(_create_table(app))


# Сервер

async def sign_in(request):
    users = request.app['USERS']

    data = await request.post()

    async with request.app['DB SESSION']() as session:
        q = select(User).where(User.username == data['username'])
        user = (await session.execute(q)).one_or_none()
    # Регистрация
    if user is None:
        user = User(username=data['username'], pass_hash=pbkdf2_sha256.hash(data['password']))
        async with request.app['DB SESSION']() as session:
            session.add(user)
    else:
        user = user[0]

    # Проверяем, что пароль правильный
    pass_hash = user.pass_hash
    if not pbkdf2_sha256.verify(data['password'], pass_hash):
        raise web.HTTPUnauthorized(text='Wrong password!')

    session = await get_session(request)
    session['username'] = user.username
    return web.Response(text=f'Hello, {user.username}')


async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    session = await get_session(request)
    user = session.get('username', None)
    if user is None:
        raise web.HTTPUnauthorized()
    room_id = request.match_info['room_id']
    # Регистрируем сокет в комнате
    request.app['ROOMS'][room_id].append(ws)

    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == 'close':
                await ws.close()
            else:
                # Рассылка сообщения
                for socket in request.app['ROOMS'][room_id]:
                    await socket.send_str(f'{user}: ' + msg.data)
        elif msg.type == aiohttp.WSMsgType.ERROR:
            print('ws connection closed with exception %s' %
                  ws.exception())

    # Соединение закрыто, убираем сокет из списка
    request.app['ROOMS'][room_id].remove(ws)

    print('websocket connection closed')

    return ws


async def room_list(request):
    return web.json_response(data=list(request.app['ROOMS'].keys()))


def create_app():
    fernet_key = fernet.Fernet.generate_key()
    SECRET_KEY = base64.urlsafe_b64decode(fernet_key)
    app = web.Application()

    # Инициализация БД
    engine = create_async_engine(DATABASE_URL, future=True, echo=True)
    app['DB ENGINE'] = engine
    app['DB SESSION'] = sessionmaker(engine, expire_on_commit=False, 
                                     class_=AsyncSession)

    app['USERS'] = {}           # Инициализируем пустым словарем
    app['ROOMS'] = {
        '1': [],
        '2': [],
        '3': [],
    }
    # Добавить комнаты ключом ROOMS
    setup(app, EncryptedCookieStorage(SECRET_KEY))


    # Параметризацию для сокетов сюда - будут комнаты
    app.add_routes([web.get('/ws/{room_id}', websocket_handler),
                    web.post('/signin', sign_in),
                    web.get('/rooms', room_list)])
    return app

if __name__ == '__main__':
    app = create_app()
    web.run_app(app)
