import sys
from client_ui.main_client_window import Ui_UI_Client
from PyQt5.QtWidgets import QApplication, QMainWindow

client_app = QApplication(sys.argv)

class ClientMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_UI_Client()
        self.ui.setupUi(self)
        self.show()
        
main_window = ClientMainWindow()
client_app.exec_()