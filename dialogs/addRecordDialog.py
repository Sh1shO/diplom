from PySide6.QtWidgets import QMainWindow, QHeaderView, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QLineEdit, QPushButton, QTabWidget, QDateEdit, QLabel, QComboBox, QCalendarWidget, QListWidget, QGroupBox, QTableView, QFileDialog, QMessageBox, QListWidgetItem, QTableWidgetItem, QDialog, QFormLayout
from PySide6.QtCore import QDate, Qt, QTimer
from PySide6.QtGui import QIcon, QPixmap, QTextCharFormat, QColor, QStandardItemModel, QStandardItem
from styles.styles import STYLESHEET
from utils.database import get_session
from dialogs.add_event_dialog import AddEventDialog
from dialogs.event_details_dialog import EventDetailsDialog
from db import User, Event, Institution, EventFormat, EventClassification, ActivityDirection, Attendance, EventType, TargetAudience, Venue, Role, Decoding
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import func
import requests
from io import BytesIO
from datetime import datetime, timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm

# Новый класс для диалога добавления записей
class AddRecordDialog(QDialog):
    def __init__(self, parent=None, table_name=None, session=None):
        super().__init__(parent)
        self.setWindowTitle(f"Добавить запись: {table_name}")
        self.setFixedSize(400, 300)
        self.table_name = table_name
        self.session = session
        self.setup_ui()
        self.setStyleSheet(STYLESHEET)

    def setup_ui(self):
        self.layout = QFormLayout(self)
        self.fields = {}

        if self.table_name == "Расшифровка":
            self.fields['full_name'] = QLineEdit()
            self.fields['short_name'] = QLineEdit()
            self.layout.addRow("Полное название", self.fields['full_name'])
            self.layout.addRow("Краткое название", self.fields['short_name'])
        elif self.table_name == "Учреждение":
            self.fields['name'] = QLineEdit()
            self.fields['decoding_id'] = QComboBox()
            decodings = self.session.query(Decoding).all()
            self.fields['decoding_id'].addItems([d.full_name for d in decodings])
            self.fields['user_id'] = QComboBox()
            users = self.session.query(User).all()
            self.fields['user_id'].addItems([u.username for u in users])
            self.layout.addRow("Название", self.fields['name'])
            self.layout.addRow("Расшифровка", self.fields['decoding_id'])
            self.layout.addRow("Пользователь", self.fields['user_id'])
        elif self.table_name == "Пользователь":
            self.fields['username'] = QLineEdit()
            self.fields['password'] = QLineEdit()
            self.fields['password'].setEchoMode(QLineEdit.Password)
            self.fields['role_id'] = QComboBox()
            roles = self.session.query(Role).all()
            self.fields['role_id'].addItems([r.name for r in roles])
            self.layout.addRow("Имя пользователя", self.fields['username'])
            self.layout.addRow("Пароль", self.fields['password'])
            self.layout.addRow("Роль", self.fields['role_id'])
        else:
            self.fields['name'] = QLineEdit()
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
                new_record = Institution(
                    name=self.fields['name'].text().strip(),
                    decoding_id=decodings[decoding_index].id,
                    user_id=users[user_index].id
                )
                self.session.add(new_record)
            elif self.table_name == "Пользователь":
                if not self.fields['username'].text().strip() or not self.fields['password'].text().strip():
                    QMessageBox.warning(self, "Ошибка", "Имя пользователя и пароль не могут быть пустыми")
                    return
                role_index = self.fields['role_id'].currentIndex()
                roles = self.session.query(Role).all()
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
                new_record = model_class(name=self.fields['name'].text().strip())
                self.session.add(new_record)

            self.session.commit()
            QMessageBox.information(self, "Успех", "Запись добавлена")
            self.accept()
        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить запись: {str(e)}")