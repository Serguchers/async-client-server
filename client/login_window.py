import sys

from PyQt5.QtWidgets import QApplication, QCheckBox, QFormLayout, QLineEdit, QVBoxLayout, QWidget, QDialog
from client_ui.login_window import UI_Login_form

class Window(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = UI_Login_form()
        self.ui.setupUi(self)
    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())