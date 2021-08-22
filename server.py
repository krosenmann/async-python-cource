#!/usr/bin/env python3
import aiohttp
from aiohttp import web
from aiohttp_session import setup, get_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage
import base64
from cryptography import fernet


async def sign_in(request):
    users = request.app['USERS']
    data = await request.post()
    # Регистрация
    if data['username'] not in list(users.keys()):
        request.app['USERS'][data['username']] = data['password']
    # Проверяем, что пароль правильный
    if data['password'] != request.app['USERS'][data['username']]:
        raise web.HTTPUnauthorized('Wrong password!')
    session = await get_session(request)
    session['username'] = data['username']       # Это решим в следующем упражнении
    return web.Response(text=f'Hello, {data["username"]}')


async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    session = await get_session(request)
    user = session.get('username', None)
    if user is None or user not in request.app['USERS']:
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
    request.app['USER CONNECTIONS'].remove(ws)

    print('websocket connection closed')

    return ws


async def room_list(request):
    return web.json_response(data=list(request.app['ROOMS'].keys()))


def create_app():
    fernet_key = fernet.Fernet.generate_key()
    SECRET_KEY = base64.urlsafe_b64decode(fernet_key)
    app = web.Application()
    app['USERS'] = {}           # Инициализируем пустым словарем
    app['ROOMS'] = {
        '1': [],
        '2': [],
        '3': [],
    }
    # Комнаты проинициализировать здесь (идентификатор, а под ним - список юзеров)
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
