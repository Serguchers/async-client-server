import sys
import os

from PyQt5.QtWidgets import QMainWindow, qApp, QMessageBox, QApplication, QListView
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QBrush, QColor
from PyQt5.QtCore import pyqtSlot, QEvent, Qt
from client_ui.main_client_window import Ui_UI_Client
from clientstorage import ClientDatabase

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
        
        self.known_users_update()
        self.show()
      
    def known_users_update(self):
        known_users = self.database.get_contacts()
        self.contact_model = QStandardItemModel()
        for i in known_users:
            item = QStandardItem(i)
            item.setEditable(False)
            self.contact_model.appendRow(item)
        self.ui.chats_list.setModel(self.contact_model)
      
suppress_qt_warnings()  
main_window = ClientMainWindow('Sergei')
client_app.exec_()