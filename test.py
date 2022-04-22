import sys
import os
import logging

from PyQt5.QtWidgets import QMainWindow, qApp, QMessageBox, QApplication, QListView
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QBrush, QColor, QFont
from PyQt5.QtCore import pyqtSlot, QEvent, Qt
from client_ui.main_client_window import Ui_UI_Client
from clientstorage import ClientDatabase
from log import client_log_config

log_client = logging.getLogger('client_logger')


client_app = QApplication(sys.argv)

def suppress_qt_warnings():
    os.environ["QT_DEVICE_PIXEL_RATIO"] = "0"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    os.environ["QT_SCREEN_SCALE_FACTORS"] = "1"
    os.environ["QT_SCALE_FACTOR"] = "1"

class ClientMainWindow(QMainWindow):
    def __init__(self, database, transport=None):
        super().__init__()
        
        self.database = ClientDatabase(database)
        self.transport = transport
        
        self.ui = Ui_UI_Client()
        self.ui.setupUi(self)
        
        # Exit button
        self.ui.action.triggered.connect(qApp.exit)
        
        # Select chat
        self.ui.chats_list.doubleClicked.connect(self.select_chat)
        
        # Message history model
        self.message_history_model = QStandardItemModel()
        self.ui.chat_history.setModel(self.message_history_model)
        
        # Variables
        self.current_chat = None
        
        
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
        
        message_list = sorted(self.database.get_message_history(self.current_chat), key=lambda item: item[2])
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
        known_users = self.database.get_known_users()
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
      
suppress_qt_warnings()  
main_window = ClientMainWindow('Sergei')
client_app.exec_()