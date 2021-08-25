#!/usr/bin/env python3
import aiohttp
import asyncio



async def ainput(prompt=None):
    loop = asyncio.get_running_loop()
    return (await loop.run_in_executor(None, input, prompt))

async def aprint(*args, prompt=None):
    loop = asyncio.get_running_loop()
    return (await loop.run_in_executor(None, print, *args))


async def run_client(ws):
    await ws.send_str('Hello!')
    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == 'close cmd':
                await ws.close()
                break
            else:
                await aprint('Message received from server:', msg)
        elif msg.type == aiohttp.WSMsgType.CLOSED:
            print("CLOSED")
            break
        elif msg.type == aiohttp.WSMsgType.ERROR:
            print("ERROR")
            break
            
async def promt(ws):
    while True:
        msg = await ainput('Your text here: ')
        if not ws.closed:
            await ws.send_str(msg)
        else:
            print('Disconnected')
            break


async def sign_in(username, password):
    """ Аутентификация клиента

    :param username: Имя пользователя
    :param password: Пароль

    :returns: Куки для аутентификации через веб-сокет

    """
    async with aiohttp.ClientSession() as client:
        auth = await client.post('http://0.0.0.0:8080/signin', data={'username': username,
                                                                     'password': password},
                                 raise_for_status=True)
    return auth.cookies


async def room_list() -> dict:
    """
    Функция для получения списка комнат
    :rtype: dict

    """
    async with aiohttp.ClientSession() as client:
        rooms = await client.get('http://0.0.0.0:8080/rooms', raise_for_status=True)
    return json.loads(rooms)
    

async def main():
    # Читаем имя пользователя и пароль
    username = await ainput('Name: ')
    password = await ainput('Password: ')

    room_id = await ainput('Room id: ')

    cookies = await sign_in(username, password)
    # Пересоздаем сессию с куками
    async with aiohttp.ClientSession(cookies=cookies) as client:
        # И дальше работаем с сокетом как раньше
        async with client.ws_connect(f'http://0.0.0.0:8080/ws/{room_id}') as ws:
            await asyncio.gather(
                run_client(ws),
                promt(ws)
            )


if __name__ == '__main__':
    print('Type "exit" to quit')
    asyncio.run(main())
