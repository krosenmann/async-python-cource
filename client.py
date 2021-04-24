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
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as clientsocket:
        clientsocket.connect((host, port))
        while True:
            message = input('> ')
            clientsocket.send(message.encode('utf8'))
            response = clientsocket.recv(4096).decode('utf8')
            print(response)

if __name__ == '__main__':
    args = parse_cli_arguments()
    main(host=args.host, port=args.port)
