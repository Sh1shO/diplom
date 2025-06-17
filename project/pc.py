from PySide6.QtWidgets import QMainWindow, QHeaderView, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QLineEdit, QPushButton, QTabWidget, QDateEdit, QLabel, QComboBox, QCalendarWidget, QListWidget, QGroupBox, QTableView, QFileDialog, QMessageBox, QListWidgetItem, QTableWidgetItem, QDialog
from PySide6.QtCore import QDate, Qt, QTimer
from PySide6.QtGui import QIcon, QPixmap, QTextCharFormat, QColor, QStandardItemModel, QStandardItem
from styles.styles import STYLESHEET
from utils.database import get_session
from dialogs.add_event_dialog import AddEventDialog
from dialogs.addRecordDialog import AddRecordDialog
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

class MainWindow(QMainWindow):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        with get_session() as session:
            self.user = session.query(User).filter(User.id == user_id).first()
        self.setWindowTitle("ЦБС Абакана")
        self.setup_icon()
        self.setup_ui()
        self.setStyleSheet(STYLESHEET)
        QTimer.singleShot(100, self.show_events)
        self.showMaximized()
        self.setWindowIcon(QIcon("./svg/logo.svg"))

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.setup_table_tab()
        self.setup_calendar_tab()
        self.setup_admin_tab()
        self.setup_report_tab()

        main_layout.addWidget(self.tabs)

    def setup_table_tab(self):
        table_tab = QWidget()
        table_layout = QVBoxLayout(table_tab)

        top_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по названию")
        top_layout.addWidget(self.search_input)
        top_layout.addStretch()

        self.add_button = QPushButton("Добавить")
        self.add_button.setObjectName("admin_button")
        self.add_button.clicked.connect(self.add_event)
        self.delete_button = QPushButton("Удалить")
        self.delete_button.setObjectName("delete_button")
        self.delete_button.clicked.connect(self.delete_event)
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.add_button)
        button_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.addWidget(button_widget)

        table_layout.addLayout(top_layout)

        filters_group = QGroupBox("Фильтры")
        filters_layout = QHBoxLayout(filters_group)

        self.start_date_filter = QDateEdit()
        self.start_date_filter.setCalendarPopup(True)
        self.start_date_filter.setDate(QDate.currentDate().addMonths(-1))
        self.end_date_filter = QDateEdit()
        self.end_date_filter.setCalendarPopup(True)
        self.end_date_filter.setDate(QDate.currentDate())
        filters_layout.addWidget(QLabel("Дата с:"))
        filters_layout.addWidget(self.start_date_filter)
        filters_layout.addWidget(QLabel("по:"))
        filters_layout.addWidget(self.end_date_filter)

        self.institution_filter_table = QComboBox()
        with get_session() as session:
            institutions = session.query(Institution).all()
            self.institution_filter_table.addItem("Все учреждения")
            self.institution_filter_table.addItems([i.name for i in institutions])
        filters_layout.addWidget(QLabel("Учреждение:"))
        filters_layout.addWidget(self.institution_filter_table)

        self.direction_filter_table = QComboBox()
        with get_session() as session:
            directions = session.query(ActivityDirection).all()
            self.direction_filter_table.addItem("Все направления")
            self.direction_filter_table.addItems([d.name for d in directions])
        filters_layout.addWidget(QLabel("Направление:"))
        filters_layout.addWidget(self.direction_filter_table)

        self.audience_filter_table = QComboBox()
        with get_session() as session:
            audiences = session.query(TargetAudience).all()
            self.audience_filter_table.addItem("Все аудитории")
            self.audience_filter_table.addItems([a.name for a in audiences])
        filters_layout.addWidget(QLabel("Аудитория:"))
        filters_layout.addWidget(self.audience_filter_table)

        self.format_filter_table = QComboBox()
        with get_session() as session:
            formats = session.query(EventFormat).all()
            self.format_filter_table.addItem("Все форматы")
            self.format_filter_table.addItems([f.name for f in formats])
        filters_layout.addWidget(QLabel("Формат:"))
        filters_layout.addWidget(self.format_filter_table)

        self.event_type_filter_table = QComboBox()
        with get_session() as session:
            event_types = session.query(EventType).all()
            self.event_type_filter_table.addItem("Все формы")
            self.event_type_filter_table.addItems([et.name for et in event_types])
        filters_layout.addWidget(QLabel("Форма:"))
        filters_layout.addWidget(self.event_type_filter_table)

        table_layout.addWidget(filters_group)

        self.events_table = QTableWidget()
        self.events_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.events_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.events_table.setSelectionMode(QTableWidget.SingleSelection)
        self.events_table.doubleClicked.connect(self.show_event_details)
        self.events_table.setShowGrid(True)
        table_layout.addWidget(self.events_table)

        self.total_label = QLabel("ИТОГО: 0 мероприятий, 0 посетителей мероприятий")
        table_layout.addWidget(self.total_label)

        self.search_input.textChanged.connect(self.update_events_table)
        self.start_date_filter.dateChanged.connect(self.update_events_table)
        self.end_date_filter.dateChanged.connect(self.update_events_table)
        self.institution_filter_table.currentIndexChanged.connect(self.update_events_table)
        self.direction_filter_table.currentIndexChanged.connect(self.update_events_table)
        self.audience_filter_table.currentIndexChanged.connect(self.update_events_table)
        self.format_filter_table.currentIndexChanged.connect(self.update_events_table)
        self.event_type_filter_table.currentIndexChanged.connect(self.update_events_table)

        self.tabs.addTab(table_tab, "Список")

    def setup_calendar_tab(self):
        calendar_tab = QWidget()
        calendar_layout = QHBoxLayout(calendar_tab)

        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.clicked.connect(self.show_events_for_date)
        calendar_layout.addWidget(self.calendar, 1)

        self.events_list = QListWidget()
        self.events_list.doubleClicked.connect(self.show_event_details_from_list)
        calendar_layout.addWidget(self.events_list, 1)

        self.tabs.addTab(calendar_tab, "Календарь")

    def setup_admin_tab(self):
        with get_session() as session:
            user = session.query(User).options(joinedload(User.role)).filter(User.id == self.user_id).first()
            if user and user.role and user.role.name == "admin":
                admin_tab = QWidget()
                admin_layout = QVBoxLayout(admin_tab)

                admin_title = QLabel("Админ-панель")
                admin_title.setAlignment(Qt.AlignCenter)
                admin_layout.addWidget(admin_title)

                manage_group = QGroupBox("Управление справочниками")
                manage_layout = QVBoxLayout(manage_group)

                self.table_selector = QComboBox()
                self.table_selector.addItems([
                    "Расшифровка", "Учреждение", "Пользователь", "Роль",
                    "Форматы", "Классификации", "Направления",
                    "Типы мероприятий", "Аудитории", "Места проведения"
                ])
                self.table_selector.currentIndexChanged.connect(self.refresh_table)

                selector_layout = QHBoxLayout()
                selector_layout.addWidget(QLabel("Выберите справочник:"))
                selector_layout.addWidget(self.table_selector)
                self.add_record_button = QPushButton("Добавить")
                self.add_record_button.setObjectName("admin_button")
                self.add_record_button.clicked.connect(self.add_record)
                self.delete_record_button = QPushButton("Удалить")
                self.delete_record_button.setObjectName("delete_button")
                self.delete_record_button.clicked.connect(self.delete_record)
                selector_layout.addWidget(self.add_record_button)
                selector_layout.addWidget(self.delete_record_button)

                self.admin_table = QTableWidget()
                self.admin_table.setSelectionBehavior(QTableWidget.SelectRows)
                self.admin_table.setSelectionMode(QTableWidget.SingleSelection)
                self.admin_table.setShowGrid(True)
                self.admin_table.setEditTriggers(QTableWidget.NoEditTriggers)
                self.admin_table.doubleClicked.connect(self.edit_record)

                manage_layout.addLayout(selector_layout)
                manage_layout.addWidget(self.admin_table)

                admin_layout.addWidget(manage_group)
                admin_layout.addStretch()

                self.tabs.addTab(admin_tab, "Админ-панель")
                self.refresh_table()

    def setup_report_tab(self):
        report_tab = QWidget()
        report_layout = QHBoxLayout(report_tab)

        filters_widget = QWidget()
        filters_layout = QVBoxLayout(filters_widget)

        report_title = QLabel("Отчёты")
        report_title.setAlignment(Qt.AlignCenter)
        filters_layout.addWidget(report_title)

        filters_group = QGroupBox("Фильтры")
        filters_group_layout = QVBoxLayout(filters_group)
        filters_group_layout.setSpacing(5)

        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        start_date_layout = QHBoxLayout()
        start_date_layout.addWidget(QLabel("Дата с:"))
        start_date_layout.addWidget(self.start_date)
        filters_group_layout.addLayout(start_date_layout)

        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        end_date_layout = QHBoxLayout()
        end_date_layout.addWidget(QLabel("по:"))
        end_date_layout.addWidget(self.end_date)
        filters_group_layout.addLayout(end_date_layout)

        self.institution_filter = QComboBox()
        with get_session() as session:
            institutions = session.query(Institution).all()
            self.institution_filter.addItem("Все учреждения")
            self.institution_filter.addItems([i.name for i in institutions])
        institution_layout = QHBoxLayout()
        institution_layout.addWidget(QLabel("Учреждение:"))
        institution_layout.addWidget(self.institution_filter)
        filters_group_layout.addLayout(institution_layout)

        self.report_type = QComboBox()
        self.report_type.addItems([
            "Еженедельный отчёт по посещениям и массовой работе",
            "Ежемесячный отчёт по посещениям и массовой работе",
            "Ежеквартальный (ежемесячный)",
            "Цифровые показатели по массовой работе"
        ])
        report_type_layout = QHBoxLayout()
        report_type_layout.addWidget(QLabel("Тип отчёта:"))
        report_type_layout.addWidget(self.report_type)
        filters_group_layout.addLayout(report_type_layout)

        self.direction_filter = QComboBox()
        with get_session() as session:
            directions = session.query(ActivityDirection).all()
            self.direction_filter.addItem("Все направления")
            self.direction_filter.addItems([d.name for d in directions])
        direction_layout = QHBoxLayout()
        direction_layout.addWidget(QLabel("Направление:"))
        direction_layout.addWidget(self.direction_filter)
        filters_group_layout.addLayout(direction_layout)

        self.audience_filter = QComboBox()
        with get_session() as session:
            audiences = session.query(TargetAudience).all()
            self.audience_filter.addItem("Все аудитории")
            self.audience_filter.addItems([a.name for a in audiences])
        audience_layout = QHBoxLayout()
        audience_layout.addWidget(QLabel("Аудитория:"))
        audience_layout.addWidget(self.audience_filter)
        filters_group_layout.addLayout(audience_layout)

        self.format_filter = QComboBox()
        with get_session() as session:
            formats = session.query(EventFormat).all()
            self.format_filter.addItem("Все форматы")
            self.format_filter.addItems([f.name for f in formats])
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Формат:"))
        format_layout.addWidget(self.format_filter)
        filters_group_layout.addLayout(format_layout)

        self.event_type_filter = QComboBox()
        with get_session() as session:
            event_types = session.query(EventType).all()
            self.event_type_filter.addItem("Все формы")
            self.event_type_filter.addItems([et.name for et in event_types])
        event_type_layout = QHBoxLayout()
        event_type_layout.addWidget(QLabel("Форма мероприятия:"))
        event_type_layout.addWidget(self.event_type_filter)
        filters_group_layout.addLayout(event_type_layout)

        self.generate_report_button = QPushButton("Сформировать отчёт")
        self.generate_report_button.clicked.connect(self.generate_report)
        filters_group_layout.addWidget(self.generate_report_button)

        filters_layout.addWidget(filters_group)
        filters_layout.addStretch()

        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)

        preview_group = QGroupBox("Предварительный просмотр")
        preview_group_layout = QVBoxLayout(preview_group)

        self.report_preview = QTableView()
        self.report_preview.setShowGrid(True)
        self.report_preview.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.report_preview.setWordWrap(True)
        self.report_preview.setTextElideMode(Qt.ElideNone)
        preview_group_layout.addWidget(self.report_preview)

        self.save_report_button = QPushButton("Сохранить отчёт")
        self.save_report_button.setObjectName("save_report_button")
        self.save_report_button.clicked.connect(self.save_report)
        preview_group_layout.addWidget(self.save_report_button)

        preview_layout.addWidget(preview_group)

        report_layout.addWidget(filters_widget, 1)
        report_layout.addWidget(preview_widget, 3)

        self.tabs.addTab(report_tab, "Отчёты")

    def update_events_table(self):
        with get_session() as session:
            try:
                search_text = self.search_input.text().strip()
                start_date = self.start_date_filter.date().toPython()
                end_date = self.end_date_filter.date().toPython()
                institution_name = self.institution_filter_table.currentText()
                direction_name = self.direction_filter_table.currentText()
                audience_name = self.audience_filter_table.currentText()
                format_name = self.format_filter_table.currentText()
                event_type_name = self.event_type_filter_table.currentText()

                query = session.query(Event).filter(
                    Event.date >= start_date,
                    Event.date <= end_date
                )

                if search_text:
                    query = query.filter(Event.name.ilike(f"%{search_text}%"))
                if institution_name != "Все учреждения":
                    query = query.join(Institution, Event.organizer_id == Institution.id).filter(Institution.name == institution_name)
                if direction_name != "Все направления":
                    query = query.join(ActivityDirection, Event.direction_id == ActivityDirection.id).filter(ActivityDirection.name == direction_name)
                if audience_name != "Все аудитории":
                    query = query.join(TargetAudience, Event.target_audience_id == TargetAudience.id).filter(TargetAudience.name == audience_name)
                if format_name != "Все форматы":
                    query = query.join(EventFormat, Event.format_id == EventFormat.id).filter(EventFormat.name == format_name)
                if event_type_name != "Все формы":
                    query = query.join(EventType, Event.event_type_id == EventType.id).filter(EventType.name == event_type_name)

                events = query.all()

                self.events_table.setRowCount(len(events))
                self.events_table.setColumnCount(10)
                self.events_table.setHorizontalHeaderLabels([
                    "Название", "Дата", "Учреждение", "Формат",
                    "Классификация", "Направление", "Тип", "Форма мероприятия", "Аудитория", "Место"
                ])
                self.events_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

                total_attendees = 0
                for row, event in enumerate(events):
                    self.events_table.setItem(row, 0, QTableWidgetItem(event.name or ""))
                    self.events_table.setItem(row, 1, QTableWidgetItem(event.date.strftime("%d.%m.%Y")))
                    self.events_table.setItem(row, 2, QTableWidgetItem(event.organizer.name if event.organizer else ""))
                    self.events_table.setItem(row, 3, QTableWidgetItem(event.format.name if event.format else ""))
                    self.events_table.setItem(row, 4, QTableWidgetItem(event.classification.name if event.classification else ""))
                    self.events_table.setItem(row, 5, QTableWidgetItem(event.direction.name if event.direction else ""))
                    self.events_table.setItem(row, 6, QTableWidgetItem(event.event_type.name if event.event_type else ""))
                    self.events_table.setItem(row, 7, QTableWidgetItem(event.event_type.name if event.event_type else ""))
                    self.events_table.setItem(row, 8, QTableWidgetItem(event.target_audience.name if event.target_audience else ""))
                    self.events_table.setItem(row, 9, QTableWidgetItem(event.venue.name if event.venue else ""))
                    attendance = event.attendances[0] if event.attendances else None
                    if attendance and attendance.total_attendees is not None:
                        total_attendees += attendance.total_attendees

                self.total_label.setText(f"ИТОГО: {len(events)} мероприятий, {total_attendees} посетителей мероприятий")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось обновить таблицу мероприятий: {str(e)}")

    def add_event(self):
        with get_session() as session:
            try:
                institutions = session.query(Institution).all()
                formats = session.query(EventFormat).all()
                classifications = session.query(EventClassification).all()
                directions = session.query(ActivityDirection).all()
                event_types = session.query(EventType).all()
                audiences = session.query(TargetAudience).all()
                venues = session.query(Venue).all()

                missing_tables = []
                if not institutions:
                    missing_tables.append("Учреждения")
                if not formats:
                    missing_tables.append("Форматы")
                if not classifications:
                    missing_tables.append("Классификации")
                if not directions:
                    missing_tables.append("Направления")
                if not event_types:
                    missing_tables.append("Типы мероприятий")
                if not audiences:
                    missing_tables.append("Аудитории")
                if not venues:
                    missing_tables.append("Места проведения")

                if missing_tables:
                    QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные справочников. Отсутствуют записи в следующих таблицах: {', '.join(missing_tables)}.")
                    return

                dialog = AddEventDialog(self)
                dialog.set_data(institutions, formats, classifications, directions, event_types, audiences, venues)
                if dialog.exec():
                    data = dialog.get_data()

                    if not data["name"]:
                        QMessageBox.critical(self, "Ошибка", "Название мероприятия не может быть пустым")
                        return
                    total_attendees = int(data["total_attendees"]) if data["total_attendees"].isdigit() else 0
                    child_attendees = int(data["child_attendees"]) if data["child_attendees"].isdigit() else 0
                    volunteers = int(data["volunteers"]) if data["volunteers"].isdigit() else 0
                    at_risk_teens = int(data["at_risk_teens"]) if data["at_risk_teens"].isdigit() else 0

                    if total_attendees < 0 or child_attendees < 0 or volunteers < 0 or at_risk_teens < 0:
                        QMessageBox.critical(self, "Ошибка", "Числовые поля не могут быть отрицательными")
                        return
                    if child_attendees > total_attendees:
                        QMessageBox.critical(self, "Ошибка", "Количество детей не может превышать общее количество посетителей")
                        return
                    if not data["event_type_id"]:
                        QMessageBox.critical(self, "Ошибка", "Выберите форму мероприятия")
                        return

                    organizer = session.query(Institution).filter(Institution.id == data["organizer_id"]).first()
                    if not organizer:
                        QMessageBox.critical(self, "Ошибка", f"Учреждение с ID {data['organizer_id']} не найдено.")
                        return

                    new_event = Event(
                        name=data["name"],
                        date=data["date"],
                        description=data["description"],
                        organizer_id=data["organizer_id"],
                        format_id=data["format_id"],
                        classification_id=data["classification_id"],
                        direction_id=data["direction_id"],
                        event_type_id=data["event_type_id"],
                        target_audience_id=data["audience_id"],
                        venue_id=data["venue_id"]
                    )
                    session.add(new_event)
                    session.flush()

                    attendance = Attendance(
                        event_id=new_event.id,
                        institution_id=data["organizer_id"],
                        total_attendees=total_attendees,
                        child_attendees=child_attendees,
                        volunteers=volunteers,
                        at_risk_teens=at_risk_teens
                    )
                    session.add(attendance)
                    session.commit()

                    QMessageBox.information(self, "Успех", "Мероприятие добавлено")
                    self.update_events_table()
                    self.update_calendar()
                    self.show_events_for_date(self.calendar.selectedDate())
            except Exception as e:
                session.rollback()
                QMessageBox.critical(self, "Ошибка", f"Не удалось добавить мероприятие: {str(e)}")

    def show_event_details(self):
        selected_rows = self.events_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Предупреждение", "Выберите мероприятие для просмотра")
            return

        row = selected_rows[0].row()
        event_name = self.events_table.item(row, 0).text()
        with get_session() as session:
            try:
                event_data = session.query(Event).options(joinedload(Event.attendances)).filter(Event.name == event_name).first()
                if not event_data:
                    QMessageBox.warning(self, "Ошибка", "Мероприятие не найдено")
                    return

                institutions = session.query(Institution).all()
                formats = session.query(EventFormat).all()
                classifications = session.query(EventClassification).all()
                directions = session.query(ActivityDirection).all()
                event_types = session.query(EventType).all()
                audiences = session.query(TargetAudience).all()
                venues = session.query(Venue).all()

                if not all([institutions, formats, classifications, directions, event_types, audiences, venues]):
                    QMessageBox.critical(self, "Ошибка", "Не удалось загрузить данные справочников")
                    return

                dialog = EventDetailsDialog(self, event_data, institutions, formats, classifications, directions, event_types, audiences, venues)
                if dialog.exec():
                    data = dialog.get_data()

                    if not data["name"]:
                        QMessageBox.critical(self, "Ошибка", "Название мероприятия не может быть пустым")
                        return
                    total_attendees = int(data["total_attendees"]) if data["total_attendees"].isdigit() else 0
                    child_attendees = int(data["child_attendees"]) if data["child_attendees"].isdigit() else 0
                    volunteers = int(data["volunteers"]) if data["volunteers"].isdigit() else 0
                    at_risk_teens = int(data["at_risk_teens"]) if data["at_risk_teens"].isdigit() else 0

                    if total_attendees < 0 or child_attendees < 0 or volunteers < 0 or at_risk_teens < 0:
                        QMessageBox.critical(self, "Ошибка", "Числовые поля не могут быть отрицательными")
                        return
                    if child_attendees > total_attendees:
                        QMessageBox.critical(self, "Ошибка", "Количество детей не может превышать общее количество посетителей")
                        return
                    if not data["event_type_id"]:
                        QMessageBox.critical(self, "Ошибка", "Выберите форму мероприятия")
                        return

                    event_data.name = data["name"]
                    event_data.date = data["date"]
                    event_data.description = data["description"]
                    event_data.organizer_id = data["organizer_id"]
                    event_data.format_id = data["format_id"]
                    event_data.classification_id = data["classification_id"]
                    event_data.direction_id = data["direction_id"]
                    event_data.event_type_id = data["event_type_id"]
                    event_data.target_audience_id = data["audience_id"]
                    event_data.venue_id = data["venue_id"]

                    attendance = event_data.attendances[0] if event_data.attendances else None
                    if attendance:
                        attendance.total_attendees = total_attendees
                        attendance.child_attendees = child_attendees
                        attendance.volunteers = volunteers
                        attendance.at_risk_teens = at_risk_teens
                    else:
                        attendance = Attendance(
                            event_id=event_data.id,
                            institution_id=data["organizer_id"],
                            total_attendees=total_attendees,
                            child_attendees=child_attendees,
                            volunteers=volunteers,
                            at_risk_teens=at_risk_teens
                        )
                        session.add(attendance)

                    session.commit()
                    QMessageBox.information(self, "Успех", "Мероприятие обновлено")
                    self.update_events_table()
                    self.update_calendar()
                    self.show_events_for_date(self.calendar.selectedDate())
            except Exception as e:
                session.rollback()
                QMessageBox.critical(self, "Ошибка", f"Не удалось обновить мероприятие: {str(e)}")

    def show_event_details_from_list(self):
        selected_items = self.events_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Предупреждение", "Выберите мероприятие для просмотра")
            return

        event_id = selected_items[0].data(Qt.UserRole)
        with get_session() as session:
            try:
                event_data = session.query(Event).options(joinedload(Event.attendances)).filter(Event.id == event_id).first()
                if not event_data:
                    QMessageBox.warning(self, "Ошибка", "Мероприятие не найдено")
                    return

                institutions = session.query(Institution).all()
                formats = session.query(EventFormat).all()
                classifications = session.query(EventClassification).all()
                directions = session.query(ActivityDirection).all()
                event_types = session.query(EventType).all()
                audiences = session.query(TargetAudience).all()
                venues = session.query(Venue).all()

                if not all([institutions, formats, classifications, directions, event_types, audiences, venues]):
                    QMessageBox.critical(self, "Ошибка", "Не удалось загрузить данные справочников")
                    return

                dialog = EventDetailsDialog(self, event_data, institutions, formats, classifications, directions, event_types, audiences, venues)
                if dialog.exec():
                    data = dialog.get_data()

                    if not data["name"]:
                        QMessageBox.critical(self, "Ошибка", "Название мероприятия не может быть пустым")
                        return
                    total_attendees = int(data["total_attendees"]) if data["total_attendees"].isdigit() else 0
                    child_attendees = int(data["child_attendees"]) if data["child_attendees"].isdigit() else 0
                    volunteers = int(data["volunteers"]) if data["volunteers"].isdigit() else 0
                    at_risk_teens = int(data["at_risk_teens"]) if data["at_risk_teens"].isdigit() else 0

                    if total_attendees < 0 or child_attendees < 0 or volunteers < 0 or at_risk_teens < 0:
                        QMessageBox.critical(self, "Ошибка", "Числовые поля не могут быть отрицательными")
                        return
                    if child_attendees > total_attendees:
                        QMessageBox.critical(self, "Ошибка", "Количество детей не может превышать общее количество посетителей")
                        return
                    if not data["event_type_id"]:
                        QMessageBox.critical(self, "Ошибка", "Выберите форму мероприятия")
                        return

                    event_data.name = data["name"]
                    event_data.date = data["date"]
                    event_data.description = data["description"]
                    event_data.organizer_id = data["organizer_id"]
                    event_data.format_id = data["format_id"]
                    event_data.classification_id = data["classification_id"]
                    event_data.direction_id = data["direction_id"]
                    event_data.event_type_id = data["event_type_id"]
                    event_data.target_audience_id = data["audience_id"]
                    event_data.venue_id = data["venue_id"]

                    attendance = event_data.attendances[0] if event_data.attendances else None
                    if attendance:
                        attendance.total_attendees = total_attendees
                        attendance.child_attendees = child_attendees
                        attendance.volunteers = volunteers
                        attendance.at_risk_teens = at_risk_teens
                    else:
                        attendance = Attendance(
                            event_id=event_data.id,
                            institution_id=data["organizer_id"],
                            total_attendees=total_attendees,
                            child_attendees=child_attendees,
                            volunteers=volunteers,
                            at_risk_teens=at_risk_teens
                        )
                        session.add(attendance)

                    session.commit()
                    QMessageBox.information(self, "Успех", "Мероприятие обновлено")
                    self.update_events_table()
                    self.update_calendar()
                    self.show_events_for_date(self.calendar.selectedDate())
            except Exception as e:
                session.rollback()
                QMessageBox.critical(self, "Ошибка", f"Не удалось обновить мероприятие: {str(e)}")

    def delete_event(self):
        selected_rows = self.events_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Предупреждение", "Выберите мероприятие для удаления")
            return

        row = selected_rows[0].row()
        event_name = self.events_table.item(row, 0).text()
        reply = QMessageBox.question(self, "Подтверждение", "Вы уверены, что хотите удалить это мероприятие?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            with get_session() as session:
                try:
                    event = session.query(Event).filter(Event.name == event_name).first()
                    if event:
                        session.delete(event)
                        session.commit()
                        QMessageBox.information(self, "Успех", "Мероприятие удалено")
                        self.update_events_table()
                        self.update_calendar()
                        self.show_events_for_date(self.calendar.selectedDate())
                    else:
                        QMessageBox.warning(self, "Ошибка", "Мероприятие не найдено")
                except Exception as e:
                    session.rollback()
                    QMessageBox.critical(self, "Ошибка", f"Не удалось удалить мероприятие: {str(e)}")

    def show_events_for_date(self, date):
        self.events_list.clear()
        with get_session() as session:
            try:
                python_date = date.toPython()
                events = session.query(Event).filter(Event.date == python_date).all()
                for event in events:
                    item = QListWidgetItem(f"{event.name} ({event.organizer.name if event.organizer else 'Нет учреждения'})")
                    item.setData(Qt.UserRole, event.id)
                    self.events_list.addItem(item)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить мероприятия: {str(e)}")

    def update_calendar(self):
        with get_session() as session:
            try:
                events = session.query(Event).all()
                format = QTextCharFormat()
                format.setBackground(QColor("#DDEAFD"))
                for event in events:
                    date = QDate(event.date.year, event.date.month, event.date.day)
                    self.calendar.setDateTextFormat(date, format)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось обновить календарь: {str(e)}")

    def show_events(self):
        self.update_events_table()
        self.update_calendar()
        self.show_events_for_date(self.calendar.selectedDate())

    def generate_report(self):
        with get_session() as session:
            try:
                start_date = self.start_date.date().toPython()
                end_date = self.end_date.date().toPython()
                institution_name = self.institution_filter.currentText()
                report_type = self.report_type.currentText()
                direction_name = self.direction_filter.currentText()
                audience_name = self.audience_filter.currentText()
                format_name = self.format_filter.currentText()
                event_type_name = self.event_type_filter.currentText()

                query = session.query(Event).\
                    join(Institution, Event.organizer_id == Institution.id).\
                    join(EventFormat, Event.format_id == EventFormat.id).\
                    join(EventClassification, Event.classification_id == EventClassification.id).\
                    join(ActivityDirection, Event.direction_id == ActivityDirection.id).\
                    join(EventType, Event.event_type_id == EventType.id).\
                    join(TargetAudience, Event.target_audience_id == TargetAudience.id).\
                    join(Venue, Event.venue_id == Venue.id).\
                    outerjoin(Attendance, Event.id == Attendance.event_id).\
                    options(
                        joinedload(Event.organizer),
                        joinedload(Event.format),
                        joinedload(Event.classification),
                        joinedload(Event.direction),
                        joinedload(Event.event_type),
                        joinedload(Event.target_audience),
                        joinedload(Event.venue),
                        joinedload(Event.attendances)
                    ).\
                    filter(Event.date >= start_date, Event.date <= end_date)

                if institution_name != "Все учреждения":
                    query = query.filter(Institution.name == institution_name)
                if direction_name != "Все направления":
                    query = query.filter(ActivityDirection.name == direction_name)
                if audience_name != "Все аудитории":
                    query = query.filter(TargetAudience.name == audience_name)
                if format_name != "Все форматы":
                    query = query.filter(EventFormat.name == format_name)
                if event_type_name != "Все формы":
                    query = query.filter(EventType.name == event_type_name)

                events = query.all()

                events_data = [
                    {
                        "name": event.name,
                        "date": event.date,
                        "description": event.description
                    }
                    for event in events
                ]

                attendance_query = session.query(Attendance).\
                    join(Event, Attendance.event_id == Event.id).\
                    join(Institution, Event.organizer_id == Institution.id).\
                    join(EventFormat, Event.format_id == EventFormat.id).\
                    join(ActivityDirection, Event.direction_id == ActivityDirection.id).\
                    join(EventType, Event.event_type_id == EventType.id).\
                    join(TargetAudience, Event.target_audience_id == TargetAudience.id).\
                    filter(Event.date >= start_date, Event.date <= end_date)

                if institution_name != "Все учреждения":
                    attendance_query = attendance_query.filter(Institution.name == institution_name)
                if direction_name != "Все направления":
                    attendance_query = attendance_query.filter(ActivityDirection.name == direction_name)
                if audience_name != "Все аудитории":
                    attendance_query = attendance_query.filter(TargetAudience.name == audience_name)
                if format_name != "Все форматы":
                    attendance_query = attendance_query.filter(EventFormat.name == format_name)
                if event_type_name != "Все формы":
                    attendance_query = attendance_query.filter(EventType.name == event_type_name)

                attendances = attendance_query.all()

                if not events and not attendances:
                    QMessageBox.warning(self, "Предупреждение", "Нет данных для формирования отчёта за выбранный период.")
                    return

                if report_type == "Еженедельный отчёт по посещениям и массовой работе":
                    report_data = self.generate_weekly_by_cultural_events_report(events, attendances, start_date, end_date, institution_name, direction_name, audience_name, format_name, event_type_name)
                elif report_type == "Ежемесячный отчёт по посещениям и массовой работе":
                    report_data = self.generate_monthly_by_weeks_report(events, attendances, start_date, end_date, institution_name, direction_name, audience_name, format_name, event_type_name)
                elif report_type == "Ежеквартальный (ежемесячный)":
                    report_data = self.generate_quarterly_by_months_report(events, attendances, start_date, end_date, institution_name, direction_name, audience_name, format_name, event_type_name)
                elif report_type == "Цифровые показатели по массовой работе":
                    report_data = self.generate_digital_indicators_by_directions_report(events, attendances, start_date, end_date, institution_name, direction_name, audience_name, format_name, event_type_name)
                else:
                    QMessageBox.critical(self, "Ошибка", "Неизвестный тип отчёта.")
                    return

                report_data['events_data'] = events_data
                self.current_report_data = report_data
                self.display_report(report_data)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сформировать отчёт: {str(e)}")

    def save_report(self):
        if not hasattr(self, 'current_report_data') or not self.current_report_data['header']:
            QMessageBox.warning(self, "Предупреждение", "Отчёт пуст. Сначала сформируйте отчёт.")
            return

        file_name, _ = QFileDialog.getSaveFileName(
            self, "Сохранить отчёт", "", "PDF файлы (*.pdf)"
        )
        if file_name:
            try:
                if not file_name.endswith('.pdf'):
                    file_name += '.pdf'
                self.generate_pdf(self.current_report_data, file_name)
                QMessageBox.information(self, "Успех", f"Отчёт сохранён в {file_name}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить отчёт: {str(e)}")

    def generate_pdf(self, report_data, file_name):
        try:
            from reportlab.pdfbase.ttfonts import TTFont
            from reportlab.lib.fonts import addMapping
            pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
            addMapping('DejaVuSans', 0, 0, 'DejaVuSans')
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить шрифт DejaVuSans.ttf: {str(e)}\nСкачайте шрифт DejaVuSans.ttf и поместите его в директорию проекта.")
            return

        doc = SimpleDocTemplate(
            file_name,
            pagesize=landscape(A4),
            rightMargin=10*mm,
            leftMargin=10*mm,
            topMargin=10*mm,
            bottomMargin=10*mm
        )
        elements = []
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='HeaderStyle', fontName='DejaVuSans', fontSize=12, leading=14, alignment=1))
        styles.add(ParagraphStyle(name='TableStyle', fontName='DejaVuSans', fontSize=7, leading=8, alignment=0, wordWrap='CJK'))
        styles.add(ParagraphStyle(name='SectionHeader', fontName='DejaVuSans', fontSize=10, leading=12, alignment=0))
        styles.add(ParagraphStyle(name='EventText', fontName='DejaVuSans', fontSize=8, leading=10, alignment=0, spaceAfter=6))

        for line in report_data['header']:
            elements.append(Paragraph(line, styles['HeaderStyle']))
        elements.append(Spacer(1, 8*mm))

        table_data = report_data['table']
        if table_data:
            pdf_table_data = []
            for row in table_data:
                pdf_row = []
                for cell in row:
                    if isinstance(cell, (int, float)):
                        cell = str(int(cell)) if cell == int(cell) else str(cell)
                    elif cell is None or cell == '':
                        cell = '-'
                    pdf_row.append(Paragraph(str(cell), styles['TableStyle']))
                pdf_table_data.append(pdf_row)

            page_width = landscape(A4)[0] - 20*mm 
            col_count = len(table_data[0])
            col_widths = report_data.get('col_widths', None)
            if col_widths:
                col_widths = [min(w, page_width / col_count) * mm for w in col_widths]
                total_width = sum(col_widths)
                if total_width > page_width:
                    scale_factor = page_width / total_width
                    col_widths = [w * scale_factor for w in col_widths]
            else:
                col_widths = [page_width / col_count] * col_count

            table = Table(pdf_table_data, colWidths=col_widths, splitByRow=True, splitInRow=False)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.95, 0.95, 0.95)),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.Color(0.13, 0.13, 0.13)),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSans'),
                ('FONTSIZE', (0, 0), (-1, 0), 7),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('BACKGROUND', (0, -1), (-1, -1), colors.Color(0.9, 0.9, 0.9)),
                ('GRID', (0, 0), (-1, -1), 1, colors.Color(0.88, 0.88, 0.88)),
                ('BOX', (0, 0), (-1, -1), 1, colors.Color(0.88, 0.88, 0.88)),
                ('WORDWRAP', (0, 0), (-1, -1), 'CJK'),
            ]))
            elements.append(table)

        elements.append(Spacer(1, 15*mm))

        elements.append(Paragraph("Список мероприятий", styles['SectionHeader']))
        elements.append(Spacer(1, 5*mm))

        events_data = report_data.get('events_data', [])
        if events_data:
            for event_data in events_data:
                event_text = f"Название: {event_data['name'] or '-'}. "
                event_text += f"Дата: {event_data['date'].strftime('%d.%m.%Y') if event_data['date'] else '-'}. "
                event_text += f"Описание: {event_data['description'] or '-'}."
                elements.append(Paragraph(event_text, styles['EventText']))
        else:
            elements.append(Paragraph("Мероприятий за выбранный период не найдено.", styles['TableStyle']))

        doc.build(elements)

    def display_report(self, report_data):
        model = QStandardItemModel()
        table_data = report_data['table']
        headers = table_data[0]

        wrapped_headers = [str(header) for header in headers]
        
        model.setHorizontalHeaderLabels(wrapped_headers)
        
        for row in table_data[1:]:
            items = [QStandardItem(str(cell) if isinstance(cell, (int, float)) else cell or '-') for cell in row]
            model.appendRow(items)
        
        self.report_preview.setModel(model)
        
        header = self.report_preview.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setDefaultAlignment(Qt.AlignCenter | Qt.AlignVCenter)

        for i in range(len(wrapped_headers)):
            header.setMinimumSectionSize(100)
            header.resizeSection(i, 150)
        
        header.setDefaultSectionSize(100)
        
        self.report_preview.setWordWrap(True)
        self.report_preview.resizeRowsToContents()
        self.report_preview.verticalHeader().setDefaultSectionSize(50)

        self.report_preview.resizeColumnsToContents()

    def generate_weekly_by_cultural_events_report(self, events, attendances, start_date, end_date, institution_name, direction_name, audience_name, format_name, event_type_name):
            header = [
                "Еженедельный отчёт по посещениям и массовой работе",
                f"Период: {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}",
                f"Учреждение: {institution_name}",
                f"Направление: {direction_name}",
                f"Аудитория: {audience_name}",
                f"Формат: {format_name}",
                f"Форма мероприятия: {event_type_name}"
            ]

            table = [
                [
                    "Библиотека-филиал",
                    "Культурно-досуговые мероприятия",
                    "", "", "", "", "", "", "", "",
                    "Волонтёры культуры, чел.",
                    "Посещения",
                    "", "",
                    "Занятия клубов, чел."
                ],
                [
                    "",
                    "Всего", "Для детей", "Выездные", "Открытые площадки",
                    "Дворовые", "Экскурсии", "Мастер-классы", "Профилактические", "Онлайн",
                    "",
                    "Всего", "На мероприятиях", "Дети лагерей",
                    ""
                ]
            ]

            with get_session() as session:
                institutions = session.query(Institution).all()
                event_types = session.query(EventType).all()
                event_type_map = {et.name: et.id for et in event_types}

                institution_data = {inst.name: {
                    "total_events": 0,
                    "child_events": 0,
                    "offsite_events": 0,
                    "open_space_events": 0,
                    "yard_events": 0,
                    "excursion_events": 0,
                    "masterclass_events": 0,
                    "preventive_events": 0,
                    "online_events": 0,
                    "volunteers": 0,
                    "total_visits": 0,
                    "event_attendees": 0,
                    "child_camp_attendees": 0,
                    "club_info": "0/0/0"
                } for inst in institutions}

                for event in events:
                    inst_name = event.organizer.name if event.organizer else "Не указано"
                    if inst_name in institution_data:
                        institution_data[inst_name]["total_events"] += 1
                        if event.target_audience and event.target_audience.name == "Дети":
                            institution_data[inst_name]["child_events"] += 1
                        if event.event_type:
                            event_type_name = event.event_type.name
                            if event_type_name == "Выездное":
                                institution_data[inst_name]["offsite_events"] += 1
                            elif event_type_name == "На открытых площадках":
                                institution_data[inst_name]["open_space_events"] += 1
                            elif event_type_name == "Дворовое":
                                institution_data[inst_name]["yard_events"] += 1
                            elif event_type_name == "Экскурсия":
                                institution_data[inst_name]["excursion_events"] += 1
                            elif event_type_name == "Мастер-класс":
                                institution_data[inst_name]["masterclass_events"] += 1
                            elif event_type_name == "Профилактическое":
                                institution_data[inst_name]["preventive_events"] += 1
                            elif event_type_name == "Онлайн":
                                institution_data[inst_name]["online_events"] += 1

                for attendance in attendances:
                    inst_name = attendance.event.organizer.name if attendance.event.organizer else "Не указано"
                    if inst_name in institution_data:
                        institution_data[inst_name]["volunteers"] += attendance.volunteers or 0
                        institution_data[inst_name]["event_attendees"] += attendance.total_attendees or 0
                        institution_data[inst_name]["child_camp_attendees"] += attendance.child_attendees or 0
                        institution_data[inst_name]["total_visits"] += attendance.total_attendees or 0

                total_events = 0
                total_child_events = 0
                total_offsite_events = 0
                total_open_space_events = 0
                total_yard_events = 0
                total_excursion_events = 0
                total_masterclass_events = 0
                total_preventive_events = 0
                total_online_events = 0
                total_volunteers = 0
                total_visits = 0
                total_event_attendees = 0
                total_child_camp_attendees = 0

                for inst_name, data in institution_data.items():
                    table.append([
                        inst_name,
                        data["total_events"], data["child_events"], data["offsite_events"], data["open_space_events"],
                        data["yard_events"], data["excursion_events"], data["masterclass_events"], data["preventive_events"], data["online_events"],
                        data["volunteers"],
                        data["total_visits"], data["event_attendees"], data["child_camp_attendees"],
                        data["club_info"]
                    ])
                    total_events += data["total_events"]
                    total_child_events += data["child_events"]
                    total_offsite_events += data["offsite_events"]
                    total_open_space_events += data["open_space_events"]
                    total_yard_events += data["yard_events"]
                    total_excursion_events += data["excursion_events"]
                    total_masterclass_events += data["masterclass_events"]
                    total_preventive_events += data["preventive_events"]
                    total_online_events += data["online_events"]
                    total_volunteers += data["volunteers"]
                    total_visits += data["total_visits"]
                    total_event_attendees += data["event_attendees"]
                    total_child_camp_attendees += data["child_camp_attendees"]

                table.append([
                    "ИТОГО по ЦБС",
                    total_events, total_child_events, total_offsite_events, total_open_space_events,
                    total_yard_events, total_excursion_events, total_masterclass_events, total_preventive_events, total_online_events,
                    total_volunteers,
                    total_visits, total_event_attendees, total_child_camp_attendees,
                    "0/0/0"
                ])

            col_widths = [50, 25, 25, 25, 25, 25, 25, 25, 25, 25, 35, 25, 25, 25, 50]
            return {'header': header, 'table': table, 'col_widths': col_widths}

    def generate_monthly_by_weeks_report(self, events, attendances, start_date, end_date, institution_name, direction_name, audience_name, format_name, event_type_name):
        header = [
            "Ежемесячный отчёт по посещениям и массовой работе",
            f"Период: {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}",
            f"Учреждение: {institution_name}",
            f"Направление: {direction_name}",
            f"Аудитория: {audience_name}",
            f"Формат: {format_name}",
            f"Форма мероприятия: {event_type_name}"
        ]

        table = [
            [
                "Неделя",
                "Посещения",
                "",
                "Мероприятия",
                "", "", "", "",
                "Обслужено, чел.",
                "Дети, чел.",
                "Подростки, чел.",
                "Занятия клубов, чел."
            ],
            [
                "",
                "Всего",
                "",
                "Всего",
                "Выездные",
                "Открытые площадки",
                "",
                "Онлайн",
                "",
                "",
                "",
                ""
            ]
        ]

        with get_session() as session:
            event_types = session.query(EventType).all()
            event_type_map = {et.name: et.id for et in event_types}

            weeks = []
            current_date = start_date
            while current_date <= end_date:
                week_start = current_date - timedelta(days=current_date.weekday())
                week_end = min(week_start + timedelta(days=6), end_date)
                if week_start >= start_date:
                    weeks.append((week_start, week_end))
                current_date = week_end + timedelta(days=1)

            weekly_data = {}
            for week_start, week_end in weeks:
                week_key = f"{week_start.strftime('%d-%m %B')} - {week_end.strftime('%d-%m %B')}"
                weekly_data[week_key] = {
                    "total_visits": 0,
                    "total_events": 0,
                    "offsite_events": 0,
                    "open_space_events": 0,
                    "online_events": 0,
                    "total_attendees": 0,
                    "child_attendees": 0,
                    "at_risk_teens": 0,
                    "club_info": "0/0/0"
                }

            for event in events:
                event_date = event.date
                for week_start, week_end in weeks:
                    if week_start <= event_date <= week_end:
                        week_key = f"{week_start.strftime('%d-%m %B')} - {week_end.strftime('%d-%m %B')}"
                        weekly_data[week_key]["total_events"] += 1
                        if event.event_type:
                            if event.event_type.name == "Выездное":
                                weekly_data[week_key]["offsite_events"] += 1
                            elif event.event_type.name == "На открытых площадках":
                                weekly_data[week_key]["open_space_events"] += 1
                            elif event.event_type.name == "Онлайн":
                                weekly_data[week_key]["online_events"] += 1
                        break

            for attendance in attendances:
                event_date = attendance.event.date
                for week_start, week_end in weeks:
                    if week_start <= event_date <= week_end:
                        week_key = f"{week_start.strftime('%d-%m %B')} - {week_end.strftime('%d-%m %B')}"
                        weekly_data[week_key]["total_attendees"] += attendance.total_attendees or 0
                        weekly_data[week_key]["child_attendees"] += attendance.child_attendees or 0
                        weekly_data[week_key]["at_risk_teens"] += attendance.at_risk_teens or 0
                        weekly_data[week_key]["total_visits"] += attendance.total_attendees or 0
                        break

            total_visits = 0
            total_events = 0
            total_offsite_events = 0
            total_open_space_events = 0
            total_online_events = 0
            total_attendees = 0
            total_child_attendees = 0
            total_risk_teens = 0

            for week_key, data in weekly_data.items():
                table.append([
                    week_key,
                    data["total_visits"],
                    "",
                    data["total_events"],
                    data["offsite_events"],
                    data["open_space_events"],
                    "",
                    data["online_events"],
                    data["total_attendees"],
                    data["child_attendees"],
                    data["at_risk_teens"],
                    data["club_info"]
                ])
                total_visits += data["total_visits"]
                total_events += data["total_events"]
                total_offsite_events += data["offsite_events"]
                total_open_space_events += data["open_space_events"]
                total_online_events += data["online_events"]
                total_attendees += data["total_attendees"]
                total_child_attendees += data["child_attendees"]
                total_risk_teens += data["at_risk_teens"]

            table.append([
                "ИТОГО по ЦБС",
                total_visits,
                "",
                total_events,
                total_offsite_events,
                total_open_space_events,
                "",
                total_online_events,
                total_attendees,
                total_child_attendees,
                total_risk_teens,
                "0/0/0"
            ])

        col_widths = [50, 30, 20, 20, 20, 20, 20, 20, 20, 20, 20, 30]
        return {'header': header, 'table': table, 'col_widths': col_widths}

    def generate_quarterly_by_months_report(self, events, attendances, start_date, end_date, institution_name, direction_name, audience_name, format_name, event_type_name):
        header = [
            "Ежеквартальный отчёт",
            f"Период: {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}",
            f"Учреждение: {institution_name}",
            f"Направление: {direction_name}",
            f"Аудитория: {audience_name}",
            f"Формат: {format_name}",
            f"Форма мероприятия: {event_type_name}"
        ]

        table = [
            [
                "Месяц",
                "Посещения",
                "",
                "Мероприятия",
                "", "", "", "",
                "Обслужено, чел.",
                "Дети, чел.",
                "Подростки, чел.",
                "Занятия клубов, чел."
            ],
            [
                "",
                "Всего",
                "",
                "Всего",
                "Выездные",
                "Открытые площадки",
                "",
                "Онлайн",
                "",
                "",
                "",
                ""
            ]
        ]

        MONTHS_RU = {
            "january": "Январь", "february": "Февраль", "march": "Март",
            "april": "Апрель", "may": "Май", "june": "Июнь",
            "july": "Июль", "august": "Август", "september": "Сентябрь",
            "october": "Октябрь", "november": "Ноябрь", "december": "Декабрь"
        }

        with get_session() as session:
            event_types = session.query(EventType).all()
            event_type_map = {et.name: et.id for et in event_types}

            months = {}
            current_date = start_date
            while current_date <= end_date:
                month_key = current_date.strftime("%B").lower()
                if month_key not in months:
                    months[month_key] = {
                        "total_visits": 0,
                        "total_events": 0,
                        "offsite_events": 0,
                        "open_space_events": 0,
                        "online_events": 0,
                        "total_attendees": 0,
                        "child_attendees": 0,
                        "at_risk_teens": 0,
                        "club_info": "0/0/0"
                    }
                current_date += timedelta(days=30)

            for event in events:
                month_key = event.date.strftime("%B").lower()
                if month_key in months:
                    months[month_key]["total_events"] += 1
                    if event.event_type:
                        if event.event_type.name == "Выездное":
                            months[month_key]["offsite_events"] += 1
                        elif event.event_type.name == "На открытых площадках":
                            months[month_key]["open_space_events"] += 1
                        elif event.event_type.name == "Онлайн":
                            months[month_key]["online_events"] += 1

            for attendance in attendances:
                month_key = attendance.event.date.strftime("%B").lower()
                if month_key in months:
                    months[month_key]["total_attendees"] += attendance.total_attendees or 0
                    months[month_key]["child_attendees"] += attendance.child_attendees or 0
                    months[month_key]["at_risk_teens"] += attendance.at_risk_teens or 0
                    months[month_key]["total_visits"] += attendance.total_attendees or 0

            total_visits = 0
            total_events = 0
            total_offsite_events = 0
            total_open_space_events = 0
            total_online_events = 0
            total_attendees = 0
            total_child_attendees = 0
            total_risk_teens = 0

            for month_key, data in months.items():
                month_ru = MONTHS_RU.get(month_key, month_key.capitalize())
                table.append([
                    month_ru,
                    data["total_visits"],
                    "",
                    data["total_events"],
                    data["offsite_events"],
                    data["open_space_events"],
                    "",
                    data["online_events"],
                    data["total_attendees"],
                    data["child_attendees"],
                    data["at_risk_teens"],
                    data["club_info"]
                ])
                total_visits += data["total_visits"]
                total_events += data["total_events"]
                total_offsite_events += data["offsite_events"]
                total_open_space_events += data["open_space_events"]
                total_online_events += data["online_events"]
                total_attendees += data["total_attendees"]
                total_child_attendees += data["child_attendees"]
                total_risk_teens += data["at_risk_teens"]

            table.append([
                "ИТОГО по ЦБС",
                total_visits,
                "",
                total_events,
                total_offsite_events,
                total_open_space_events,
                "",
                total_online_events,
                total_attendees,
                total_child_attendees,
                total_risk_teens,
                "0/0/0"
            ])

        col_widths = [50, 30, 20, 20, 20, 20, 20, 20, 20, 20, 20, 30]
        return {'header': header, 'table': table, 'col_widths': col_widths}

    def generate_digital_indicators_by_directions_report(self, events, attendances, start_date, end_date, institution_name, direction_name, audience_name, format_name, event_type_name):
        header = [
            f"Цифровые показатели массовой работы, {start_date.year}",
            f"Период: {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}",
            f"Учреждение: {institution_name}",
            f"Направление: {direction_name}",
            f"Аудитория: {audience_name}",
            f"Формат: {format_name}",
            f"Форма мероприятия: {event_type_name}"
        ]

        table = [
            [
                "Направления",
                "Мероприятия, всего",
                "Посещения",
                "Мероприятия для детей",
                "Посещения детей",
                "Культ-досуговые",
                "",
                "Информ-просветительские",
                ""
            ],
            [
                "",
                "",
                "",
                "",
                "",
                "Мероприятия",
                "Посещения",
                "Мероприятия",
                "Посещения"
            ]
        ]

        predefined_directions = [
            "Духовное развитие и нравственное воспитание",
            "Педагогика, этика, культура поведения",
            f"Летние чтения – {start_date.year}",
            "Пропаганда художественной литературы",
            "Эстетическое воспитание",
            "Помощь школьной программе, День знаний",
            "Продвижение исторических знаний",
            "Патриотическое воспитание",
            "Формирование правовой культуры",
            "Толерантность и межнациональное общение",
            "Здоровый образ жизни",
            "Спорт",
            "Молодёжная политика, социализация, профориентация",
            "Наука и техника",
            "Экологическое просвещение",
            "Краеведение, градоведение",
            "Формирование информационной культуры"
        ]

        with get_session() as session:
            directions = {direction: {
                "total_events": 0,
                "total_attendees": 0,
                "child_events": 0,
                "child_attendees": 0,
                "cultural_events": 0,
                "cultural_attendees": 0,
                "info_events": 0,
                "info_attendees": 0
            } for direction in predefined_directions}

            for event in events:
                if event.direction and event.direction.name in directions:
                    direction = event.direction.name
                    directions[direction]["total_events"] += 1
                    if event.target_audience and event.target_audience.name == "Дети":
                        directions[direction]["child_events"] += 1
                    if event.classification:
                        if event.classification.name == "Культ-досуговые":
                            directions[direction]["cultural_events"] += 1
                        elif event.classification.name == "Информ-просветительские":
                            directions[direction]["info_events"] += 1

            for attendance in attendances:
                event = attendance.event
                if event.direction and event.direction.name in directions:
                    direction = event.direction.name
                    directions[direction]["total_attendees"] += attendance.total_attendees or 0
                    if event.target_audience and event.target_audience.name == "Дети":
                        directions[direction]["child_attendees"] += attendance.total_attendees or 0
                    if event.classification:
                        if event.classification.name == "Культ-досуговые":
                            directions[direction]["cultural_attendees"] += attendance.total_attendees or 0
                        elif event.classification.name == "Информ-просветительские":
                            directions[direction]["info_attendees"] += attendance.total_attendees or 0

            total_events = 0
            total_attendees = 0
            total_child_events = 0
            total_child_attendees = 0
            total_cultural_events = 0
            total_cultural_attendees = 0
            total_info_events = 0
            total_info_attendees = 0

            for direction in predefined_directions:
                data = directions[direction]
                table.append([
                    direction,
                    data["total_events"],
                    data["total_attendees"],
                    data["child_events"],
                    data["child_attendees"],
                    data["cultural_events"],
                    data["cultural_attendees"],
                    data["info_events"],
                    data["info_attendees"]
                ])
                total_events += data["total_events"]
                total_attendees += data["total_attendees"]
                total_child_events += data["child_events"]
                total_child_attendees += data["child_attendees"]
                total_cultural_events += data["cultural_events"]
                total_cultural_attendees += data["cultural_attendees"]
                total_info_events += data["info_events"]
                total_info_attendees += data["info_attendees"]

            table.append([
                "ИТОГО",
                total_events,
                total_attendees,
                total_child_events,
                total_child_attendees,
                total_cultural_events,
                total_cultural_attendees,
                total_info_events,
                total_info_attendees
            ])

        col_widths = [70, 30, 30, 30, 30, 30, 30, 30, 30]
        return {'header': header, 'table': table, 'col_widths': col_widths}


    def add_record(self):
        table_name = self.table_selector.currentText()
        with get_session() as session:
            try:
                dialog = AddRecordDialog(self, table_name, session)
                if dialog.exec():
                    self.refresh_table()
                    self.refresh_combos()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось открыть диалог добавления: {str(e)}")

    def edit_record(self):
            selected_rows = self.admin_table.selectionModel().selectedRows()
            if not selected_rows:
                QMessageBox.warning(self, "Предупреждение", "Выберите запись для редактирования")
                return

            row = selected_rows[0].row()
            table_name = self.table_selector.currentText()
            with get_session() as session:
                try:
                    record_id = self.admin_table.item(row, 0).data(Qt.UserRole)
                    if table_name == "Расшифровка":
                        record = session.query(Decoding).filter(Decoding.id == record_id).first()
                    elif table_name == "Учреждение":
                        record = session.query(Institution).filter(Institution.id == record_id).first()
                    elif table_name == "Пользователь":
                        record = session.query(User).filter(User.id == record_id).first()
                    elif table_name == "Роль":
                        record = session.query(Role).filter(Role.id == record_id).first()
                    elif table_name == "Форматы":
                        record = session.query(EventFormat).filter(EventFormat.id == record_id).first()
                    elif table_name == "Классификации":
                        record = session.query(EventClassification).filter(EventClassification.id == record_id).first()
                    elif table_name == "Направления":
                        record = session.query(ActivityDirection).filter(ActivityDirection.id == record_id).first()
                    elif table_name == "Типы мероприятий":
                        record = session.query(EventType).filter(EventType.id == record_id).first()
                    elif table_name == "Аудитории":
                        record = session.query(TargetAudience).filter(TargetAudience.id == record_id).first()
                    elif table_name == "Места проведения":
                        record = session.query(Venue).filter(Venue.id == record_id).first()
                    else:
                        QMessageBox.critical(self, "Ошибка", "Неизвестная таблица")
                        return

                    if not record:
                        QMessageBox.warning(self, "Ошибка", "Запись не найдена")
                        return

                    dialog = AddRecordDialog(self, table_name, session, record)
                    if dialog.exec():
                        session.commit()
                        self.refresh_table()
                        self.refresh_combos()
                except Exception as e:
                    session.rollback()
                    QMessageBox.critical(self, "Ошибка", f"Не удалось отредактировать запись: {str(e)}")

    def refresh_table(self):
        table_name = self.table_selector.currentText()
        with get_session() as session:
            try:
                if table_name == "Расшифровка":
                    records = session.query(Decoding).all()
                    headers = ["Название", "Описание"]
                    self.populate_admin_table(records, headers, ["name", "description"], [150, 300])
                elif table_name == "Учреждение":
                    records = session.query(Institution).all()
                    headers = ["Название", "Адрес"]
                    self.populate_admin_table(records, headers, ["name", "address"], [150, 300])
                elif table_name == "Пользователь":
                    records = session.query(User).options(joinedload(User.role)).all()
                    headers = ["Логин", "Роль"]
                    self.populate_admin_table(records, headers, ["login", "role.name"], [150, 150])
                elif table_name == "Роль":
                    records = session.query(Role).all()
                    headers = ["Название"]
                    self.populate_admin_table(records, headers, ["name"], [300])
                elif table_name == "Форматы":
                    records = session.query(EventFormat).all()
                    headers = ["Название"]
                    self.populate_admin_table(records, headers, ["name"], [300])
                elif table_name == "Классификации":
                    records = session.query(EventClassification).all()
                    headers = ["Название"]
                    self.populate_admin_table(records, headers, ["name"], [300])
                elif table_name == "Направления":
                    records = session.query(ActivityDirection).all()
                    headers = ["Название"]
                    self.populate_admin_table(records, headers, ["name"], [300])
                elif table_name == "Типы мероприятий":
                    records = session.query(EventType).all()
                    headers = ["Название"]
                    self.populate_admin_table(records, headers, ["name"], [300])
                elif table_name == "Аудитории":
                    records = session.query(TargetAudience).all()
                    headers = ["Название"]
                    self.populate_admin_table(records, headers, ["name"], [300])
                elif table_name == "Места проведения":
                    records = session.query(Venue).all()
                    headers = ["Название"]
                    self.populate_admin_table(records, headers, ["name"], [300])
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось обновить таблицу: {str(e)}")

    def populate_admin_table(self, records, headers, attributes, col_widths=None):
        self.admin_table.setRowCount(len(records))
        self.admin_table.setColumnCount(len(headers))
        self.admin_table.setHorizontalHeaderLabels(headers)
        self.admin_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        for row, record in enumerate(records):
            for col, attr in enumerate(attributes):
                value = record
                for part in attr.split("."):
                    value = getattr(value, part, "")
                item = QTableWidgetItem(str(value or ""))
                item.setData(Qt.UserRole, record.id)
                self.admin_table.setItem(row, col, item)

        if col_widths:
            for col, width in enumerate(col_widths):
                self.admin_table.setColumnWidth(col, width)

    def delete_record(self):
        selected_rows = self.admin_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Предупреждение", "Выберите запись для удаления")
            return

        row = selected_rows[0].row()
        record_id = self.admin_table.item(row, 0).data(Qt.UserRole)
        table_name = self.table_selector.currentText()
        reply = QMessageBox.question(self, "Подтверждение", "Вы уверены, что хотите удалить эту запись?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            with get_session() as session:
                try:
                    if table_name == "Расшифровка":
                        record = session.query(Decoding).filter(Decoding.id == record_id).first()
                    elif table_name == "Учреждение":
                        record = session.query(Institution).filter(Institution.id == record_id).first()
                    elif table_name == "Пользователь":
                        record = session.query(User).filter(User.id == record_id).first()
                    elif table_name == "Роль":
                        record = session.query(Role).filter(Role.id == record_id).first()
                    elif table_name == "Форматы":
                        record = session.query(EventFormat).filter(EventFormat.id == record_id).first()
                    elif table_name == "Классификации":
                        record = session.query(EventClassification).filter(EventClassification.id == record_id).first()
                    elif table_name == "Направления":
                        record = session.query(ActivityDirection).filter(ActivityDirection.id == record_id).first()
                    elif table_name == "Типы мероприятий":
                        record = session.query(EventType).filter(EventType.id == record_id).first()
                    elif table_name == "Аудитории":
                        record = session.query(TargetAudience).filter(TargetAudience.id == record_id).first()
                    elif table_name == "Места проведения":
                        record = session.query(Venue).filter(Venue.id == record_id).first()
                    else:
                        QMessageBox.critical(self, "Ошибка", "Неизвестная таблица")
                        return

                    if record:
                        session.delete(record)
                        session.commit()
                        QMessageBox.information(self, "Успех", "Запись удалена")
                        self.refresh_table()
                        self.refresh_combos()
                    else:
                        QMessageBox.warning(self, "Ошибка", "Запись не найдена")
                except Exception as e:
                    session.rollback()
                    QMessageBox.critical(self, "Ошибка", f"Не удалось удалить запись: {str(e)}")

    def refresh_combos(self):
        with get_session() as session:
            try:
                institutions = session.query(Institution).all()
                current_institution = self.institution_filter_table.currentText()
                self.institution_filter_table.clear()
                self.institution_filter_table.addItem("Все учреждения")
                self.institution_filter_table.addItems([i.name for i in institutions])
                if current_institution in [i.name for i in institutions]:
                    self.institution_filter_table.setCurrentText(current_institution)

                directions = session.query(ActivityDirection).all()
                current_direction = self.direction_filter_table.currentText()
                self.direction_filter_table.clear()
                self.direction_filter_table.addItem("Все направления")
                self.direction_filter_table.addItems([d.name for d in directions])
                if current_direction in [d.name for d in directions]:
                    self.direction_filter_table.setCurrentText(current_direction)

                audiences = session.query(TargetAudience).all()
                current_audience = self.audience_filter_table.currentText()
                self.audience_filter_table.clear()
                self.audience_filter_table.addItem("Все аудитории")
                self.audience_filter_table.addItems([a.name for a in audiences])
                if current_audience in [a.name for a in audiences]:
                    self.audience_filter_table.setCurrentText(current_audience)

                formats = session.query(EventFormat).all()
                current_format = self.format_filter_table.currentText()
                self.format_filter_table.clear()
                self.format_filter_table.addItem("Все форматы")
                self.format_filter_table.addItems([f.name for f in formats])
                if current_format in [f.name for f in formats]:
                    self.format_filter_table.setCurrentText(current_format)

                event_types = session.query(EventType).all()
                current_event_type = self.event_type_filter_table.currentText()
                self.event_type_filter_table.clear()
                self.event_type_filter_table.addItem("Все формы")
                self.event_type_filter_table.addItems([et.name for et in event_types])
                if current_event_type in [et.name for et in event_types]:
                    self.event_type_filter_table.setCurrentText(current_event_type)

                current_institution = self.institution_filter.currentText()
                self.institution_filter.clear()
                self.institution_filter.addItem("Все учреждения")
                self.institution_filter.addItems([i.name for i in institutions])
                if current_institution in [i.name for i in institutions]:
                    self.institution_filter.setCurrentText(current_institution)

                current_direction = self.direction_filter.currentText()
                self.direction_filter.clear()
                self.direction_filter.addItem("Все направления")
                self.direction_filter.addItems([d.name for d in directions])
                if current_direction in [d.name for d in directions]:
                    self.direction_filter.setCurrentText(current_direction)

                current_audience = self.audience_filter.currentText()
                self.audience_filter.clear()
                self.audience_filter.addItem("Все аудитории")
                self.audience_filter.addItems([a.name for a in audiences])
                if current_audience in [a.name for a in audiences]:
                    self.audience_filter.setCurrentText(current_audience)

                current_format = self.format_filter.currentText()
                self.format_filter.clear()
                self.format_filter.addItem("Все форматы")
                self.format_filter.addItems([f.name for f in formats])
                if current_format in [f.name for f in formats]:
                    self.format_filter.setCurrentText(current_format)

                current_event_type = self.event_type_filter.currentText()
                self.event_type_filter.clear()
                self.event_type_filter.addItem("Все формы")
                self.event_type_filter.addItems([et.name for et in event_types])
                if current_event_type in [et.name for et in event_types]:
                    self.event_type_filter.setCurrentText(current_event_type)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось обновить выпадающие списки: {str(e)}")


STYLESHEET = """
    /* Общие стили для окна и диалогов */
    QDialog, QMainWindow { 
        background-color: #F7F9FC; 
    }

    /* Поля ввода и текстовые области */
    QLineEdit, QTextEdit { 
        background-color: #FFFFFF; 
        color: #2D3748; 
        border: 1px solid #CBD5E0; 
        padding: 10px; 
        font-size: 14px; 
        font-family: 'Inter', 'Roboto', sans-serif; 
        border-radius: 6px; 
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05); 
    }
    QLineEdit:focus, QTextEdit:focus { 
        border: 1px solid #6B7280; 
        box-shadow: 0 0 5px rgba(107, 114, 128, 0.2); 
    }
    /* Cтили для поля поиска */
    QLineEdit#search_input { 
        min-width: 250px; 
        padding-left: 35px;
        background: #FFFFFF url(:/svg/search.svg) no-repeat 10px center; 
        background-size: 20px; 
    }
    QLineEdit#search_input:focus { 
        background-color: #FFFFFF; 
        border: 1px solid #6B7280; 
        box-shadow: 0 0 5px rgba(107, 114, 128, 0.2); 
    }

    /* Кнопки */
    QPushButton { 
        background-color: #E2E8F0; 
        color: #1F2937; 
        border: none; 
        padding: 10px 16px; 
        font-size: 14px; 
        font-family: 'Inter', 'Roboto', sans-serif; 
        border-radius: 6px; 
        transition: background-color 0.2s ease, transform 0.1s ease; 
    }
    QPushButton:hover { 
        background-color: #CBD5E0; 
        transform: scale(1.02); 
    }
    QPushButton:pressed { 
        transform: scale(0.98); 
    }
    QPushButton#delete_button { 
        background-color: #FECACA; 
        color: #B91C1C; 
        icon: url(:/svg/trash.svg); 
        min-width: 150px; 
        max-width: 150px; 
        min-height: 40px; 
        max-height: 40px; 
    }
    QPushButton#delete_button:hover { 
        background-color: #FCA5A5; 
    }
    QPushButton#admin_button { 
        min-width: 150px; 
        max-width: 150px; 
        min-height: 40px; 
        max-height: 40px; 
        background-color: #BFDBFE; 
        color: #1E3A8A; 
        icon: url(:/svg/add.svg); 
    }
    QPushButton#admin_button:hover { 
        background-color: #93C5FD; 
    }
    QPushButton#save_report_button { 
        background-color: #BFDBFE; 
        color: #1E3A8A; 
        icon: url(:/svg/save.svg); 
    }
    QPushButton#save_report_button:hover { 
        background-color: #93C5FD; 
    }

    /* Таблицы */
    QTableWidget, QTableView { 
        background-color: #FFFFFF; 
        color: #2D3748; 
        border: 1px solid #E2E8F0; 
        font-size: 14px; 
        font-family: 'Inter', 'Roboto', sans-serif; 
        gridline-color: #E2E8F0; 
        border-radius: 6px; 
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05); 
    }
    QTableWidget::item { 
        padding: 8px; 
        border: none; 
    }
    QTableWidget::item:selected { 
        background-color: #DBEAFE; 
        color: #1E3A8A; 
    }
    QHeaderView::section { 
        background-color: #EDF2F7; 
        color: #1F2937; 
        padding: 8px; 
        border: none; 
        font-family: 'Inter', 'Roboto', sans-serif; 
        border-bottom: 1px solid #E2E0F0; 
    }

    /* Вкладки */
    QTabWidget::pane { 
        border: 1px solid #E2E8F0; 
        border-radius: 6px; 
        background-color: #FFFFFF; 
    }
    QTabBar { 
        align: center;
    }
    QTabBar::tab { 
        background-color: #E2E8F0; 
        color: #4B5563; 
        padding: 10px 20px; 
        font-size: 14px; 
        font-family: 'Inter', 'Roboto', sans-serif; 
        border-top-left-radius: 6px; 
        border-top-right-radius: 6px; 
        margin-right: 2px; 
        text-align: center;
    }
    QTabBar::tab:selected { 
        background-color: #FFFFFF; 
        color: #1E3A8A; 
        border-bottom: 2px solid #3B82F6; 
    }
    QTabBar::tab:hover { 
        background-color: #D1D5DB; 
    }

    /* Календарь */
    QCalendarWidget { 
        background-color: #FFFFFF; 
        color: #2D3748; 
        border: 1px solid #E2E8F0; 
        border-radius: 6px; 
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05); 
    }
    QCalendarWidget QToolButton { 
        background-color: #E2E8F0; 
        color: #1F2937; 
        border: none; 
        border-radius: 6px; 
        padding: 8px; 
        font-size: 14px; 
        font-family: 'Inter', 'Roboto', sans-serif; 
        width: 100px; 
        height: 30px; 
    }
    QCalendarWidget QToolButton#qt_calendar_monthbutton { 
        width: 200px; 
    }
    QCalendarWidget QToolButton#qt_calendar_yearbutton { 
        width: 100px; 
    }
    QCalendarWidget QToolButton:hover { 
        background-color: #CBD5E0; 
    }
    QCalendarWidget QWidget#qt_calendar_navigationbar { 
        background-color: #FFFFFF; 
        border-bottom: 1px solid #E2E8F0; 
    }
    QCalendarWidget QTableView { 
        border: none; 
        box-shadow: none; 
    }

    /* Список */
    QListWidget { 
        background-color: #FFFFFF; 
        color: #2D3748; 
        border: 1px solid #E2E8F0; 
        font-size: 14px; 
        font-family: 'Inter', 'Roboto', sans-serif; 
        border-radius: 6px; 
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05); 
    }
    QListWidget::item { 
        padding: 10px; 
    }
    QListWidget::item:selected { 
        background-color: #DBEAFE; 
        color: #1E3A8A; 
    }

    /* Группы */
    QGroupBox { 
        background-color: #FFFFFF; 
        color: #1F2937; 
        font-size: 16px; 
        font-family: 'Inter', 'Roboto', sans-serif; 
        border: 1px solid #E2E8F0; 
        border-radius: 6px; 
        padding: 15px; 
        margin-top: 15px; 
    }
    QGroupBox::title { 
        subcontrol-origin: margin; 
        subcontrol-position: top left; 
        padding: 5px 10px; 
        background-color: #EDF2F7; 
        border-top-left-radius: 6px; 
        border-top-right-radius: 6px; 
    }

    /* Метки */
    QLabel { 
        color: #1F2937; 
        font-size: 18px; 
        font-family: 'Inter', 'Roboto', sans-serif; 
    }

    /* Поля даты */
    QDateEdit { 
        background-color: #FFFFFF; 
        color: #2D3748; 
        border: 1px solid #CBD5E0; 
        padding: 10px; 
        font-size: 14px; 
        font-family: 'Inter', 'Roboto', sans-serif; 
        border-radius: 6px; 
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05); 
    }
    QDateEdit:focus { 
        border: 1px solid #6B7280; 
        box-shadow: 0 0 5px rgba(107, 114, 128, 0.2); 
    }

    /* Выпадающие списки */
    QComboBox { 
        background-color: #FFFFFF; 
        color: #2D3748; 
        border: 1px solid #CBD5E0; 
        padding: 8px 30px 8px 10px;
        font-size: 14px; 
        font-family: 'Inter', 'Roboto', sans-serif; 
        border-radius: 6px; 
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05); 
        min-width: 150px;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FFFFFF, stop:0.95 #F7F9FC);
    }
    QComboBox:hover { 
        border: 1px solid #6B7280; 
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FFFFFF, stop:0.95 #E2E8F0); 
    }
    QComboBox QAbstractItemView { 
        background-color: #FFFFFF; 
        color: #2D3748; 
        selection-background-color: #DBEAFE; 
        selection-color: #1E3A8A; 
        font-size: 14px; 
        font-family: 'Inter', 'Roboto', sans-serif; 
        border: 1px solid #E2E8F0; 
        border-radius: 6px; 
    }
    QComboBox::drop-down { 
        border: none; 
        width: 30px; 
        background: transparent; 
    }
    QComboBox::down-arrow { 
        width: 12px; 
        height: 12px; 
    }

    /* Логотип */
    QLabel#logo_label {
        padding: 10px;
        background: transparent;
    }
"""


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

from PySide6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox, QDateEdit, QPushButton, QTextEdit, QHBoxLayout
from PySide6.QtCore import QDate

class EventDetailsDialog(QDialog):
    def __init__(self, parent=None, event_data=None, institutions=None, formats=None, classifications=None, directions=None, event_types=None, audiences=None, venues=None):
        super().__init__(parent)
        self.event_data = event_data
        self.setWindowTitle("Детали мероприятия")
        self.layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()
        
        self.name_input = QLineEdit()
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.description_input = QTextEdit()
        self.organizer_combo = QComboBox()
        self.format_combo = QComboBox()
        self.classification_combo = QComboBox()
        self.direction_combo = QComboBox()
        self.event_type_combo = QComboBox()
        self.audience_combo = QComboBox()
        self.venue_combo = QComboBox()
        self.total_attendees_input = QLineEdit()
        self.child_attendees_input = QLineEdit()
        self.volunteers_input = QLineEdit()
        self.at_risk_teens_input = QLineEdit()
        
        self.form_layout.addRow("Название:", self.name_input)
        self.form_layout.addRow("Дата:", self.date_input)
        self.form_layout.addRow("Описание:", self.description_input)
        self.form_layout.addRow("Организатор:", self.organizer_combo)
        self.form_layout.addRow("Формат:", self.format_combo)
        self.form_layout.addRow("Классификация:", self.classification_combo)
        self.form_layout.addRow("Направление:", self.direction_combo)
        self.form_layout.addRow("Форма мероприятия:", self.event_type_combo)
        self.form_layout.addRow("Аудитория:", self.audience_combo)
        self.form_layout.addRow("Место проведения:", self.venue_combo)
        self.form_layout.addRow("Всего посетителей:", self.total_attendees_input)
        self.form_layout.addRow("Детей:", self.child_attendees_input)
        self.form_layout.addRow("Волонтёров:", self.volunteers_input)
        self.form_layout.addRow("Подростков группы риска:", self.at_risk_teens_input)
        
        self.layout.addLayout(self.form_layout)
        
        self.save_button = QPushButton("Сохранить")
        self.save_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.reject)
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        self.layout.addLayout(button_layout)
        
        self.set_data(event_data, institutions, formats, classifications, directions, event_types, audiences, venues)
    
    def set_data(self, event_data, institutions, formats, classifications, directions, event_types, audiences, venues):
        self.name_input.setText(event_data.name or "")
        self.date_input.setDate(QDate(event_data.date.year, event_data.date.month, event_data.date.day))
        self.description_input.setText(event_data.description or "")
        
        self.organizer_combo.addItems([i.name for i in institutions])
        self.organizer_combo.setProperty("ids", [i.id for i in institutions])
        self.organizer_combo.setCurrentText(event_data.organizer.name if event_data.organizer else "")
        
        self.format_combo.addItems([f.name for f in formats])
        self.format_combo.setProperty("ids", [f.id for f in formats])
        self.format_combo.setCurrentText(event_data.format.name if event_data.format else "")
        
        self.classification_combo.addItems([c.name for c in classifications])
        self.classification_combo.setProperty("ids", [c.id for c in classifications])
        self.classification_combo.setCurrentText(event_data.classification.name if event_data.classification else "")
        
        self.direction_combo.addItems([d.name for d in directions])
        self.direction_combo.setProperty("ids", [d.id for d in directions])
        self.direction_combo.setCurrentText(event_data.direction.name if event_data.direction else "")
        
        self.event_type_combo.addItems([et.name for et in event_types])
        self.event_type_combo.setProperty("ids", [et.id for et in event_types])
        self.event_type_combo.setCurrentText(event_data.event_type.name if event_data.event_type else "")
        
        self.audience_combo.addItems([a.name for a in audiences])
        self.audience_combo.setProperty("ids", [a.id for a in audiences])
        self.audience_combo.setCurrentText(event_data.target_audience.name if event_data.target_audience else "")
        
        self.venue_combo.addItems([v.name for v in venues])
        self.venue_combo.setProperty("ids", [v.id for v in venues])
        self.venue_combo.setCurrentText(event_data.venue.name if event_data.venue else "")
        
        attendance = event_data.attendances[0] if event_data.attendances else None
        self.total_attendees_input.setText(str(attendance.total_attendees or "") if attendance else "")
        self.child_attendees_input.setText(str(attendance.child_attendees or "") if attendance else "")
        self.volunteers_input.setText(str(attendance.volunteers or "") if attendance else "")
        self.at_risk_teens_input.setText(str(attendance.at_risk_teens or "") if attendance else "")
    
    def get_data(self):
        return {
            "name": self.name_input.text(),
            "date": self.date_input.date().toPython(),
            "description": self.description_input.toPlainText(),
            "organizer_id": self.organizer_combo.property("ids")[self.organizer_combo.currentIndex()],
            "format_id": self.format_combo.property("ids")[self.format_combo.currentIndex()],
            "classification_id": self.classification_combo.property("ids")[self.classification_combo.currentIndex()],
            "direction_id": self.direction_combo.property("ids")[self.direction_combo.currentIndex()],
            "event_type_id": self.event_type_combo.property("ids")[self.event_type_combo.currentIndex()],
            "audience_id": self.audience_combo.property("ids")[self.audience_combo.currentIndex()],
            "venue_id": self.venue_combo.property("ids")[self.venue_combo.currentIndex()],
            "total_attendees": self.total_attendees_input.text(),
            "child_attendees": self.child_attendees_input.text(),
            "volunteers": self.volunteers_input.text(),
            "at_risk_teens": self.at_risk_teens_input.text()
        }

