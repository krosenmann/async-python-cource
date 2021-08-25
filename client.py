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


async def main():
    # Читаем имя пользователя и пароль
    username = await ainput('Name: ')
    password = await ainput('Password: ')

    room_id = await ainput('Room id: ')

    # Проходим аутентификацию. 
    # Если что-то пойдет не так, вылетит исключение за счет параметра raise_for_status=True
    async with aiohttp.ClientSession() as client:
        auth = await client.post('http://0.0.0.0:8080/signin', data={'username': username,
                                                                     'password': password},
                                 raise_for_status=True)
        print(auth)
    # Пересоздаем сессию с куками
    async with aiohttp.ClientSession(cookies=auth.cookies) as client:
        # И дальше работаем с сокетом как раньше
        async with client.ws_connect(f'http://0.0.0.0:8080/ws/{room_id}') as ws:
            await asyncio.gather(
                run_client(ws),
                promt(ws)
            )


if __name__ == '__main__':
    print('Type "exit" to quit')
    asyncio.run(main())
