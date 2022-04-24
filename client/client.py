import sys
import os

sys.path.append(os.getcwd())
sys.path.append(os.path.dirname(__file__))

import socket
import logging
from log import client_log_config
from common.variables import ACCOUNT_NAME, MESSAGE_STATUS, DEFAULT_IP, DEFAULT_PORT, DEFAULT_CLIENT_MODE
from time import time
from log.utils import log_deco
import argparse
from common.utils import send_message, convert_to_dict, suppress_qt_warnings
from threading import Thread
from clientstorage import ClientDatabase
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QApplication
from main_window import ClientMainWindow

log_client = logging.getLogger('client_logger')



class Client(QObject):
    
    new_message = pyqtSignal(dict)
    
    def __init__(self, connection_address, connection_port, username):
        super().__init__()
        self.username = username
        self.database = ClientDatabase(self.username)
        self.transport = None

        self.init_connection(connection_address, connection_port)
        
        self.MessageSender = MessageSender()
        self.MessageSender.setClient(self)
        self.MessageSender.start()
        
        self.MessageReciever = MessageReciever()
        self.MessageReciever.setClient(self)
        self.MessageReciever.start()
        
    def init_connection(self, connection_address, connection_port):
        self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.transport.connect((connection_address, connection_port))

        try:
            send_message(self.transport, self.presence_msg())
            message = self.transport.recv(1024)
            message = convert_to_dict(message)
            self.process_response(message)
        except:
            print('Произошла ошибка при подключении')
        else:
            print('Успешное подключение')
    
    def presence_msg(self):
        message = {
            "action": "presence",
            "time": time(),
            "type": "status",
            "user": {
                "account_name": self.username,
                "status": MESSAGE_STATUS
            }
        }
        return message
    
    def process_response(self, response):
        if response['response'] == 200:
            return 'SUCCESS'
        elif response['response'] == 400:
            raise Exception


    def create_message(self, to_user, message_text):
        message_to_send = {
            'action': 'msg',
            'time': time(),
            'account_name': self.username,
            'destination': to_user,
            'message_text': message_text
        }
        
        self.MessageSender.messages_to_send.append(message_to_send)
        return message_to_send

    def add_contact(self, contact):
        add_request = {
            'action': 'add_contact',
            'time': time(),
            'account_name': self.username,
            'destination': contact
        }
        self.MessageSender.messages_to_send.append(add_request)
        return add_request
    
    def del_contact(self, contact):
        del_request = {
            'action': 'del_contact',
            'time': time(),
            'account_name': self.username,
            'destination': contact
        }
        self.MessageSender.messages_to_send.append(del_request)
        return del_request

    def get_contacts(self):
        request  = {
            'action': 'get_contacts',
            'time': time(),
            'account_name': self.username
        }
        return request
    
    def exit_message(self):
        request = {
            'action': 'exit',
            'time': time(),
            'account_name': self.username
        }
        self.MessageSender.messages_to_send.append(request)
        return request
 
    def users_interface(self):
        while True:
            action = input('Введите команду:')
            if action == 'message':
                message = self.create_message()
                try:
                    self.database.save_message_history(message['destination'], self.username, message["message_text"])
                except Exception as e:
                    print('Потеряно соединение с сервером.')
                    print(e)
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
        
class MessageReciever(Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        self.client = None
    
    def setClient(self, client):
        self.client = client
        
    def run(self):
        while True:
            try:
                message = self.client.transport.recv(1024)
                message = convert_to_dict(message)
                print(message)
                if message['action'] == 'msg' and message['message_text'] and message['account_name']:
                    print(f'Получено сообщение от {message["account_name"]}: {message["message_text"]}')

                    self.client.new_message.emit(message) 

                elif message['action'] == 'add_contact' and message['status'] == 'success':
                    print(f'Успешно добавлен контакт: {message["contact"]}')
                    
                    self.client.new_message.emit(message) 
                    
                elif message['action'] == 'del_contact' and message['status'] == 'success':
                    print(f'Успешно удален контакт: {message["contact"]}')
                    
                    self.client.new_message.emit(message) 
                    
                elif message['action'] == 'get_contacts' and message['status'] == 'success':
                    contacts = ', '.join(message['contacts'])
                    print(f'Список ваших контактов: {contacts}')
                elif message['action'] == 'message_user':
                    if message['status'] == 'success':
                        self.client.database.meet_user(message['target_user'])    
                else:
                    print(f'Поступило некорректное сообщение с сервера: {message}')
            except Exception:
                print('Произошла ошибка.')
                break
      
        
class MessageSender(Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        self.client = None
        self.messages_to_send = []
    
    def setClient(self, client):
        self.client = client
    
    def run(self):
        while True:
            try:
                message = self.messages_to_send.pop(0)
            except:
                pass
            else:
                print(message)
                send_message(self.client.transport, message)



if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('addr', default=DEFAULT_IP, nargs='?')
    arg_parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
    arg_parser.add_argument('-n', '--name', default='Sergei', nargs='?')
    namespace = arg_parser.parse_args()
    print(namespace.addr, namespace.port, namespace.name)
    
    client = Client(namespace.addr, namespace.port, namespace.name) 
    client_app = QApplication(sys.argv)
    
    suppress_qt_warnings()  
    main_window = ClientMainWindow(client)
    client_app.exec_()
    
    
    
    