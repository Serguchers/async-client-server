import sys
import os
sys.path.append(os.getcwd())
sys.path.append(os.path.dirname(__file__))

import logging
import argparse

from common.variables import *
from PyQt5.QtWidgets import QMainWindow, qApp, QMessageBox, QApplication, QListView
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QBrush, QColor, QFont
from PyQt5.QtCore import pyqtSlot, QEvent, Qt, QObject, pyqtSignal
from client_ui.main_client_window import Ui_UI_Client
from threading import Thread, Lock
import socket
from common.utils import *
from time import time
from log import client_log_config
from client.client import Client
from client.clientstorage import ClientDatabase

log_client = logging.getLogger('client_logger')


client_app = QApplication(sys.argv)




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