from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QComboBox, QPushButton, QHBoxLayout, QMessageBox
from styles.styles import STYLESHEET
from db import Decoding, Institution, User, Role, EventFormat, EventClassification, ActivityDirection, EventType, TargetAudience, Venue
from sqlalchemy.sql import func

class EditRecordDialog(QDialog):
    def __init__(self, parent=None, table_name=None, record=None, session=None):
        super().__init__(parent)
        self.setWindowTitle(f"Редактировать запись: {table_name}")
        self.setFixedSize(400, 300)
        self.table_name = table_name
        self.record = record
        self.session = session
        self.setup_ui()
        self.setStyleSheet(STYLESHEET)

    def setup_ui(self):
        self.layout = QFormLayout(self)
        self.fields = {}

        if self.table_name == "Расшифровка":
            self.fields['full_name'] = QLineEdit(self.record.full_name or "")
            self.fields['short_name'] = QLineEdit(self.record.short_name or "")
            self.layout.addRow("Полное название", self.fields['full_name'])
            self.layout.addRow("Краткое название", self.fields['short_name'])
        elif self.table_name == "Учреждение":
            self.fields['name'] = QLineEdit(self.record.name or "")
            self.fields['decoding_id'] = QComboBox()
            decodings = self.session.query(Decoding).all()
            self.fields['decoding_id'].addItems([d.full_name for d in decodings])
            self.fields['decoding_id'].setCurrentText(self.record.decoding.full_name if self.record.decoding else "")
            self.fields['user_id'] = QComboBox()
            users = self.session.query(User).all()
            self.fields['user_id'].addItems([u.username for u in users])
            self.fields['user_id'].setCurrentText(self.record.user.username if self.record.user else "")
            self.layout.addRow("Название", self.fields['name'])
            self.layout.addRow("Расшифровка", self.fields['decoding_id'])
            self.layout.addRow("Пользователь", self.fields['user_id'])
        elif self.table_name == "Пользователь":
            self.fields['username'] = QLineEdit(self.record.username or "")
            self.fields['password'] = QLineEdit()
            self.fields['password'].setEchoMode(QLineEdit.Password)
            self.fields['password'].setPlaceholderText("Оставьте пустым, чтобы не менять")
            self.fields['role_id'] = QComboBox()
            roles = self.session.query(Role).all()
            self.fields['role_id'].addItems([r.name for r in roles])
            self.fields['role_id'].setCurrentText(self.record.role.name if self.record.role else "")
            self.layout.addRow("Имя пользователя", self.fields['username'])
            self.layout.addRow("Новый пароль", self.fields['password'])
            self.layout.addRow("Роль", self.fields['role_id'])
        else:
            self.fields['name'] = QLineEdit(self.record.name or "")
            self.layout.addRow("Название", self.fields['name'])

        buttons = QHBoxLayout()
        save = QPushButton("Сохранить")
        cancel = QPushButton("Отмена")
        save.clicked.connect(self.save_changes)
        cancel.clicked.connect(self.reject)
        buttons.addWidget(save)
        buttons.addWidget(cancel)
        self.layout.addRow(buttons)

    def save_changes(self):
        try:
            if self.table_name == "Расшифровка":
                if not self.fields['full_name'].text().strip() or not self.fields['short_name'].text().strip():
                    QMessageBox.warning(self, "Ошибка", "Все поля должны быть заполнены")
                    return
                self.record.full_name = self.fields['full_name'].text().strip()
                self.record.short_name = self.fields['short_name'].text().strip()
            elif self.table_name == "Учреждение":
                if not self.fields['name'].text().strip():
                    QMessageBox.warning(self, "Ошибка", "Название учреждения не может быть пустым")
                    return
                self.record.name = self.fields['name'].text().strip()
                decoding_index = self.fields['decoding_id'].currentIndex()
                user_index = self.fields['user_id'].currentIndex()
                decodings = self.session.query(Decoding).all()
                users = self.session.query(User).all()
                self.record.decoding_id = decodings[decoding_index].id
                self.record.user_id = users[user_index].id
            elif self.table_name == "Пользователь":
                if not self.fields['username'].text().strip():
                    QMessageBox.warning(self, "Ошибка", "Имя пользователя не может быть пустым")
                    return
                self.record.username = self.fields['username'].text().strip()
                password = self.fields['password'].text().strip()
                if password:
                    self.record.password = func.crypt(password, func.gen_salt('bf'))
                role_index = self.fields['role_id'].currentIndex()
                roles = self.session.query(Role).all()
                self.record.role_id = roles[role_index].id
            else:
                if not self.fields['name'].text().strip():
                    QMessageBox.warning(self, "Ошибка", "Название не может быть пустым")
                    return
                self.record.name = self.fields['name'].text().strip()

            QMessageBox.information(self, "Успех", "Запись обновлена")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось обновить запись: {str(e)}")