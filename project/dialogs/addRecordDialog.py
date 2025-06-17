from PySide6.QtWidgets import QMainWindow, QHeaderView, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QLineEdit, QPushButton, QTabWidget, QDateEdit, QLabel, QComboBox, QCalendarWidget, QListWidget, QGroupBox, QTableView, QFileDialog, QMessageBox, QListWidgetItem, QTableWidgetItem, QDialog, QFormLayout
from styles.styles import STYLESHEET
from utils.database import get_session
from dialogs.add_event_dialog import AddEventDialog
from dialogs.event_details_dialog import EventDetailsDialog
from db import User, Event, Institution, EventFormat, EventClassification, ActivityDirection, Attendance, EventType, TargetAudience, Venue, Role, Decoding
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import func

class AddRecordDialog(QDialog):
    def __init__(self, parent=None, table_name=None, session=None, record=None):
        super().__init__(parent)
        self.setWindowTitle(f"{'Редактировать' if record else 'Добавить'} запись: {table_name}")
        self.table_name = table_name
        self.session = session
        self.record = record
        self.setup_ui()
        self.setStyleSheet(STYLESHEET)

    def setup_ui(self):
        self.layout = QFormLayout(self)
        self.fields = {}

        if self.table_name == "Расшифровка":
            self.fields['full_name'] = QLineEdit(self.record.full_name if self.record else "")
            self.fields['short_name'] = QLineEdit(self.record.short_name if self.record else "")
            self.layout.addRow("Полное название", self.fields['full_name'])
            self.layout.addRow("Краткое название", self.fields['short_name'])
        elif self.table_name == "Учреждение":
            self.fields['name'] = QLineEdit(self.record.name if self.record else "")
            self.fields['decoding_id'] = QComboBox()
            self.fields['user_id'] = QComboBox()
            decodings = self.session.query(Decoding).all()
            decoding_names = [d.full_name for d in decodings]
            self.fields['decoding_id'].addItems(decoding_names)
            users = self.session.query(User).all()
            user_names = [u.username for u in users]
            self.fields['user_id'].addItems(user_names)
            if self.record:
                decoding = self.session.query(Decoding).filter(Decoding.id == self.record.decoding_id).first()
                user = self.session.query(User).filter(User.id == self.record.user_id).first()
                if decoding:
                    self.fields['decoding_id'].setCurrentText(decoding.full_name)
                if user:
                    self.fields['user_id'].setCurrentText(user.username)
            self.layout.addRow("Название", self.fields['name'])
            self.layout.addRow("Расшифровка", self.fields['decoding_id'])
            self.layout.addRow("Пользователь", self.fields['user_id'])
        elif self.table_name == "Пользователь":
            self.fields['username'] = QLineEdit(self.record.username if self.record else "")
            self.fields['password'] = QLineEdit()
            self.fields['password'].setEchoMode(QLineEdit.Password)
            self.fields['password'].setPlaceholderText("Оставьте пустым, чтобы не менять пароль" if self.record else "")
            self.fields['role_id'] = QComboBox()
            roles = self.session.query(Role).all()
            role_names = [r.name for r in roles]
            self.fields['role_id'].addItems(role_names)
            if self.record:
                role = self.session.query(Role).filter(Role.id == self.record.role_id).first()
                if role:
                    self.fields['role_id'].setCurrentText(role.name)
            self.layout.addRow("Имя пользователя", self.fields['username'])
            self.layout.addRow("Пароль", self.fields['password'])
            self.layout.addRow("Роль", self.fields['role_id'])
        else:
            self.fields['name'] = QLineEdit(self.record.name if self.record else "")
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
                if self.record:
                    self.record.full_name = self.fields['full_name'].text().strip()
                    self.record.short_name = self.fields['short_name'].text().strip()
                else:
                    new_record = Decoding(
                        full_name=self.fields['full_name'].text().strip(),
                        short_name=self.fields['short_name'].text().strip()
                    )
                    self.session.add(new_record)
            elif self.table_name == "Учреждение":
                if not self.fields['name'].text().strip():
                    QMessageBox.warning(self, "Ошибка", "Название учреждения не может быть пустым")
                    return
                decoding_index = self.fields['decoding_id'].currentIndex()
                user_index = self.fields['user_id'].currentIndex()
                decodings = self.session.query(Decoding).all()
                users = self.session.query(User).all()
                if not decodings or not users:
                    QMessageBox.warning(self, "Ошибка", "Нет доступных расшифровок или пользователей")
                    return
                if self.record:
                    self.record.name = self.fields['name'].text().strip()
                    self.record.decoding_id = decodings[decoding_index].id
                    self.record.user_id = users[user_index].id
                else:
                    new_record = Institution(
                        name=self.fields['name'].text().strip(),
                        decoding_id=decodings[decoding_index].id,
                        user_id=users[user_index].id
                    )
                    self.session.add(new_record)
            elif self.table_name == "Пользователь":
                if not self.fields['username'].text().strip():
                    QMessageBox.warning(self, "Ошибка", "Имя пользователя не может быть пустым")
                    return
                role_index = self.fields['role_id'].currentIndex()
                roles = self.session.query(Role).all()
                if not roles:
                    QMessageBox.warning(self, "Ошибка", "Нет доступных ролей")
                    return
                if self.record:
                    self.record.username = self.fields['username'].text().strip()
                    if self.fields['password'].text().strip():
                        self.record.password = func.crypt(self.fields['password'].text().strip(), func.gen_salt('bf'))
                    self.record.role_id = roles[role_index].id
                else:
                    if not self.fields['password'].text().strip():
                        QMessageBox.warning(self, "Ошибка", "Пароль не может быть пустым при создании")
                        return
                    new_record = User(
                        username=self.fields['username'].text().strip(),
                        password=func.crypt(self.fields['password'].text().strip(), func.gen_salt('bf')),
                        role_id=roles[role_index].id
                    )
                    self.session.add(new_record)
            else:
                if not self.fields['name'].text().strip():
                    QMessageBox.warning(self, "Ошибка", "Название не может быть пустым")
                    return
                model_class = {
                    "Роль": Role,
                    "Форматы": EventFormat,
                    "Классификации": EventClassification,
                    "Направления": ActivityDirection,
                    "Типы мероприятий": EventType,
                    "Аудитории": TargetAudience,
                    "Места проведения": Venue
                }.get(self.table_name)
                if self.record:
                    self.record.name = self.fields['name'].text().strip()
                else:
                    new_record = model_class(name=self.fields['name'].text().strip())
                    self.session.add(new_record)

            self.session.commit()
            QMessageBox.information(self, "Успех", f"Запись {'обновлена' if self.record else 'добавлена'}")
            self.accept()
        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить запись: {str(e)}")