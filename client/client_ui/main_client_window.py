# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\form.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class UI_Client(object):
    def setupUi(self, UI_Client):
        UI_Client.setObjectName("Messenger")
        UI_Client.resize(906, 642)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(UI_Client.sizePolicy().hasHeightForWidth())
        UI_Client.setSizePolicy(sizePolicy)
        UI_Client.setAutoFillBackground(True)
        UI_Client.setStyleSheet("background-color: rgb(200, 228, 234)")
        UI_Client.setDocumentMode(False)
        UI_Client.setUnifiedTitleAndToolBarOnMac(False)
        self.centralwidget = QtWidgets.QWidget(UI_Client)
        self.centralwidget.setObjectName("centralwidget")
        self.chat_history = QtWidgets.QListView(self.centralwidget)
        self.chat_history.setGeometry(QtCore.QRect(0, 0, 661, 561))
        self.chat_history.setStyleSheet("background-color: rgb(237, 246, 248)")
        self.chat_history.setObjectName("chat_history")
        self.chats_list = QtWidgets.QListView(self.centralwidget)
        self.chats_list.setGeometry(QtCore.QRect(660, 0, 251, 561))
        self.chats_list.setStyleSheet("background-color: rgb(237, 246, 248)")
        self.chats_list.setObjectName("chats_list")
        self.msg_area = QtWidgets.QTextEdit(self.centralwidget)
        self.msg_area.setGeometry(QtCore.QRect(0, 560, 591, 41))
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(11)
        self.msg_area.setFont(font)
        self.msg_area.setStyleSheet("background-color: rgb(255,255,255)")
        self.msg_area.setObjectName("msg_area")
        self.send_msg = QtWidgets.QPushButton(self.centralwidget)
        self.send_msg.setGeometry(QtCore.QRect(590, 560, 71, 41))
        self.send_msg.setObjectName("send_msg")
        self.send_msg.setStyleSheet("border-width: 1px;\n"
"border-style: solid;\n"
"border-color: grey;\n"
"background-color: rgb(255, 255, 255);")
        self.search_cont = QtWidgets.QLineEdit(self.centralwidget)
        self.search_cont.setGeometry(QtCore.QRect(660, 560, 251, 41))
        self.search_cont.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.search_cont.setObjectName("search_cont")
        UI_Client.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(UI_Client)
        self.menubar.setEnabled(True)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 905, 21))
        self.menubar.setStyleSheet("background-color: rgb(144, 200, 213)")
        self.menubar.setObjectName("menubar")
        self.main_menu = QtWidgets.QMenu(self.menubar)
        self.main_menu.setObjectName("main_menu")
        UI_Client.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(UI_Client)
        self.statusbar.setEnabled(True)
        self.statusbar.setObjectName("statusbar")
        UI_Client.setStatusBar(self.statusbar)
        self.action = QtWidgets.QAction(UI_Client)
        self.action.setObjectName("action")
        self.main_menu.addAction(self.action)
        self.menubar.addAction(self.main_menu.menuAction())

        self.retranslateUi(UI_Client)
        QtCore.QMetaObject.connectSlotsByName(UI_Client)

    def retranslateUi(self, UI_Client):
        _translate = QtCore.QCoreApplication.translate
        UI_Client.setWindowTitle(_translate("UI_Client", "Messenger"))
        self.msg_area.setPlaceholderText(
            _translate("UI_Client", "?????????????? ?????????????????? ?????? ????????????????...")
        )
        self.send_msg.setText(_translate("UI_Client", "??????????????????"))
        self.search_cont.setPlaceholderText(_translate("UI_Client", "??????????...."))
        self.main_menu.setTitle(_translate("UI_Client", "????????"))
        self.action.setText(_translate("UI_Client", "??????????"))
