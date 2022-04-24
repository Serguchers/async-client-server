from distutils.log import log
from msilib.schema import SelfReg
from re import I
import sys
import os
sys.path.append(os.getcwd())
sys.path.append(os.path.dirname(__file__))

import logging
import argparse

from common.variables import *
from PyQt5.QtWidgets import QMainWindow, qApp, QMessageBox, QApplication, QListView, QMenu, QAction, QTextEdit
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QBrush, QColor, QFont, QCursor
from PyQt5.QtCore import pyqtSlot, QEvent, Qt, QObject, pyqtSignal
from client_ui.main_client_window import UI_Client
from threading import Thread, Lock
from PyQt5 import QtCore
import socket
from common.utils import *
from time import time
from log import client_log_config
from clientstorage import ClientDatabase

log_client = logging.getLogger('client_logger')



class ClientMainWindow(QMainWindow):
    def __init__(self, client):
        super().__init__()
        
        self.client = client
        
        self.ui = UI_Client()
        self.ui.setupUi(self)
        self.contacts_switch_button = QAction('Контакты', self)
        self.ui.menubar.addAction(self.contacts_switch_button)
        
        # Exit button
        self.ui.action.triggered.connect(self.closeEvent)
        
        # Select chat
        self.ui.chats_list.doubleClicked.connect(self.select_chat)
        
        # Send message button
        self.ui.send_msg.clicked.connect(self.send_message)
        self.ui.msg_area.installEventFilter(self)
        
        # Search users
        self.ui.search_cont.installEventFilter(self)
        
        # Message history model
        self.message_history_model = QStandardItemModel()
        self.ui.chat_history.setModel(self.message_history_model)
    
        
        # Variables
        self.current_chat = None
        self.known_users = None
        self.contacts = None
        
        # Switch to contacts panel
        self.contacts_switch_button.triggered.connect(self.known_users_update)
        
        #Connection
        client.new_message.connect(self.message)
        
        self.ui.chats_list.installEventFilter(self)
        
        # Prevent exit by pressing X
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowTitleHint | QtCore.Qt.WindowMinimizeButtonHint)
        self.known_users_update()
        self.show()
    
    # Select chat
    def select_chat(self):
        self.current_chat = self.ui.chats_list.currentIndex().data()
        self.message_history_update()
        self.known_users_update(update_req=False)
    
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
            
        self.ui.chat_history.scrollToBottom()
        
    # List of users we are familiar with
    def known_users_update(self, update_req=True):
        self.known_users = self.client.database.get_known_users()
        self.contacts = self.client.database.get_contacts()
        self.contact_model = QStandardItemModel()

        for i in self.contacts:
            if i == self.current_chat:
                self.contact_list_item(i, bold=True, contact=True)
                continue
            self.contact_list_item(i, contact=True)
        for i in self.known_users:
            if i in self.contacts:
                continue
            else:
                if i == self.current_chat:
                    self.contact_list_item(i, bold=True)
                    continue
                self.contact_list_item(i)
    
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
    @pyqtSlot(dict)
    def message(self, message):
        log_client.info('Слот отработал')
        if message['action'] == 'msg':
            self.client.database.save_message_history(self.client.username, message["account_name"], message["message_text"])
            self.client.database.meet_user(message['account_name'])  
            self.known_users_update()
            
            for idx in range(self.ui.chats_list.model().rowCount()):
                if message['account_name'] == self.ui.chats_list.model().item(idx).text():
                    self.ui.chats_list.model().item(idx).setText(f'{self.ui.chats_list.model().item(idx).text()} *')
            
            if self.current_chat == message['account_name']:
                self.message_history_update()
            
            if self.current_chat == message['account_name']:
                self.message_history_update()
        if message['action'] == 'add_contact' and message['status'] == 'success':
            self.client.database.add_contact(message['contact'])
            self.client.database.meet_user(message['contact']) 
            
            self.known_users_update(update_req=False)
            
        if message['action'] == 'del_contact' and message['status'] == 'success':
            self.client.database.del_contact(message['contact'])
            
            self.known_users_update(update_req=False)
            
        if message['action'] == 'search':
            self.search_result(message['result'])
            
           
    # Send message - press Enter
    def eventFilter(self, obj: 'QObject', event: 'QEvent'):
        if event.type() == QEvent.KeyPress and obj is self.ui.msg_area:
            if event.key() == Qt.Key.Key_Return and self.ui.msg_area.hasFocus():
                self.send_message()
                
        if event.type() == QEvent.ContextMenu and self.ui.chats_list.currentIndex() \
            and obj.indexAt(event.pos()).isValid():
                global contact_context_menu
                contact_context_menu = QMenu(self)
                add_contact_action = QAction('Добавить в контакты', self)
                del_contact_action = QAction('Удалить из контактов', self)
                
                contact_context_menu.addAction(add_contact_action)
                contact_context_menu.addAction(del_contact_action)
                
                add_contact_action.triggered.connect(self.add_contact)
                del_contact_action.triggered.connect(self.del_contact)
                
                contact_context_menu.popup(event.globalPos())
        
        if event.type() == QEvent.KeyPress and obj is self.ui.search_cont and\
            self.ui.search_cont.displayText():
            if event.key() == Qt.Key.Key_Return and self.ui.search_cont.hasFocus():
                self.client.find_user(self.ui.search_cont.displayText())
                self.ui.search_cont.clear()
                     
        return super().eventFilter(obj, event)
    
    def add_contact(self):
        self.client.add_contact(self.ui.chats_list.currentIndex().data())
        
    def del_contact(self):
        self.client.del_contact(self.ui.chats_list.currentIndex().data())
    
    # List item creator
    def contact_list_item(self, item, bold=False, contact=False):
        item = QStandardItem(item)
        font = QFont('Segoe UI', 11)
        if contact:
            font.setItalic(True)
        font.setBold(bold)
        item.setFont(font)
        item.setEditable(False)
        self.contact_model.appendRow(item)
     
    # App close handler   
    def closeEvent(self, event):
        close = QMessageBox()
        close.setText('Вы хотите закрыть приложение?')
        close.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        close = close.exec()
        
        if close == QMessageBox.Yes:
            self.client.exit_message()
            print('message sent')
            qApp.exit()
        else:
            pass
        
    def search_result(self, result):
        self.contact_model.clear()
        for i in result:
            self.contact_list_item(i)