#!/usr/bin/env python3

import time
import socket

class ClientError(socket.error):
    pass

class ClientSocketError(ClientError):
    pass

class ClientProtocolError (ClientError):
    pass


class Client:

    def __init__(self, host, port, timeout=None):
        self.host = host
        self.port = port
        try:
            self.sock = socket.create_connection((self.host, self.port), timeout)

        except socket.error as err:
            raise ClientError('Connection not successful', err)

    def put(self, metric_name, metric_value, timestamp = None):
        try:
            with self.sock as sock:
                timestamp = str(timestamp) if timestamp else str(int(time.time()))
                data_to_send = 'put {0} {1} {2}\n'.format(metric_name, metric_value, timestamp)
                sock.sendall(data_to_send.encode('utf8'))

                while True:
                    data = sock.recv(1024)
                    print(data.decode())

                    if not data:
                        break
                    elif data == b'ok\n\n':
                        return data.decode('utf8')
                    else:
                        raise ClientError

        except socket.error as err:
            raise ClientError('error in sending data', err)


    def get(self, request):
        metric_name, metric_value, timestamp = (0, 1, 2)
        data = b''
        metric_dict = {}

        try:
            with self.sock as sock:
                data_to_send = 'get {0}\n'.format(str(request))
                sock.sendall(data_to_send.encode('utf8'))
                while not data.endswith(b'\n\n'):
                    data += sock.recv(1024)

        except socket.error as err:
            raise ClientError('error in sending data', err)

        decoded_data = data.decode('utf8')
        information = decoded_data.split('\n')
        if 'error' in information:
            raise ClientError(' '.join(information))

        for i in range(len(information)):
            metric = information[i].split(' ')
            if len(metric) == 3:
                metric_dict.setdefault(metric[metric_name], [])
                metric_dict[metric[metric_name]].append((int(metric[timestamp]),
                                                         float(metric[metric_value])))

        return metric_dict

#checking client
if __name__ == '__main__':
    client = Client("127.0.0.1", 8888, timeout=5)
    client.put("test", 0.5, timestamp=1)
    client.put("test", 2.0, timestamp=2)
    client.put("test", 0.5, timestamp=3)
    client.put("load", 3, timestamp=4)
    client.put("load", 4, timestamp=5)
    print(client.get("*"))

    client.close()