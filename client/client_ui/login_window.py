# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\context_menu_contact.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class UI_Login_form(object):
    def setupUi(self, Form):
        Form.setObjectName("Log in")
        Form.resize(273, 155)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Form.sizePolicy().hasHeightForWidth())
        Form.setSizePolicy(sizePolicy)
        self.verticalLayoutWidget = QtWidgets.QWidget(Form)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(10, 10, 251, 141))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.outer_layout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.outer_layout.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.outer_layout.setContentsMargins(0, 0, 0, 0)
        self.outer_layout.setObjectName("outer_layout")
        Form.setLayout(self.outer_layout)
        self.vertical_inner = QtWidgets.QVBoxLayout()
        self.vertical_inner.setObjectName("vertical_inner")
        self.username = QtWidgets.QLineEdit(self.verticalLayoutWidget)
        self.username.setText("")
        self.username.setObjectName("username")
        self.vertical_inner.addWidget(self.username)
        self.outer_layout.addLayout(self.vertical_inner)
        self.password = QtWidgets.QLineEdit(self.verticalLayoutWidget)
        self.password.setObjectName("password")
        self.vertical_inner.addWidget(self.password)
        self.horizontal_inner = QtWidgets.QHBoxLayout()
        self.horizontal_inner.setContentsMargins(-1, 0, -1, -1)
        self.horizontal_inner.setSpacing(3)
        self.horizontal_inner.setObjectName("horizontal_inner")
        self.login_btn = QtWidgets.QPushButton(self.verticalLayoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.login_btn.sizePolicy().hasHeightForWidth())
        self.login_btn.setSizePolicy(sizePolicy)
        self.login_btn.setObjectName("login_btn")
        self.horizontal_inner.addWidget(self.login_btn)
        self.singup_btn = QtWidgets.QPushButton(self.verticalLayoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.singup_btn.sizePolicy().hasHeightForWidth())
        self.singup_btn.setSizePolicy(sizePolicy)
        self.singup_btn.setObjectName("singup_btn")
        self.horizontal_inner.addWidget(self.singup_btn)
        self.outer_layout.addLayout(self.horizontal_inner)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.username.setPlaceholderText(_translate("Form", "Username"))
        self.password.setPlaceholderText(_translate("Form", "Password"))
        self.login_btn.setText(_translate("Form", "Login"))
        self.singup_btn.setText(_translate("Form", "Sign up"))
