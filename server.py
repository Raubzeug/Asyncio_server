#!/usr/bin/env python3

import asyncio
import concurrent.futures
import logging
import os

class Storage():
    def __init__(self):
        self.data = set()

    def save(self, data_to_save):
        self.data.add(data_to_save)

    def get(self, key):
        if key == '*':
            return sorted(list(self.data), key=lambda value: int(value.split(' ')[-1].strip()))
        else:
            result = []
            for i in self.data:
                if i.startswith(key):
                    result.append(i)
            if len(result) > 1:
                result = sorted(result, key=lambda value: int(value.split(' ')[-1].strip()))
            return result


class Parser():
    def __init__(self, data):
        self.data = data

    def parse(self):
        decoded_data = self.data.decode()

        if decoded_data.startswith('put'):
            data_to_save = decoded_data.split(' ', 1)[1]
            return 'put', data_to_save, 'ok\n\n'

        if decoded_data.startswith('get'):
            return 'get', decoded_data.split(' ', 1)[1].strip()

        else:
            return 'error\nwrong command\n\n'

class ServerError():
    pass

class Server:

    data_storage = Storage()

    def run_server(self, host, port):
        self._loop = asyncio.get_event_loop()
        self._coro = asyncio.start_server(self.handle_echo, host = host, port = port, loop = self._loop)
        self._server = self._loop.run_until_complete(self._coro)
        self._loop.run_forever()

    def stop_server(self):
        self._server.close()
        self._loop.run_until_complete(self._server.wait_closed())
        self._loop.close()

    """async handle_echo function creates a coroutine for every client."""
    async def handle_echo(self, reader, writer):

        peername = writer.get_extra_info('peername')
        logging.info('Accepted connection from {}'.format(peername))

        while True:
            try:
                data = await reader.read(1024)
                if data:
                    """from client we recieve some data and process it with instance of class Parser"""
                    parser = Parser(data)
                    """from parser we recieve a string, first word of which is a command, second (if it exists)
                    is some data from client (which we need to store or to retrieve)"""
                    command = parser.parse()

                    """if command is 'put' it means that we need to save the data and give a response when
                    it is saved.
                    if command is 'get' it means that we need to retrieve the data by some key or
                    all data from storage"""
                    if command[0] == 'put':
                        self.data_storage.save(command[1])
                        response = 'ok\n\n'
                        writer.write(response.encode('utf8'))
                    elif command[0] == 'get':
                        result = self.data_storage.get(command[1])
                        final = 'ok\n{0}\n'.format(''.join(result))
                        writer.write(final.encode('utf8'))
                    else:
                        writer.write(command.encode('utf8'))

                else:
                    logging.info('Connection from {} closed by peer'.format(peername))
                    break
            except concurrent.futures.TimeoutError:
                logging.info('Connection from {} closed by timeout'.format(peername))
                break

        writer.close()

def run_server(host, port):
    server = Server()
    try:
        server.run_server(host, port)
    except KeyboardInterrupt:
        pass  # Press Ctrl+C to stop
    finally:
        server.stop_server()
        logging.info('Server stopped')


if __name__ == '__main__':
    logging.basicConfig(filename=os.path.join(os.getcwd(), "server_log.log"), filemode='w', level=logging.DEBUG)
    run_server('127.0.0.1', 8888)
