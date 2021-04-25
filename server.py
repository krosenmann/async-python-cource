#!/usr/bin/env python3
import argparse
import queue
import select, socket


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

        serversocket.setblocking(False)
        serversocket.bind((host, port))
        # слушаем порт
        serversocket.listen()
        inputs = [serversocket]
        outputs = []
        message_queues = {}

        # Основной цикл программы. Ждем новых соеднинений.
        while inputs:
            readable, writable, exceptional = select.select(inputs, outputs, inputs)

            for sock in readable: # Перебираем сокеты на прослушивание.
                if sock is serversocket:
                    connection, address = serversocket.accept() # Принимаем соединение от клиентов
                    connection.setblocking(0)
                    inputs.append(connection) # Регистрируем соединение на чтение
                    outputs.append(connection) # Регистрируем на отправку
                    message_queues[connection] = queue.Queue() # И очередь сообщений для соединения. Сюда можно сразу же добавить приветсвенное сообщение
                    message_queues[connection].put('Как тебя зовут'.encode('utf8') + EOM)
                    print(f"Соединение установлено с {address}")
                else:
                    data = read_message(sock)
                    if data:
                        for q in message_queues.values():
                            q.put(data) # Регистрируем сообщение для отправки по всем соединениям
                        if sock not in outputs:
                            outputs.append(sock) # Регистрируем соединение в списке на отправку
                    else:
                        if sock in outputs:
                            outputs.remove(sock) # Соединение разорвано, удаляем соединения из списка на отправку
                        inputs.remove(sock)      # И из списка на прослушивание тоже удаляем
                        sock.close()             # Закрываем соединение
                        del message_queues[sock]  # Помечаем очередь для удаления
                        print("Соединение разорвано")

            for sock in writable: # Сокеты для отправки
                try:
                    message = message_queues[sock].get_nowait() # Неблокирующий get
                except queue.Empty:
                    outputs.remove(sock) # Сообщений нет, из очереди на отправку удаляем (по идее, это не обязательно)
                else:
                    print(get_message_text(message))
                    sock.send(message)

if __name__ == '__main__':
    args = parse_cli_arguments()
    main(host=args.host, port=args.port)
