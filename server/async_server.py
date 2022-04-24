import argparse
import asyncio
import json
import sys
import configparser
import os
sys.path.append(os.getcwd())
sys.path.append(os.path.dirname(__file__))

from threading import Lock, Thread
from common.utils import convert_to_dict, suppress_qt_warnings, send_message_server
from common.variables import ACTIONS, DEFAULT_PORT, ENCODING, MAX_CONNECTIONS
from server.serverstorage import ServerStorage
from server.server_gui import MainWindow, HistoryWindow, ConfigWindow, gui_create_model, create_stat_model
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QStandardItemModel, QStandardItem

CLIENTS = {}
new_active_user = False

class Server(Thread):
    def __init__(self, connection_port, connection_address, database='server_base.db3'):
        """
        Server initalizator. Starts message processor and message sender subprocesses.
        Args:
            connection_port (int): connection port
            connection_address (str): connection address
        """      
        super().__init__()
        self.connection_port = connection_port
        self.connection_address = connection_address
        self.server_storage = ServerStorage(database)
        self.message_processor = MessageProcessor(self)
        self.message_processor.start()
        self.message_sender = MessageSender(self)
        self.message_sender.start()
        
    
    def run(self):
        asyncio.run(self.run_server())
        
    async def run_server(self):
        """
        Main runner, starts serving clients.
        """
        runner = await asyncio.start_server(self.process_client, self.connection_address, self.connection_port)
        await runner.serve_forever()
        
    async def process_client(self, reader, writer):
        """
        Accepts data from client. 
        Send client message to message processor.
        Args:
            reader : asycnio reader obj
            writer : asyncio writer obj
        """
        while True:
            try:
                message = await self.process_client_message(reader)
            except ConnectionResetError:
                to_remove = tuple(filter(lambda x: x[1] == (reader, writer), CLIENTS.items()))
                del CLIENTS[to_remove[0][0]]
                break
                
            self.message_processor.message_queue.append({'message': message,
                                                         'reader': reader,
                                                         'writer': writer})

                  
    async def process_client_message(self, reader, delimiter=b'\n'):
        """
        Read client message.
        Args:
            reader : asycnio reader obj
            delimiter (bytes, optional): stops reading at delimiter

        Returns:
            bytes: encoded message
        """
        message = await reader.read(1000)
        return message
        
        


class MessageProcessor(Thread):
    def __init__(self, server):
        """
        Processes messages. Message sorting with further transfer to MessageSender.
        Args:
            server (Server): server object
        """
        super().__init__()
        self.daemon = True
        self.server = server
        self.storage = server.server_storage
        self.message_queue = []
        self.message_sender = None
    
    def run(self):
        while True:
            try:
                data = self.message_queue.pop(0)
                data['message'] = convert_to_dict(data['message'])
            except:
                pass
            else:
                self.parse_message(data)
    
    def parse_message(self, data):
        """
        Check message action and message format.
        Args:
            data (dict): usefull data related to message
        """
        message = data['message']
        global new_active_user
        if message["action"] == 'presence' and message["time"]:
            CLIENTS[message['user']['account_name']] = (data['reader'], data['writer'])
            self.server.message_sender.messages_to_send.append({'response': 200,
                                                                'sender': message['user']['account_name'],
                                                                'action': 'initial'})
            user_ip, user_port = data['writer'].get_extra_info('peername')
            self.storage.login_user(message['user']['account_name'], user_ip, user_port)
            new_active_user = True

        elif message['action'] == 'msg' and message['time'] and message['account_name'] \
            and message['message_text'] and message['destination']:
            self.storage.write_statistics(message['account_name'], 'sent')
            self.storage.write_statistics(message['account_name'], 'accepted')
            self.server.message_sender.messages_to_send.append(message)
        
        elif message['action'] == 'add_contact' and message['account_name'] and message['destination']:
            try:
                self.storage.add_contact(message['account_name'], message['destination'])
            except:
                self.server.message_sender.messages_to_send.append({'response': 400,
                                                                    'sender': message['account_name'],
                                                                    'action': 'add_contact',
                                                                    'contact': message['destination'],
                                                                    'status': 'failed'})
            else:
               self.server.message_sender.messages_to_send.append({'response': 200,
                                                                    'sender': message['account_name'],
                                                                    'action': 'add_contact',
                                                                    'contact': message['destination'],
                                                                    'status': 'success'}) 
        elif message['action'] == 'del_contact' and message['account_name'] and message['destination']:
            try:
                self.storage.del_contact(message['account_name'], message['destination'])
            except:
                self.server.message_sender.messages_to_send.append({'response': 400,
                                                                    'sender': message['account_name'],
                                                                    'action': 'del_contact',
                                                                    'contact': message['destination'],
                                                                    'status': 'failed'})
            else:
               self.server.message_sender.messages_to_send.append({'response': 200,
                                                                    'sender': message['account_name'],
                                                                    'action': 'del_contact',
                                                                    'contact': message['destination'],
                                                                    'status': 'success'}) 
        elif message['action'] == 'get_contacts' and message['account_name']:
            try:
                contacts = self.storage.get_users_contacts(message['account_name'])
            except:
                pass
            else:
                self.server.message_sender.messages_to_send.append({'response': 200,
                                                                    'destination': message['account_name'],
                                                                    'action': 'get_contacts',
                                                                    'contacts': contacts,
                                                                    'status': 'success'}) 
        elif message['action'] == 'exit' and message['account_name']:
            self.storage.logout_user(message['account_name'])
            new_active_user = True

        else:
            self.server.message_sender.messages_to_send.append({"response": 400, 
                                                                "alert": "Wrong message format!",
                                                                'destination': data['writer'],
                                                                'action': 'error'})
        return
        

