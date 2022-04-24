import sys
import os
import logging
import argparse

from common.variables import *
from PyQt5.QtWidgets import QMainWindow, qApp, QMessageBox, QApplication, QListView
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QBrush, QColor, QFont
from PyQt5.QtCore import pyqtSlot, QEvent, Qt, QObject, pyqtSignal
from client_ui.main_client_window import Ui_UI_Client
from client.clientstorage import ClientDatabase
from threading import Thread, Lock
import socket
from common.utils import *
from time import time
from log import client_log_config

log_client = logging.getLogger('client_logger')


client_app = QApplication(sys.argv)

def suppress_qt_warnings():
    os.environ["QT_DEVICE_PIXEL_RATIO"] = "0"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    os.environ["QT_SCREEN_SCALE_FACTORS"] = "1"
    os.environ["QT_SCALE_FACTOR"] = "1"

class Client(QObject):
    
    new_message = pyqtSignal(str)
    
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

                    self.client.new_message.emit(message['account_name'])
                    
                    self.client.database.save_message_history(self.client.username, message["account_name"], message["message_text"])
                    self.client.database.meet_user(message['account_name'])   

                elif message['action'] == 'add_contact' and message['status'] == 'success':
                    print(f'Успешно добавлен контакт: {message["contact"]}')
                    
                    self.client.database.add_contact(message['contact'])
                    self.client.database.meet_user(message['contact'])  
                elif message['action'] == 'del_contact' and message['status'] == 'success':
                    print(f'Успешно удален контакт: {message["contact"]}')
                    
                    self.client.database.del_contact(message['contact'])
                    
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
            except IndexError:
                pass
            else:
                send_message(self.client.transport, message)


class ClientMainWindow(QMainWindow):
    def __init__(self, client:Client):
        super().__init__()
        
        self.client = client
        
        self.ui = Ui_UI_Client()
        self.ui.setupUi(self)
        
        # Exit button
        self.ui.action.triggered.connect(qApp.exit)
        
        # Select chat
        self.ui.chats_list.doubleClicked.connect(self.select_chat)
        
        # Send message button
        self.ui.send_msg.clicked.connect(self.send_message)
        self.ui.msg_area.installEventFilter(self)
        
        # Message history model
        self.message_history_model = QStandardItemModel()
        self.ui.chat_history.setModel(self.message_history_model)
        
        # Variables
        self.current_chat = None
        
        #Connection
        client.new_message.connect(self.message)
        
        self.known_users_update()
        self.show()
    
    # Select chat
    def select_chat(self):
        self.current_chat = self.ui.chats_list.currentIndex().data()
        self.message_history_update()
        self.known_users_update()
    
    # Message history
    def message_history_update(self):
        self.message_history_model.clear()
    
        message_list = sorted(self.client.database.get_message_history(self.current_chat), key=lambda item: item[2])
        
        for message in message_list:
            if message[0] == self.current_chat:
                message = QStandardItem(f'{message[1]}: \n{message[3]}')
                message.setEditable(False)
                message.setBackground(QBrush(QColor(255, 213, 213)))
                message.setTextAlignment(Qt.AlignLeft)
                self.message_history_model.appendRow(message)
            else:
                message = QStandardItem(f'{message[1]}: \n{message[3]}')
                message.setEditable(False)
                message.setBackground(QBrush(QColor(61, 255, 171)))
                message.setTextAlignment(Qt.AlignRight)
                self.message_history_model.appendRow(message)
            
        log_client.info(message_list)
        
    # List of users we are familiar with
    def known_users_update(self):
        known_users = self.client.database.get_known_users()
        self.contact_model = QStandardItemModel()
        for i in known_users:
            if i == self.current_chat:
                item = QStandardItem(i)
                font = QFont()
                font.setBold(True)
                item.setFont(font)
                item.setEditable(False)
                self.contact_model.appendRow(item)
                continue
            item = QStandardItem(i)
            item.setEditable(False)
            self.contact_model.appendRow(item)
        self.ui.chats_list.setModel(self.contact_model)
    
    # Send message to user
    def send_message(self):
        message_text = self.ui.msg_area.toPlainText()
        self.ui.msg_area.clear()
        try:
            self.client.create_message(self.current_chat, message_text)
            log_client.info('Сообщение отправлено')
        except Exception as fail:
            log_client.critical(f'Сообщение не отправлено {fail}')
        else:
            self.client.database.save_message_history(self.current_chat, self.client.username, message_text)
            self.message_history_update()
       
    # Handle message from user 
    @pyqtSlot(str)
    def message(self, sender):
        log_client.info('Слот отработал')
        if sender == self.current_chat:
           self.message_history_update()
           
    # Send message - press Enter
    def eventFilter(self, obj: 'QObject', event: 'QEvent'):
        if event.type() == QEvent.KeyPress and obj is self.ui.msg_area:
            if event.key() == Qt.Key.Key_Return and self.ui.msg_area.hasFocus():
                self.send_message()
        return super().eventFilter(obj, event)
    

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('addr', default=DEFAULT_IP, nargs='?')
    arg_parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
    arg_parser.add_argument('-n', '--name', default='Sergei', nargs='?')
    namespace = arg_parser.parse_args()
    print(namespace.addr, namespace.port, namespace.name)
    
    client = Client(namespace.addr, namespace.port, namespace.name) 
    
    suppress_qt_warnings()  
    main_window = ClientMainWindow(client)
    client_app.exec_()