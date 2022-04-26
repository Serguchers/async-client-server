import sys

from PyQt5.QtWidgets import QApplication, QCheckBox, QFormLayout, QLineEdit, QVBoxLayout, QWidget, QDialog, QMessageBox
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
        self.message_box = QMessageBox()
        
        self.show()
        
    def login(self):
        self.client.log_in(self.ui.username.displayText() ,self.ui.password.displayText())
    
    def register(self):
        self.client.sign_up(self.ui.username.displayText() ,self.ui.password.displayText())
    
    @pyqtSlot(dict)
    def message(self, message):
        if message['action'] == 'sign up':
            if message['status'] == 'success':
                self.show_ok_box('Успешная регистрация')
                self.message_box.show()
            else:
                self.show_error_box('Такой пользователь уже существует!')
                self.message_box.show()
                print('Ошибочка')
        elif message['action'] == 'log in':
            if message['status'] == 'success':
                self.client.success_login(message['destination'])
                self.logged_in.emit()
            else:
                self.show_error_box('Неверный логин или пароль!')
                self.message_box.show()

    def show_error_box(self, text):
        self.message_box.setIcon(QMessageBox.Critical)
        self.message_box.setText(text)
        self.message_box.setStandardButtons(QMessageBox.Ok)
    
    def show_ok_box(self, text):
        self.message_box.setText(text)
        self.message_box.setStandardButtons(QMessageBox.Ok)
    
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())