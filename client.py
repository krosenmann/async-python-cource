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

async def promt(ws):
    while True:
        msg = await ainput('Your text here: ')
        await ws.send_str(msg)


async def main():
    async with aiohttp.ClientSession().ws_connect('http://0.0.0.0:8080/ws') as ws:
        await asyncio.gather(
            run_client(ws),
            promt(ws)
        )


if __name__ == '__main__':
    print('Type "exit" to quit')
    asyncio.run(main())
