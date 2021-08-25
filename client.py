#!/usr/bin/env python3
import aiohttp
import asyncio
from contextlib import asynccontextmanager


# Определим, что именно можно будет импортировать, если использовать программу, как библиотеку
__all__ = [
    'recieve',
    'send',
    'ws_connect',
    'sing_in',
    'room_list',
]


async def ainput(prompt=None):
    loop = asyncio.get_running_loop()
    return (await loop.run_in_executor(None, input, prompt))

async def aprint(*args, prompt=None):
    loop = asyncio.get_running_loop()
    return (await loop.run_in_executor(None, print, *args))


async def recieve(ws, callback):
    """Цикл чтения данных из сокета

    :param ws: веб-сокет
    :param callback: функция, которая будет обрабатывать данные.

    """
    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == 'close cmd':
                await ws.close()
                break
            else:
                callback(msg)
        elif msg.type == aiohttp.WSMsgType.CLOSED:
            print("CLOSED")
            break
        elif msg.type == aiohttp.WSMsgType.ERROR:
            print("ERROR")
            break


async def send(ws, message):
    """Отправить сообщение через сокет

    :param ws: 
    :param message: 
    :returns: 

    """
    
    if not ws.closed:
        await ws.send_str(msg)
    else:
        print('Disconnected')

@asynccontextmanager
async def ws_connect(cookies, room):
    """Подключение к вебсокету

    :param cookie: cookie object
    :returns: клиент aiohttp WebSocket

    """
    
    async with aiohttp.ClientSession(cookies=cookies) as client:
        async with client.ws_connect(f'http://0.0.0.0:8080/ws/{room}') as web_socket:
            yield web_socket


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
    

# --- Интерфейс командной строки

async def promt(ws):
    while True:
        msg = await ainput('Your text here: ')
        if not ws.closed:
            await ws.send_str(msg)
        else:
            print('Disconnected')
            break


async def main():
    """CLI-интерфейс для использования библиотеки в качестве программы
    """
    # Читаем имя пользователя и пароль
    username = await ainput('Name: ')
    password = await ainput('Password: ')

    room_id = await ainput('Room id: ')

    cookies = await sign_in(username, password)

    # Пересоздаем сессию с куками
    async with ws_connect(cookies, room_id) as socket:
        await asyncio.gather(recieve(socket, callback=print), promt(socket))
    

if __name__ == '__main__':
    print('Type "exit" to quit')
    asyncio.run(main())
