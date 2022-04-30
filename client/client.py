from login_window import Window
from main_window import ClientMainWindow
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import pyqtSignal, QObject
from clientstorage import ClientDatabase
from threading import Thread
from common.utils import send_message, convert_to_dict, suppress_qt_warnings
import argparse
from log.utils import log_deco
from time import time, sleep
from common.variables import (
    ACCOUNT_NAME,
    MESSAGE_STATUS,
    DEFAULT_IP,
    DEFAULT_PORT,
    DEFAULT_CLIENT_MODE,
)
from log import client_log_config
import logging
import hmac
import socket
from pydoc import cli
import sys
import os

sys.path.append(os.getcwd())
sys.path.append(os.path.dirname(__file__))


log_client = logging.getLogger("client_logger")


class Client(QObject):

    new_message = pyqtSignal(dict)

    def __init__(self, connection_address, connection_port):
        super().__init__()
        self.username = None
        self.database = None
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

        # try:
        #     send_message(self.transport, self.presence_msg())
        #     message = self.transport.recv(1024)
        #     message = convert_to_dict(message)
        #     self.process_response(message)
        # except:
        #     print('Произошла ошибка при подключении')
        # else:
        #     print('Успешное подключение')

    def success_login(self, username):
        self.username = username
        self.database = ClientDatabase(username)

    def presence_msg(self):
        message = {
            "action": "presence",
            "time": time(),
            "type": "status",
            "user": {"account_name": self.username, "status": MESSAGE_STATUS},
        }
        return message

    def process_response(self, response):
        if response["response"] == 200:
            return "SUCCESS"
        elif response["response"] == 400:
            raise Exception

    def sign_up(self, username, password):
        password = hmac.new(
            password.encode("utf-8"), f"{username}".encode("utf-8"), "MD5"
        )
        request = {
            "action": "sign up",
            "account_name": username,
            "password": password.hexdigest(),
        }
        self.MessageSender.messages_to_send.append(request)
        return request

    def log_in(self, username, password):
        password = hmac.new(
            password.encode("utf-8"), f"{username}".encode("utf-8"), "MD5"
        )
        request = {
            "action": "log in",
            "account_name": username,
            "password": password.hexdigest(),
        }
        self.MessageSender.messages_to_send.append(request)
        return request

    def create_message(self, to_user, message_text):
        message_to_send = {
            "action": "msg",
            "time": time(),
            "account_name": self.username,
            "destination": to_user,
            "message_text": message_text,
        }

        self.MessageSender.messages_to_send.append(message_to_send)
        return message_to_send

    def add_contact(self, contact):
        add_request = {
            "action": "add_contact",
            "time": time(),
            "account_name": self.username,
            "destination": contact,
        }
        self.MessageSender.messages_to_send.append(add_request)
        return add_request

    def del_contact(self, contact):
        del_request = {
            "action": "del_contact",
            "time": time(),
            "account_name": self.username,
            "destination": contact,
        }
        self.MessageSender.messages_to_send.append(del_request)
        return del_request

    def get_contacts(self):
        request = {
            "action": "get_contacts",
            "time": time(),
            "account_name": self.username,
        }
        return request

    def exit_message(self):
        request = {"action": "exit",
                   "time": time(), "account_name": self.username}
        self.MessageSender.messages_to_send.append(request)
        return request

    def find_user(self, username):
        request = {
            "action": "search",
            "time": time(),
            "account_name": self.username,
            "target_user": username,
        }
        self.MessageSender.messages_to_send.append(request)
        return request


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
                if (
                    message["action"] == "msg"
                    and message["message_text"]
                    and message["account_name"]
                ):
                    self.client.new_message.emit(message)
                elif (
                    message["action"] == "add_contact"
                    and message["status"] == "success"
                ):
                    self.client.new_message.emit(message)
                elif (
                    message["action"] == "del_contact"
                    and message["status"] == "success"
                ):
                    self.client.new_message.emit(message)
                elif (
                    message["action"] == "get_contacts"
                    and message["status"] == "success"
                ):
                    contacts = ", ".join(message["contacts"])
                elif message["action"] == "message_user":
                    if message["status"] == "success":
                        self.client.database.meet_user(message["target_user"])
                elif message["action"] == "search":
                    self.client.new_message.emit(message)
                elif message["action"] == "sign up":
                    if message["status"] == "success":
                        self.client.new_message.emit(message)
                    else:
                        self.client.new_message.emit(message)
                elif message["action"] == "log in":
                    if message["status"] == "success":
                        self.client.new_message.emit(message)
                    else:
                        print(message)
                        self.client.new_message.emit(message)
                else:
                    log_client.info(
                        f"Поступило некорректное сообщение с сервера: {message}"
                    )
            except Exception:
                log_client.critical(
                    f"Произошла ошибка при приёме сообщения {message}")
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
            except:
                log_client.critical(f"Ошибка при отправке сообщения {message}")
            else:
                print(f"Отправлено сообщение {message}")
                send_message(self.client.transport, message)


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("addr", default=DEFAULT_IP, nargs="?")
    arg_parser.add_argument("port", default=DEFAULT_PORT, type=int, nargs="?")
    namespace = arg_parser.parse_args()
    print(namespace.addr, namespace.port)

    client = Client(namespace.addr, namespace.port)
    client_app = QApplication(sys.argv)

    suppress_qt_warnings()

    login_window = Window(client)
    main_window = ClientMainWindow(client)
    login_window.logged_in.connect(main_window.success_login)
    client_app.exec_()
