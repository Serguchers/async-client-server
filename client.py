from time import time
from common.variables import ACCOUNT_NAME, MESSAGE_STATUS, DEFAULT_IP, DEFAULT_PORT, DEFAULT_CLIENT_MODE
import sys
import socket
import logging
from log import client_log_config
from log.utils import log_deco
import argparse
from common.utils import send_message, convert_to_dict
from threading import Thread
from clientstorage import ClientDatabase
log_client = logging.getLogger('client_logger')



class Client:
    def __init__(self, connection_address, connection_port, username):
        self.username = username
        self.database = ClientDatabase(self.username)
        self.transport = None

        self.init_connection(connection_address, connection_port)
        
    def init_connection(self, connection_address, connection_port):
         self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
         self.transport.connect((connection_address, connection_port))
        
    @staticmethod
    def presence_msg(account_name):
        message = {
            "action": "presence",
            "time": time(),
            "type": "status",
            "user": {
                "account_name": account_name,
                "status": MESSAGE_STATUS
            }
        }
        return message
    
    @staticmethod
    def process_response(response):
        if response['response'] == 200:
            return 'SUCCESS'
        elif response['response'] == 400:
            raise Exception


    def create_message(self):
        to_user = input('Введите имя получателя: ')
        message = input('Введите сообщение для отправки: ')
 
        message_to_send = {
            'action': 'msg',
            'time': time(),
            'account_name': self.username,
            'destination': to_user,
            'message_text': message
        }
        return message_to_send

    def change_contacts(self):
        action = input('Введите add/del, чтобы добавить/удалить контак:')
        to_user = input('Введите имя контакта: ')
 
        add_request = {
            'action': f'{action}_contact',
            'time': time(),
            'account_name': self.username,
            'destination': to_user
        }
        return add_request

    def get_contacts(self):
        request  = {
            'action': 'get_contacts',
            'time': time(),
            'account_name': self.username
        }
        return request
    
    def process_message_from_server(self):
        while True:
            try:
                message = self.transport.recv(1024)
                message = convert_to_dict(message)
                if message['action'] == 'msg' and message['message_text'] and message['account_name']:
                    print(f'Получено сообщение от {message["account_name"]}: {message["message_text"]}')
                    self.database.save_message_history(self.username, message["account_name"], message["message_text"])
                    self.database.meet_user(message['account_name'])   
                elif message['action'] == 'add_contact' and message['status'] == 'success':
                    print(f'Успешно добавлен контакт: {message["contact"]}')
                    self.database.add_contact(message['contact'])
                    self.database.meet_user(message['contact'])  
                elif message['action'] == 'del_contact' and message['status'] == 'success':
                    print(f'Успешно удален контакт: {message["contact"]}')
                elif message['action'] == 'get_contacts' and message['status'] == 'success':
                    contacts = ', '.join(message['contacts'])
                    print(f'Список ваших контактов: {contacts}')
                elif message['action'] == 'message_user':
                    if message['status'] == 'success':
                        self.database.meet_user(message['target_user'])    
                else:
                    print(f'Поступило некорректное сообщение с сервера: {message}')
            except:
                print('Произошла ошибка.')
                break
            
    
    def users_interface(self):
        while True:
            action = input('Введите команду:')
            if action == 'message':
                message = self.create_message()
                try:
                    send_message(self.transport, message)
                    self.database.save_message_history(message['destination'], self.username, message["message_text"])
                except:
                    print('Потеряно соединение с сервером.')
                    sys.exit(1)
            elif action == 'edit contacts':
                request = self.change_contacts()
                try:
                    send_message(self.transport, request)
                    if request['action'] == 'add_contact':
                        self.database.add_contact(request['destination'])
                    elif request['action'] == 'del_contact':
                        self.database.del_contact(request['destination'])
                except:
                    print('Потеряно соединение с сервером.')
                    sys.exit(1)
            elif action =='get contacts':
                request = self.get_contacts()
                try:
                    send_message(self.transport, request)
                except:
                    print('Потеряно соединение с сервером.')
                    sys.exit(1)    
            elif action == 'help':
                Client.print_help()
            elif action == 'exit':
                print('Завершение работы.')
                break
            elif action:
                print('Неверная команда.')
            
        
    
    @staticmethod
    def print_help():
        """Функция выводящяя справку по использованию"""
        print('Поддерживаемые команды:')
        print('message - отправить сообщение. Кому и текст будет запрошены отдельно.')
        print('edit contacts - добавить/удалить контакт')
        print('get contacts - получить список ваших контактов')
        print('help - вывести подсказки по командам')
        print('exit - выход из программы')
        


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('addr', default=DEFAULT_IP, nargs='?')
    arg_parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
    arg_parser.add_argument('-n', '--name', default='test', nargs='?')
    namespace = arg_parser.parse_args()
    print(namespace.addr, namespace.port, namespace.name)
    
    client = Client(namespace.addr, namespace.port, namespace.name)
    try:
        send_message(client.transport, client.presence_msg(client.username))
        message = client.transport.recv(1024)
        message = convert_to_dict(message)
        client.process_response(message)
    except:
        print('Произошла ошибка при подключении.')
        sys.exit(1)
    else:
        print('Успешное подключение.')
        
    message_receiver = Thread(target=client.process_message_from_server, daemon=True)
    message_receiver.start()
    
    user_interface = Thread(target=client.users_interface, daemon=True)
    user_interface.start()
    
    while True:
        if message_receiver.is_alive() and user_interface.is_alive():
            continue
        break
    
    
    
    