from PySide6.QtWidgets import QMainWindow, QHeaderView, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QLineEdit, QPushButton, QTabWidget, QDateEdit, QLabel, QComboBox, QCalendarWidget, QListWidget, QGroupBox, QTableView, QFileDialog, QMessageBox, QListWidgetItem, QTableWidgetItem, QDialog, QFormLayout
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

    def setup_icon(self):
        try:
            response = requests.get("https://цбс.абакан.рф/static/images/logo.png")
            icon = QIcon()
            icon_pixmap = QPixmap()
            icon_pixmap.loadFromData(BytesIO(response.content).read())
            icon.addPixmap(icon_pixmap)
            self.setWindowIcon(icon)
        except:
            pass

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Вкладка "Список"
        self.setup_table_tab()

        # Вкладка "Календарь"
        self.setup_calendar_tab()

        # Вкладка "Админ-панель"
        self.setup_admin_tab()

        # Вкладка "Отчёты"
        self.setup_report_tab()

        main_layout.addWidget(self.tabs)

    def setup_table_tab(self):
        table_tab = QWidget()
        table_layout = QVBoxLayout(table_tab)

        # Верхний горизонтальный макет для поиска и кнопок
        top_layout = QHBoxLayout()
            
        # Поле поиска слева
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по названию")
        top_layout.addWidget(self.search_input)
        top_layout.addStretch()  # Растяжение между поиском и кнопками

        # Кнопки "Добавить" и "Удалить" справа
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

        # Группа фильтров
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
            user = session.query(User).options(
                joinedload(User.role)
            ).filter(User.id == self.user_id).first()
            if user and user.role and user.role.name == "admin":
                admin_tab = QWidget()
                admin_layout = QVBoxLayout(admin_tab)

                admin_title = QLabel("Админ-панель")
                admin_title.setAlignment(Qt.AlignCenter)
                admin_layout.addWidget(admin_title)

                # Секция управления справочниками
                manage_group = QGroupBox("Управление справочниками")
                manage_layout = QVBoxLayout(manage_group)

                self.table_selector = QComboBox()
                self.table_selector.addItems([
                    "Расшифровка", "Учреждение", "Пользователь", "Роль",
                    "Форматы", "Классификации", "Направления",
                    "Типы мероприятий", "Аудитории", "Места проведения"
                ])
                self.table_selector.currentIndexChanged.connect(self.refresh_table)

                # Кнопки Добавить и Удалить рядом с выпадающим списком
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
            "Еженедельный (по неделям)",
            "Ежеквартальный (по месяцам)",
            "Цифровые показатели (по направлениям)"
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

                events = query.all()

                self.events_table.setRowCount(len(events))
                self.events_table.setColumnCount(9)
                self.events_table.setHorizontalHeaderLabels([
                    "Название", "Дата", "Учреждение", "Формат",
                    "Классификация", "Направление", "Тип", "Аудитория", "Место"
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
                    self.events_table.setItem(row, 7, QTableWidgetItem(event.target_audience.name if event.target_audience else ""))
                    self.events_table.setItem(row, 8, QTableWidgetItem(event.venue.name if event.venue else ""))
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
                        target_audience_id=data["target_audience_id"],
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

                    event_data.name = data["name"]
                    event_data.date = data["date"]
                    event_data.description = data["description"]
                    event_data.organizer_id = data["organizer_id"]
                    event_data.format_id = data["format_id"]
                    event_data.classification_id = data["classification_id"]
                    event_data.direction_id = data["direction_id"]
                    event_data.event_type_id = data["event_type_id"]
                    event_data.target_audience_id = data["target_audience_id"]
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

                    event_data.name = data["name"]
                    event_data.date = data["date"]
                    event_data.description = data["description"]
                    event_data.organizer_id = data["organizer_id"]
                    event_data.format_id = data["format_id"]
                    event_data.classification_id = data["classification_id"]
                    event_data.direction_id = data["direction_id"]
                    event_data.event_type_id = data["event_type_id"]
                    event_data.target_audience_id = data["target_audience_id"]
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

                # Eagerly load all relationships to avoid lazy loading issues
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

                events = query.all()

                # Extract event data into a list of dictionaries to avoid session issues
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

                attendances = attendance_query.all()

                if not events and not attendances:
                    QMessageBox.warning(self, "Предупреждение", "Нет данных для формирования отчёта за выбранный период.")
                    return

                if report_type == "Еженедельный (по неделям)":
                    report_data = self.generate_weekly_by_weeks_report(events, attendances, start_date, end_date, institution_name, direction_name, audience_name, format_name)
                elif report_type == "Ежеквартальный (по месяцам)":
                    report_data = self.generate_monthly_by_months_report(events, attendances, start_date, end_date, institution_name, direction_name, audience_name, format_name)
                elif report_type == "Цифровые показатели (по направлениям)":
                    report_data = self.generate_digital_indicators_by_directions_report(events, attendances, start_date, end_date, institution_name, direction_name, audience_name, format_name)
                else:
                    QMessageBox.critical(self, "Ошибка", "Неизвестный тип отчёта.")
                    return

                # Store event data (not Event objects) for use in generate_pdf
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

        doc = SimpleDocTemplate(file_name, pagesize=landscape(A4), rightMargin=10*mm, leftMargin=10*mm, topMargin=10*mm, bottomMargin=10*mm)
        elements = []
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='HeaderStyle', fontName='DejaVuSans', fontSize=14, leading=16, alignment=1))
        styles.add(ParagraphStyle(name='TableStyle', fontName='DejaVuSans', fontSize=10, leading=12, alignment=0))
        styles.add(ParagraphStyle(name='SectionHeader', fontName='DejaVuSans', fontSize=12, leading=14, alignment=0))
        styles.add(ParagraphStyle(name='EventText', fontName='DejaVuSans', fontSize=10, leading=12, alignment=0, spaceAfter=6))

        # Add header
        for line in report_data['header']:
            elements.append(Paragraph(line, styles['HeaderStyle']))
        elements.append(Spacer(1, 10*mm))

        # Add main table
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
                    pdf_row.append(Paragraph(cell, styles['TableStyle']))
                pdf_table_data.append(pdf_row)
            col_widths = report_data.get('col_widths', None)
            if col_widths:
                col_widths = [w * mm for w in col_widths]
            table = Table(pdf_table_data, colWidths=col_widths)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.95, 0.95, 0.95)),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.Color(0.13, 0.13, 0.13)),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSans'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('BACKGROUND', (0, -1), (-1, -1), colors.Color(0.9, 0.9, 0.9)),
                ('GRID', (0, 0), (-1, -1), 1, colors.Color(0.88, 0.88, 0.88)),
                ('BOX', (0, 0), (-1, -1), 1, colors.Color(0.88, 0.88, 0.88)),
            ]))
            elements.append(table)

        # Add spacer before events list
        elements.append(Spacer(1, 20*mm))

        # Add events list section
        elements.append(Paragraph("Список мероприятий", styles['SectionHeader']))
        elements.append(Spacer(1, 5*mm))

        # Use events_data as paragraphs instead of a table
        events_data = report_data.get('events_data', [])
        if events_data:
            for event_data in events_data:
                event_text = f"Название: {event_data['name'] or '-'}."
                event_text += f"\nДата: {event_data['date'].strftime('%d.%m.%Y') if event_data['date'] else '-'}."
                event_text += f"\nОписание: {event_data['description'] or '-'}."
                elements.append(Paragraph(event_text, styles['EventText']))
        else:
            elements.append(Paragraph("Мероприятий за выбранный период не найдено.", styles['TableStyle']))

        doc.build(elements)

    def display_report(self, report_data):
        model = QStandardItemModel()
        table_data = report_data['table']
        headers = table_data[0]
        model.setHorizontalHeaderLabels(headers)
        for row in table_data[1:]:
            items = [QStandardItem(str(cell) if isinstance(cell, (int, float)) else cell or '-') for cell in row]
            model.appendRow(items)
        self.report_preview.setModel(model)
        self.report_preview.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.report_preview.resizeRowsToContents()

    def generate_weekly_by_weeks_report(self, events, attendances, start_date, end_date, institution_name, direction_name, audience_name, format_name):
        header = [
            "Еженедельный отчёт (по неделям) по посещениям и массовой работе",
            f"Период: {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}",
            f"Учреждение: {institution_name}",
            f"Направление: {direction_name}",
            f"Аудитория: {audience_name}",
            f"Формат: {format_name}"
        ]

        table = [
            [
                "Период",
                "Количество посещений всего по библиотеке",
                "Проведено мероприятий",
                "Обслужено всего чел.",
                "В т.ч. детей",
                "В т.ч. подростков группы риска",
                "Кружки/участники/подростки группы риска"
            ],

        ]

        weeks = []
        current_date = start_date
        while current_date <= end_date:
            week_start = current_date - timedelta(days=current_date.weekday())
            week_end = week_start + timedelta(days=6)
            if week_end > end_date:
                week_end = end_date
            weeks.append((week_start, week_end))
            current_date = week_end + timedelta(days=1)

        weekly_data = {}
        for week_start, week_end in weeks:
            week_key = f"{week_start.strftime('%d-%m %B')} - {week_end.strftime('%d-%m %B')}"
            weekly_data[week_key] = {
                "total_visits": 0,
                "total_events": 0,
                "total_attendees": 0,
                "child_attendees": 0,
                "at_risk_teens": 0,
                "club_activities": 0,
                "club_participants": 0,
                "risk_teens_clubs": 0
            }

        for event in events:
            event_date = event.date
            for week_start, week_end in weeks:
                if week_start <= event_date <= week_end:
                    week_key = f"{week_start.strftime('%d-%m %B')} - {week_end.strftime('%d-%m %B')}"
                    weekly_data[week_key]["total_events"] += 1
                    break

        for attendance in attendances:
            event_date = attendance.event.date
            for week_start, week_end in weeks:
                if week_start <= event_date <= week_end:
                    week_key = f"{week_start.strftime('%d-%m %B')} - {week_end.strftime('%d-%m %B')}"
                    weekly_data[week_key]["total_attendees"] += attendance.total_attendees or 0
                    weekly_data[week_key]["child_attendees"] += attendance.child_attendees or 0
                    weekly_data[week_key]["at_risk_teens"] += attendance.at_risk_teens or 0
                    break

        total_visits = 0
        total_events = 0
        total_attendees = 0
        total_child_attendees = 0
        total_risk_teens = 0
        total_club_activities = 0
        total_club_participants = 0
        total_risk_teens_clubs = 0

        for week_key, data in weekly_data.items():
            club_info = f"{data['club_activities']}/{data['club_participants']}/{data['risk_teens_clubs']}" if data['club_activities'] > 0 else "-"
            table.append([
                week_key,
                data['total_visits'],
                data['total_events'],
                data['total_attendees'],
                data['child_attendees'],
                data['at_risk_teens'],
                club_info
            ])
            total_visits += data['total_visits']
            total_events += data['total_events']
            total_attendees += data['total_attendees']
            total_child_attendees += data['child_attendees']
            total_risk_teens += data['at_risk_teens']
            total_club_activities += data['club_activities']
            total_club_participants += data['club_participants']
            total_risk_teens_clubs += data['risk_teens_clubs']

        table.append([
            "ИТОГО по ЦБС",
            total_visits,
            total_events,
            total_attendees,
            total_child_attendees,
            total_risk_teens,
            f"{total_club_activities}/{total_club_participants}/{total_risk_teens_clubs}" if total_club_activities > 0 else "-"
        ])

        col_widths = [40, 30, 30, 30, 30, 30, 40]
        return {'header': header, 'table': table, 'col_widths': col_widths}

    def generate_monthly_by_months_report(self, events, attendances, start_date, end_date, institution_name, direction_name, audience_name, format_name):
        header = [
            "Ежемесячный отчёт (по месяцам) по посещениям и массовой работе",
            f"Период: {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}",
            f"Учреждение: {institution_name}",
            f"Направление: {direction_name}",
            f"Аудитория: {audience_name}",
            f"Формат: {format_name}"
        ]

        table = [
            [
                "Месяц",
                "Количество посещений всего по библиотеке",
                "Проведено мероприятий",
                "Обслужено всего чел.",
                "В т.ч. детей",
                "В т.ч. подростков группы риска",
                "Кружки/участники/подростки группы риска"
            ],

        ]

        MONTHS_RU = {
            "january": "Январь",
            "february": "Февраль",
            "march": "Март",
            "april": "Апрель",
            "may": "Май",
            "june": "Июнь",
            "july": "Июль",
            "august": "Август",
            "september": "Сентябрь",
            "october": "Октябрь",
            "november": "Ноябрь",
            "december": "Декабрь"
        }

        months = {}
        current_date = start_date
        while current_date <= end_date:
            month_key = current_date.strftime("%B").lower()
            if month_key not in months:
                months[month_key] = {
                    "total_visits": 0,
                    "total_events": 0,
                    "total_attendees": 0,
                    "child_attendees": 0,
                    "at_risk_teens": 0,
                    "club_activities": 0,
                    "club_participants": 0,
                    "risk_teens_clubs": 0
                }
            current_date += timedelta(days=30)

        for event in events:
            month_key = event.date.strftime("%B").lower()
            if month_key in months:
                months[month_key]["total_events"] += 1

        for attendance in attendances:
            month_key = attendance.event.date.strftime("%B").lower()
            if month_key in months:
                months[month_key]["total_attendees"] += attendance.total_attendees or 0
                months[month_key]["child_attendees"] += attendance.child_attendees or 0
                months[month_key]["at_risk_teens"] += attendance.at_risk_teens or 0

        total_visits = 0
        total_events = 0
        total_attendees = 0
        total_child_attendees = 0
        total_risk_teens = 0
        total_club_activities = 0
        total_club_participants = 0
        total_risk_teens_clubs = 0

        for month_key, data in months.items():
            month_ru = MONTHS_RU[month_key]
            club_info = f"{data['club_activities']}/{data['club_participants']}/{data['risk_teens_clubs']}" if data['club_activities'] > 0 else "-"
            table.append([
                month_ru,
                data['total_visits'],
                data['total_events'],
                data['total_attendees'],
                data['child_attendees'],
                data['at_risk_teens'],
                club_info
            ])
            total_visits += data['total_visits']
            total_events += data['total_events']
            total_attendees += data['total_attendees']
            total_child_attendees += data['child_attendees']
            total_risk_teens += data['at_risk_teens']
            total_club_activities += data['club_activities']
            total_club_participants += data['club_participants']
            total_risk_teens_clubs += data['risk_teens_clubs']

        table.append([
            "ИТОГО по ЦБС",
            total_visits,
            total_events,
            total_attendees,
            total_child_attendees,
            total_risk_teens,
            f"{total_club_activities}/{total_club_participants}/{total_risk_teens_clubs}" if total_club_activities > 0 else "-"
        ])

        col_widths = [40, 30, 30, 30, 30, 30, 40]
        return {'header': header, 'table': table, 'col_widths': col_widths}

    def generate_digital_indicators_by_directions_report(self, events, attendances, start_date, end_date, institution_name, direction_name, audience_name, format_name):
        header = [
            "Цифровые показатели (по направлениям) по посещениям и массовой работе",
            f"Период: {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}",
            f"Учреждение: {institution_name}",
            f"Направление: {direction_name}",
            f"Аудитория: {audience_name}",
            f"Формат: {format_name}"
        ]

        table = [
            [
                "Направления",
                "Количество массовых мероприятий, всего",
                "Посещение на массовых мероприятиях",
                "Количество массовых мероприятий для детей",
                "Посещение на детских массовых мероприятиях",
                "Количество культ-досуговых мероприятий",
                "Посещение на культ-досуговых мероприятиях",
                "Количество информ-просветительских мероприятий",
                "Посещение на информ-просветительских мероприятиях"
            ],

        ]

        predefined_directions = [
            "Содействие духовному развитию личности и нравственному воспитанию",
            "Педагогика, Этика, Культура поведения",
            "Летние чтения – 202__",
            "Пропаганда художественной литературы",
            "Эстетическое воспитание",
            "В помощь школьной программе, День знаний",
            "Продвижение исторических знаний",
            "Патриотическое воспитание",
            "Формирование правовой культуры",
            "Развитие толерантности и культуры межнационального общения",
            "Здоровый образ жизни",
            "Спорт",
            "Молодежная политика. Социализация личности. Профориентация",
            "Наука и техника.",
            "Экологическое просвещение",
            "Краеведение. Градоведение",
            "Мероприятия по формированию информационной культуры пользователей"
        ]

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
                    elif event.classification.name == "Информ-просветительских":
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

        col_widths = [60, 30, 30, 30, 30, 30, 30, 30, 30]
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
                    record = session.query(ActivityDirection).filter(EventClassification.id == record_id).first()
                elif table_name == "Типы мероприятий":
                    record = session.query(EventType).filter(EventType.id == record_id).first()
                elif table_name == "Аудитории":
                    record = session.query(TargetAudience).filter(TargetAudience.id == record_id).first()
                elif table_name == "Места проведения":
                    record = session.query(Venue).filter(Venue.id == record_id).first()
                else:
                    QMessageBox.warning(self, "Ошибка", "Неизвестный справочник")
                    return

                if not record:
                    QMessageBox.warning(self, "Ошибка", "Запись не найдена")
                    return

                from dialogs.edit_record_dialog import EditRecordDialog
                dialog = EditRecordDialog(self, table_name, record, session)
                if dialog.exec():
                    self.refresh_table()
                    self.refresh_combos()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось открыть диалог редактирования: {str(e)}")

    def delete_record(self):
        selected_rows = self.admin_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Предупреждение", "Выберите запись для удаления")
            return

        row = selected_rows[0].row()
        table_name = self.table_selector.currentText()
        reply = QMessageBox.question(self, "Подтверждение", "Вы уверены, что хотите удалить эту запись?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
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
                        QMessageBox.warning(self, "Ошибка", "Неизвестный справочник")
                        return

                    if record:
                        session.delete(record)
                        session.commit()
                        QMessageBox.information(self, "Успех", "Запись удалена")
                        self.refresh_table()
                        self.refresh_combos()
                    else:
                        raise ValueError("Запись не найдена")
                except Exception as e:
                    session.rollback()
                    QMessageBox.critical(self, "Ошибка", f"Не удалось удалить запись: {str(e)}")

    def refresh_table(self):
        with get_session() as session:
            try:
                table_name = self.table_selector.currentText()
                if table_name == "Расшифровка":
                    records = session.query(Decoding).all()
                    self.admin_table.setColumnCount(2)
                    self.admin_table.setHorizontalHeaderLabels(["Полное название", "Краткое название"])
                    self.admin_table.setRowCount(len(records))
                    for row, record in enumerate(records):
                        item0 = QTableWidgetItem(record.full_name or "")
                        item0.setData(Qt.UserRole, record.id)
                        self.admin_table.setItem(row, 0, item0)
                        self.admin_table.setItem(row, 1, QTableWidgetItem(record.short_name or ""))

                elif table_name == "Учреждение":
                    records = session.query(Institution).all()
                    self.admin_table.setColumnCount(3)
                    self.admin_table.setHorizontalHeaderLabels(["Название", "Расшифровка", "Пользователь"])
                    self.admin_table.setRowCount(len(records))
                    for row, record in enumerate(records):
                        item0 = QTableWidgetItem(record.name or "")
                        item0.setData(Qt.UserRole, record.id)
                        self.admin_table.setItem(row, 0, item0)
                        self.admin_table.setItem(row, 1, QTableWidgetItem(record.decoding.full_name if record.decoding else ""))
                        self.admin_table.setItem(row, 2, QTableWidgetItem(record.user.username if record.user else ""))

                elif table_name == "Пользователь":
                    records = session.query(User).all()
                    self.admin_table.setColumnCount(2)
                    self.admin_table.setHorizontalHeaderLabels(["Имя пользователя", "Роль"])
                    self.admin_table.setRowCount(len(records))
                    for row, record in enumerate(records):
                        item0 = QTableWidgetItem(record.username or "")
                        item0.setData(Qt.UserRole, record.id)
                        self.admin_table.setItem(row, 0, item0)
                        self.admin_table.setItem(row, 1, QTableWidgetItem(record.role.name if record.role else ""))

                elif table_name == "Роль":
                    records = session.query(Role).all()
                    self.admin_table.setColumnCount(1)
                    self.admin_table.setHorizontalHeaderLabels(["Название"])
                    self.admin_table.setRowCount(len(records))
                    for row, record in enumerate(records):
                        item0 = QTableWidgetItem(record.name or "")
                        item0.setData(Qt.UserRole, record.id)
                        self.admin_table.setItem(row, 0, item0)

                elif table_name == "Форматы":
                    records = session.query(EventFormat).all()
                    self.admin_table.setColumnCount(1)
                    self.admin_table.setHorizontalHeaderLabels(["Название"])
                    self.admin_table.setRowCount(len(records))
                    for row, record in enumerate(records):
                        item0 = QTableWidgetItem(record.name or "")
                        item0.setData(Qt.UserRole, record.id)
                        self.admin_table.setItem(row, 0, item0)

                elif table_name == "Классификации":
                    records = session.query(EventClassification).all()
                    self.admin_table.setColumnCount(1)
                    self.admin_table.setHorizontalHeaderLabels(["Название"])
                    self.admin_table.setRowCount(len(records))
                    for row, record in enumerate(records):
                        item0 = QTableWidgetItem(record.name or "")
                        item0.setData(Qt.UserRole, record.id)
                        self.admin_table.setItem(row, 0, item0)

                elif table_name == "Направления":
                    records = session.query(ActivityDirection).all()
                    self.admin_table.setColumnCount(1)
                    self.admin_table.setHorizontalHeaderLabels(["Название"])
                    self.admin_table.setRowCount(len(records))
                    for row, record in enumerate(records):
                        item0 = QTableWidgetItem(record.name or "")
                        item0.setData(Qt.UserRole, record.id)
                        self.admin_table.setItem(row, 0, item0)

                elif table_name == "Типы мероприятий":
                    records = session.query(EventType).all()
                    self.admin_table.setColumnCount(1)
                    self.admin_table.setHorizontalHeaderLabels(["Название"])
                    self.admin_table.setRowCount(len(records))
                    for row, record in enumerate(records):
                        item0 = QTableWidgetItem(record.name or "")
                        item0.setData(Qt.UserRole, record.id)
                        self.admin_table.setItem(row, 0, item0)

                elif table_name == "Аудитории":
                    records = session.query(TargetAudience).all()
                    self.admin_table.setColumnCount(1)
                    self.admin_table.setHorizontalHeaderLabels(["Название"])
                    self.admin_table.setRowCount(len(records))
                    for row, record in enumerate(records):
                        item0 = QTableWidgetItem(record.name or "")
                        item0.setData(Qt.UserRole, record.id)
                        self.admin_table.setItem(row, 0, item0)

                elif table_name == "Места проведения":
                    records = session.query(Venue).all()
                    self.admin_table.setColumnCount(1)
                    self.admin_table.setHorizontalHeaderLabels(["Название"])
                    self.admin_table.setRowCount(len(records))
                    for row, record in enumerate(records):
                        item0 = QTableWidgetItem(record.name or "")
                        item0.setData(Qt.UserRole, record.id)
                        self.admin_table.setItem(row, 0, item0)

                self.admin_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось обновить таблицу: {str(e)}")

    def refresh_combos(self):
        with get_session() as session:
            try:
                # Обновление фильтра учреждений в таблице
                current_institution = self.institution_filter_table.currentText()
                self.institution_filter_table.clear()
                self.institution_filter_table.addItem("Все учреждения")
                institutions = session.query(Institution).all()
                self.institution_filter_table.addItems([i.name for i in institutions])
                if current_institution in ["Все учреждения"] + [i.name for i in institutions]:
                    self.institution_filter_table.setCurrentText(current_institution)

                # Обновление фильтра направлений в таблице
                current_direction = self.direction_filter_table.currentText()
                self.direction_filter_table.clear()
                self.direction_filter_table.addItem("Все направления")
                directions = session.query(ActivityDirection).all()
                self.direction_filter_table.addItems([d.name for d in directions])
                if current_direction in ["Все направления"] + [d.name for d in directions]:
                    self.direction_filter_table.setCurrentText(current_direction)

                # Обновление фильтра аудиторий в таблице
                current_audience = self.audience_filter_table.currentText()
                self.audience_filter_table.clear()
                self.audience_filter_table.addItem("Все аудитории")
                audiences = session.query(TargetAudience).all()
                self.audience_filter_table.addItems([a.name for a in audiences])
                if current_audience in ["Все аудитории"] + [a.name for a in audiences]:
                    self.audience_filter_table.setCurrentText(current_audience)

                # Обновление фильтра форматов в таблице
                current_format = self.format_filter_table.currentText()
                self.format_filter_table.clear()
                self.format_filter_table.addItem("Все форматы")
                formats = session.query(EventFormat).all()
                self.format_filter_table.addItems([f.name for f in formats])
                if current_format in ["Все форматы"] + [f.name for f in formats]:
                    self.format_filter_table.setCurrentText(current_format)

                # Обновление фильтра учреждений в отчётах
                current_institution_report = self.institution_filter.currentText()
                self.institution_filter.clear()
                self.institution_filter.addItem("Все учреждения")
                institutions = session.query(Institution).all()
                self.institution_filter.addItems([i.name for i in institutions])
                if current_institution_report in ["Все учреждения"] + [i.name for i in institutions]:
                    self.institution_filter.setCurrentText(current_institution_report)

                # Обновление фильтра направлений в отчётах
                current_direction_report = self.direction_filter.currentText()
                self.direction_filter.clear()
                self.direction_filter.addItem("Все направления")
                directions = session.query(ActivityDirection).all()
                self.direction_filter.addItems([d.name for d in directions])
                if current_direction_report in ["Все направления"] + [d.name for d in directions]:
                    self.direction_filter.setCurrentText(current_direction_report)

                # Обновление фильтра аудиторий в отчётах
                current_audience_report = self.audience_filter.currentText()
                self.audience_filter.clear()
                self.audience_filter.addItem("Все аудитории")
                audiences = session.query(TargetAudience).all()
                self.audience_filter.addItems([a.name for a in audiences])
                if current_audience_report in ["Все аудитории"] + [a.name for a in audiences]:
                    self.audience_filter.setCurrentText(current_audience_report)

                # Обновление фильтра форматов в отчётах
                current_format_report = self.format_filter.currentText()
                self.format_filter.clear()
                self.format_filter.addItem("Все форматы")
                formats = session.query(EventFormat).all()
                self.format_filter.addItems([f.name for f in formats])
                if current_format_report in ["Все форматы"] + [f.name for f in formats]:
                    self.format_filter.setCurrentText(current_format_report)

            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось обновить выпадающие списки: {str(e)}")