class MessageSender(Thread):
    def __init__(self, server):
        """
        Object responsible for sending message to destination.
        """
        super().__init__()
        self.daemon = True
        self.storage = server.server_storage
        self.messages_to_send = []
    
    def run(self):
        while True:
            try:
                message = self.messages_to_send.pop(0)
            except:
                pass
            else:
                self.send_message(message)
        
    def send_message(self, message):
        """
        If message is error or initial send back to owner.
        If message is sent to someone, send to destination.

        Args:
            message (dict): data related to message
        """
        
        if message['action'] == 'initial' or message['action'] == 'error':
            send_message_server(CLIENTS, message, 'sender')
        
        if message['action'] == 'msg':
            try:
                send_message_server(CLIENTS, message, 'destination')
            except:
                message = {'action': 'message_user','response': 400, 
                           'destination': message['account_name'], 'status': 'failed'}
                send_message_server(CLIENTS, message, 'destination')
            else:
                message = {'action': 'message_user', 'response': 200, 
                            'destination': message['account_name'], 'target_user': message['destination'],
                            'status': 'success'}
                send_message_server(CLIENTS, message, 'destination')
        
        if message['action'] == 'add_contact':
            send_message_server(CLIENTS, message, 'sender')
        
        if message['action'] == 'del_contact':
            send_message_server(CLIENTS, message, 'sender')

        if message['action'] == 'get_contacts':
            send_message_server(CLIENTS, message, 'destination')
        
        
        
        
if __name__ == '__main__':
    suppress_qt_warnings()
    
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
    arg_parser.add_argument('-a', default='127.0.0.1', nargs='?')
    namespace = arg_parser.parse_args()
    
    config = configparser.ConfigParser()
    config_path = f'{os.path.dirname(os.path.realpath(__file__))}/server.ini'
    config.read(config_path)
    config['SETTINGS']['database_path'] = os.path.dirname(__file__)
    
    database_path = os.path.join(config['SETTINGS']['database_path'], config['SETTINGS']['database_file'])
    server = Server(namespace.p, namespace.a, database=database_path)
    server.daemon = True
    server.start()

    server_app = QApplication(sys.argv)
    main_window = MainWindow()
    
    main_window.statusBar().showMessage('Server is working')
    main_window.active_clients_table.setModel(gui_create_model(server.server_storage))
    main_window.active_clients_table.resizeColumnsToContents()
    main_window.active_clients_table.resizeRowsToContents()
    
    def list_update():
        global new_active_user
        if new_active_user:
            main_window.active_clients_table.setModel(
                gui_create_model(server.server_storage))
            main_window.active_clients_table.resizeColumnsToContents()
            main_window.active_clients_table.resizeRowsToContents()
            new_active_user = False
            
    def show_statistics():
        global statistics_window
        statistics_window = HistoryWindow()
        statistics_window.history_table.setModel(create_stat_model(server.server_storage))
        statistics_window.history_table.resizeColumnsToContents()
        statistics_window.history_table.resizeRowsToContents()
        statistics_window.show()
        
    def server_config():
        global config_window
        config_window = ConfigWindow()
        config_window.db_path.insert(config['SETTINGS']['database_path'])
        config_window.db_file.insert(config['SETTINGS']['database_file'])
        config_window.ip.insert(config['SETTINGS']['listen_address'])
        config_window.port.insert(config['SETTINGS']['default_port'])
        config_window.save_btn.clicked.connect(save_server_config)
        
    def save_server_config():
        global config_window
        message =QMessageBox()
        config['SETTINGS']['database_path'] = config_window.db_path.text()
        config['SETTINGS']['database_file'] = config_window.db_file.text()

        try:
            port = int(config_window.port.text())
        except:
            message.warning(config_window, 'Error', 'Port must be a number')
        else:
            config['SETTINGS']['listed_address'] = config_window.ip.text()
            if 1023 < port < 65536:
                config['SETTINGS']['default_port'] = str(port)
                with open('server.ini', 'w') as conf:
                    config.write(conf)
                    message.information(config_window, 'Success', 'Settings are successfully saved!')
            else:
                message.warning(config_window, 'Error', 'Port value should be in range 1023-65536')
            
            
            
    timer = QTimer()
    timer.timeout.connect(list_update)
    timer.start(1000)
    
    main_window.refresh_button.triggered.connect(list_update)
    main_window.show_history_button.triggered.connect(show_statistics)
    main_window.config_btn.triggered.connect(server_config)
    
    server_app.exec_()