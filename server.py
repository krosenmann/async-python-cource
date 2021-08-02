#!/usr/bin/env python3
import aiohttp
from aiohttp import web

async def websocket_handler(request):

    ws = web.WebSocketResponse()
    await ws.prepare(request)

    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == 'close':
                await ws.close()
            else:
                await ws.send_str(msg.data + '/answer')
        elif msg.type == aiohttp.WSMsgType.ERROR:
            print('ws connection closed with exception %s' %
                  ws.exception())

    print('websocket connection closed')

    return ws


async def sign_in(request):
    users = request.app['USERS']
    data = await request.post()
    # Регистрация
    if data['username'] not in list(users.keys()):
        request.app['USERS'][data['username']] = data['password']
    # Проверяем, что пароль правильный
    if data['password'] != request.app['USERS'][data['username']]:
        raise web.HTTPUnauthorized('Wrong password!')
    # <<Сохранение сессии>>       Это решим в следующем упражнении
    return web.Response(text=f'Hello, {data["username"]}')


if __name__ == '__main__':
    app = web.Application()
    app.add_routes([web.get('/ws', websocket_handler)])
    web.run_app(app)
