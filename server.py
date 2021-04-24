#!/usr/bin/env python3
import socket
import argparse

def parse_cli_arguments():
    parser = argparse.ArgumentParser(description="Простой сервер")
    parser.add_argument('--host', type=str, default='localhost')
    parser.add_argument('--port', type=int, default=9999)
    args = parser.parse_args()
    return args


def main(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as serversocket:

        serversocket.bind((host, port))
        # слушаем порт
        serversocket.listen()

        # Основной цикл программы. Ждем новых соеднинений.
        while True:
            # accept connections from outside
            connection, address = serversocket.accept()
            print(f"Соединение установлено с {address}")
            while True:                  # Цикл работы с соединением
                data = connection.recv(4096) # man 2 recv
                # Когда клиент отключается, ``recv`` возвращает пустое сообщение: ``b''``.
                if not data:
                    break
                # Инвариант клиента. В корректно работающей программе это условие всегда верно.
                assert isinstance(data[0], int), f"С данными что-то не так. Ожидаем байты, получили {type(data)}"
                # Проблема 1: на сокет
                # приходят байты, поэтому в выводе мы видим кракозябры.
                print(data.decode('utf8'))
                # Отправляем данные обратно клиенту.
                sendet = connection.send(data)
                assert sendet > 0, "Данные не отправлены, возможно соединение разорвано" # Удостоверимся, что данные ушли


if __name__ == '__main__':
    args = parse_cli_arguments()
    main(host=args.host, port=args.port)
