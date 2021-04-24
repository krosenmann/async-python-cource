#!/usr/bin/env python3
import socket                    
import argparse

def parse_cli_arguments():
    parser = argparse.ArgumentParser(description="Простой сервер")
    parser.add_argument('--host', type=str, default='localhost')
    parser.add_argument('--port', type=int, default=9999)
    args = parser.parse_args()
    return args


BLOCK_LEN = 32                 # Для практики установим всего 32 байта
EOM = b"ENDOFMESSAGE___"        # End of message


def read_message(connection) -> bytes:
    message = b''
    while len(message) < len(EOM) or message[-len(EOM):] != EOM: # Обрабатываем условие нашего протокола.
        data = connection.recv(BLOCK_LEN)
        if not data:
            break
        assert isinstance(data[0], int), f"С данными что-то не так. Ожидаем байты, получили {type(data)}"
        message += data
    return message

def get_message_text(message):
    return message.decode('utf8')[:-len(EOM)]


def ask_name(connection) -> bytes:
    connection.send('Как тебя зовут'.encode('utf8') + EOM)
    raw_name = read_message(connection)
    connection.send('Привет, '.encode('utf8') + raw_name) # Надо послать сообщение, иначе клиент застрянет в ожидании ответа сервера после отправки имени
    name = get_message_text(raw_name)
    return name


def main(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as serversocket:

        serversocket.bind((host, port))
        # слушаем порт
        serversocket.listen()

        # Основной цикл программы. Ждем новых соеднинений.
        while True:
            # accept connections from outside
            connection, address = serversocket.accept()
            username = ask_name(connection)
            print(f"Соединение установлено с {address}")
            while True:                  # Цикл работы с соединением
                data = read_message(connection)
                if not data:    # Выходим из цикла работы с клиентом.
                    print("Соединение разорвано")
                    break
                data = username.encode('utf8') + b': ' + data # Работаем с байтами
                # Проблема 1: на сокет
                # приходят байты, поэтому в выводе мы видим кракозябры.
                print(get_message_text(data)) # Декодируем, выделяем и печатаем сообщение
                # Отправляем данные обратно клиенту.
                sendet = connection.send(data)
                assert sendet > 0, "Данные не отправлены, возможно соединение разорвано" # Удостоверимся, что данные ушли


if __name__ == '__main__':
    args = parse_cli_arguments()
    main(host=args.host, port=args.port)
