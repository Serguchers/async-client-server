import re
from base import Base
import json
import sys
from common.variables import ACTIONS, MAX_CONNECTIONS, DEFAULT_PORT
from time import time
import socket
import logging
from log import server_log_config
from log.utils import log_deco
import select
import argparse

log_server = logging.getLogger('server_logger')


class Server(Base):
    def __init__(self, connection_port, connection_address):
        super().__init__()
        self.connection_port = connection_port
        self.connection_address = connection_address

        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        client = (self.connection_address, self.connection_port)
        self.connection.bind(client)
        self.connection.settimeout(0.5)

        self.connection.listen(MAX_CONNECTIONS)

        self.clients = []
        self.messages = []


    @log_deco(logger=log_server)
    def process_message(self, message, client):
        if message["action"] == 'presence' and message["time"]:
            Base.send_message(client, {'response': 200})
            return True

        if message['action'] == 'msg' and message['time'] and message['account_name'] \
            and message['message_text']:
            self.messages.append(message)
            return True

        Base.send_message(client, {"response": 400,
                "alert": "Wrong message format!"})
        return False

    @log_deco(logger=log_server)
    def run(self):

        while True:
            try:
                client, client_address = self.connection.accept()
            except:
                pass
            else:
                self.clients.append(client)
                print('Пользователь подключился')
            
            clients_to_read = []
            clients_to_send = []
            

            if self.clients:
                clients_to_read, clients_to_send, errs = select.select(
                    self.clients, self.clients, [])

            if clients_to_read:
                for client in clients_to_read:
                    try:
                        client_message = Base.get_message(client)
                        self.process_message(client_message, client)
                    except:
                        self.clients.remove(client)
            
            if self.messages and clients_to_send:
                message_to_send = self.messages.pop(0)
                message_to_send['time'] = time()
                
                for client in clients_to_send:
                    try:
                        Base.send_message(client, message_to_send)
                    except:
                        self.clients.remove(client)




if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
    arg_parser.add_argument('-a', default='', nargs='?')
    namespace = arg_parser.parse_args()
    
    server = Server(namespace.p, namespace.a)
    server.run()
