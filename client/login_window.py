import sys

from PyQt5.QtWidgets import QApplication, QCheckBox, QFormLayout, QLineEdit, QVBoxLayout, QWidget, QDialog
from PyQt5.QtCore import pyqtSlot, QEvent, Qt, QObject, pyqtSignal
from client_ui.login_window import UI_Login_form

class Window(QDialog):
    logged_in = pyqtSignal()
    
    def __init__(self, client):
        super().__init__()
        self.ui = UI_Login_form()
        self.ui.setupUi(self)
        
        self.client = client
        
        self.ui.login_btn.clicked.connect(self.login)
        self.ui.singup_btn.clicked.connect(self.register)
        
        client.new_message.connect(self.message)
        self.show()
        
    def login(self):
        self.client.log_in(self.ui.password.displayText())
    
    def register(self):
        self.client.sign_up(self.ui.password.displayText())
    
    @pyqtSlot(dict)
    def message(self, message):
        if message['action'] == 'sign up':
            if message['status'] == 'success':
                print('Успешная регистрация')
            else:
                print('Такой пользователь уже существует')
        elif message['action'] == 'log in':
            if message['status'] == 'success':
                print('Успешный вход')
                self.logged_in.emit()
            else:
                print('Вход не удался')

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())