from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QComboBox, QPushButton, QHBoxLayout, QMessageBox
from styles.styles import STYLESHEET
from db import Decoding, Institution, User, Role, EventFormat, EventClassification, ActivityDirection, EventType, TargetAudience, Venue
from sqlalchemy.sql import func

class EditRecordDialog(QDialog):
    def __init__(self, parent=None, table_name=None, record=None, session=None):
        super().__init__(parent)
        self.setWindowTitle(f"Редактировать запись: {table_name}")

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

from PySide6.QtWidgets import QMainWindow, QHeaderView, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QLineEdit, QPushButton, QTabWidget, QDateEdit, QLabel, QComboBox, QCalendarWidget, QListWidget, QGroupBox, QTableView, QFileDialog, QMessageBox, QListWidgetItem, QTableWidgetItem, QDialog, QFormLayout
from styles.styles import STYLESHEET
from utils.database import get_session
from dialogs.add_event_dialog import AddEventDialog
from dialogs.event_details_dialog import EventDetailsDialog
from db import User, Event, Institution, EventFormat, EventClassification, ActivityDirection, Attendance, EventType, TargetAudience, Venue, Role, Decoding
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import func

class AddRecordDialog(QDialog):
    def __init__(self, parent=None, table_name=None, session=None):
        super().__init__(parent)
        self.setWindowTitle(f"Добавить запись: {table_name}")

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

