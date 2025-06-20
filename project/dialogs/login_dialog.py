from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import Qt
from utils.database import get_session
from db import User
from styles.styles import STYLESHEET
import requests
from io import BytesIO
from sqlalchemy.sql import func

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Вход в систему")
        self.user_id = None 
        self.setup_ui()
        self.setStyleSheet(STYLESHEET)
        self.setMinimumSize(300, 300)
        self.setWindowIcon(QIcon("./svg/logo.svg"))

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        title_label = QLabel("Вход в систему")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; margin: 20px 0;")
        main_layout.addWidget(title_label)

        form_layout = QVBoxLayout()

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Имя пользователя")
        self.username_input.setStyleSheet("padding: 10px; font-size: 14px; border-radius: 5px;")
        form_layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Пароль")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet("padding: 10px; font-size: 14px; border-radius: 5px; margin-top: 10px;")
        form_layout.addWidget(self.password_input)

        main_layout.addLayout(form_layout)

        self.login_button = QPushButton("Войти")
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px;
                font-size: 16px;
                border-radius: 5px;
                margin-top: 20px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.login_button.clicked.connect(self.login)
        main_layout.addWidget(self.login_button)

        main_layout.addStretch()

    def login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, заполните все поля")
            return

        with get_session() as session:
            try:
                user = session.query(User).filter(
                    User.username == username,
                    func.crypt(password, User.password) == User.password
                ).first()

                if user:
                    self.user_id = user.id 
                    self.accept() 
                else:
                    QMessageBox.critical(self, "Ошибка", "Неверное имя пользователя или пароль")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Произошла ошибка: {str(e)}")