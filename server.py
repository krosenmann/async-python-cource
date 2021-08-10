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
    # Если пользователь не залогинен (или не существует), то не даем ему подключиться.
    if user is None or user not in request.app['USERS']:
        raise web.HTTPUnauthorized()

    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == 'close':
                await ws.close()
            else:
                await ws.send_str(f'{user}: ' + msg.data + '/answer')
        elif msg.type == aiohttp.WSMsgType.ERROR:
            print('ws connection closed with exception %s' %
                  ws.exception())

    print('websocket connection closed')

    return ws

def create_app():
    fernet_key = fernet.Fernet.generate_key()
    SECRET_KEY = base64.urlsafe_b64decode(fernet_key)
    app = web.Application()
    app['USERS'] = {}           # Инициализируем пустым словарем
    app['USER CONNECTIONS'] = []
    setup(app, EncryptedCookieStorage(SECRET_KEY))
    app.add_routes([web.get('/ws', websocket_handler),
                    web.post('/signin', sign_in)])
    return app

if __name__ == '__main__':
    app = create_app()
    web.run_app(app)