from PySide6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox, QDateEdit, QPushButton, QTextEdit, QHBoxLayout
from PySide6.QtCore import QDate

class AddEventDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить мероприятие")
        self.layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()
        
        self.name_input = QLineEdit()
        self.date_input = QDateEdit(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.description_input = QTextEdit()
        self.organizer_combo = QComboBox()
        self.format_combo = QComboBox()
        self.classification_combo = QComboBox()
        self.direction_combo = QComboBox()
        self.event_type_combo = QComboBox()
        self.audience_combo = QComboBox()
        self.venue_combo = QComboBox()
        self.total_attendees_input = QLineEdit()
        self.child_attendees_input = QLineEdit()
        self.volunteers_input = QLineEdit()
        self.at_risk_teens_input = QLineEdit()
        
        self.form_layout.addRow("Название:", self.name_input)
        self.form_layout.addRow("Дата:", self.date_input)
        self.form_layout.addRow("Описание:", self.description_input)
        self.form_layout.addRow("Организатор:", self.organizer_combo)
        self.form_layout.addRow("Формат:", self.format_combo)
        self.form_layout.addRow("Классификация:", self.classification_combo)
        self.form_layout.addRow("Направление:", self.direction_combo)
        self.form_layout.addRow("Форма мероприятия:", self.event_type_combo)  # Добавляем
        self.form_layout.addRow("Аудитория:", self.audience_combo)
        self.form_layout.addRow("Место проведения:", self.venue_combo)
        self.form_layout.addRow("Всего посетителей:", self.total_attendees_input)
        self.form_layout.addRow("Детей:", self.child_attendees_input)
        self.form_layout.addRow("Волонтёров:", self.volunteers_input)
        self.form_layout.addRow("Подростков группы риска:", self.at_risk_teens_input)
        
        self.layout.addLayout(self.form_layout)
        
        self.save_button = QPushButton("Сохранить")
        self.save_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.reject)
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        self.layout.addLayout(button_layout)
    
    def set_data(self, institutions, formats, classifications, directions, event_types, audiences, venues):
        self.organizer_combo.addItems([i.name for i in institutions])
        self.organizer_combo.setProperty("ids", [i.id for i in institutions])
        self.format_combo.addItems([f.name for f in formats])
        self.format_combo.setProperty("ids", [f.id for f in formats])
        self.classification_combo.addItems([c.name for c in classifications])
        self.classification_combo.setProperty("ids", [c.id for c in classifications])
        self.direction_combo.addItems([d.name for d in directions])
        self.direction_combo.setProperty("ids", [d.id for d in directions])
        self.event_type_combo.addItems([et.name for et in event_types])
        self.event_type_combo.setProperty("ids", [et.id for et in event_types])
        self.audience_combo.addItems([a.name for a in audiences])
        self.audience_combo.setProperty("ids", [a.id for a in audiences])
        self.venue_combo.addItems([v.name for v in venues])
        self.venue_combo.setProperty("ids", [v.id for v in venues])
    
    def get_data(self):
        return {
            "name": self.name_input.text(),
            "date": self.date_input.date().toPython(),
            "description": self.description_input.toPlainText(),
            "organizer_id": self.organizer_combo.property("ids")[self.organizer_combo.currentIndex()],
            "format_id": self.format_combo.property("ids")[self.format_combo.currentIndex()],
            "classification_id": self.classification_combo.property("ids")[self.classification_combo.currentIndex()],
            "direction_id": self.direction_combo.property("ids")[self.direction_combo.currentIndex()],
            "event_type_id": self.event_type_combo.property("ids")[self.event_type_combo.currentIndex()],
            "audience_id": self.audience_combo.property("ids")[self.audience_combo.currentIndex()],
            "venue_id": self.venue_combo.property("ids")[self.venue_combo.currentIndex()],
            "total_attendees": self.total_attendees_input.text(),
            "child_attendees": self.child_attendees_input.text(),
            "volunteers": self.volunteers_input.text(),
            "at_risk_teens": self.at_risk_teens_input.text()
        }
    

import sys
from PySide6.QtWidgets import QApplication
from dialogs.login_dialog import LoginDialog
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    login_dialog = LoginDialog()
    if login_dialog.exec():
        main_window = MainWindow(login_dialog.user_id)
        app.exec()

if __name__ == "__main__":
    main()