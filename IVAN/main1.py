import sys
import logging
from datetime import date, timedelta
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QLineEdit, QPushButton, QListWidget, QStackedWidget, QLabel, QComboBox,
    QTableWidgetItem, QMessageBox, QDialog, QFormLayout, QDateEdit, QHeaderView,
    QTabWidget, QTableView, QGroupBox, QFileDialog, QSizePolicy, QCheckBox,
    QSpacerItem, QListWidgetItem, QMenuBar, QMenu, QInputDialog
)
from PySide6.QtCore import Qt, QDate, QTimer
from PySide6.QtGui import QIcon, QPixmap, QStandardItemModel, QStandardItem, QBrush, QColor
from sqlalchemy.orm import joinedload
from db import (
    User, Role, Unit, ProductType, DeliveryCondition, Supplier, Product, Delivery,
    ProductInDelivery, Session
)
from styles import STYLESHEET
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='app.log',
    filemode='a'
)

class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Авторизация")
        self.setWindowIcon(QIcon("./logo.svg"))
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)
        try:
            pixmap = QPixmap("logo.svg")
            logo = QLabel()
            logo.setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio))
            logo.setAlignment(Qt.AlignCenter)
            layout.addWidget(logo)
        except Exception as e:
            logging.error(f"Ошибка загрузки логотипа: {e}")
        self.username = QLineEdit()
        self.username.setPlaceholderText("Имя пользователя")
        self.username.setFixedHeight(35)
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setPlaceholderText("Пароль")
        self.password.setFixedHeight(35)
        login_button = QPushButton("Войти")
        login_button.setFixedHeight(35)
        login_button.setObjectName("login_button")
        login_button.clicked.connect(self.accept)
        layout.addWidget(QLabel("Вход"))
        layout.addWidget(self.username)
        layout.addWidget(self.password)
        layout.addWidget(login_button)

    def get_credentials(self):
        return self.username.text().strip(), self.password.text().strip()

class AddEditRecordDialog(QDialog):
    def __init__(self, table_name, record=None):
        super().__init__()
        self.setWindowTitle(f"{'Редактировать' if record else 'Добавить'} {table_name}")
        self.setWindowIcon(QIcon("./logo.svg"))
        self.table_name = table_name
        self.record = record
        layout = QFormLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        self.inputs = {}
        if table_name == "Единицы измерения":
            self.inputs['name'] = QLineEdit(record.name if record else "")
            layout.addRow("Название:", self.inputs['name'])
        elif table_name == "Типы товаров":
            self.inputs['name'] = QLineEdit(record.name if record else "")
            layout.addRow("Название:", self.inputs['name'])
        elif table_name == "Условия поставки":
            self.inputs['name'] = QLineEdit(record.name if record else "")
            layout.addRow("Название:", self.inputs['name'])
        elif table_name == "Поставщики":
            self.inputs['inn'] = QLineEdit(record.inn if record else "")
            self.inputs['name'] = QLineEdit(record.name if record else "")
            self.inputs['phone'] = QLineEdit(record.phone if record else "")
            layout.addRow("ИНН:", self.inputs['inn'])
            layout.addRow("Название:", self.inputs['name'])
            layout.addRow("Телефон:", self.inputs['phone'])
        elif table_name == "Товары":
            self.inputs['name'] = QLineEdit(record.name if record else "")
            self.inputs['unit_id'] = QComboBox()
            self.inputs['type_id'] = QComboBox()
            self.inputs['condition_id'] = QComboBox()
            with Session() as s:
                units = s.query(Unit).all()
                types = s.query(ProductType).all()
                conditions = s.query(DeliveryCondition).all()
                self.inputs['unit_id'].addItem("Выберите", None)
                for u in units:
                    self.inputs['unit_id'].addItem(u.name, u.id)
                self.inputs['type_id'].addItem("Выберите", None)
                for t in types:
                    self.inputs['type_id'].addItem(t.name, t.id)
                self.inputs['condition_id'].addItem("Выберите", None)
                for c in conditions:
                    self.inputs['condition_id'].addItem(c.name, c.id)
                if record:
                    self.inputs['unit_id'].setCurrentIndex(self.inputs['unit_id'].findData(record.unit_id))
                    self.inputs['type_id'].setCurrentIndex(self.inputs['type_id'].findData(record.type_id))
                    self.inputs['condition_id'].setCurrentIndex(self.inputs['condition_id'].findData(record.condition_id))
            layout.addRow("Название:", self.inputs['name'])
            layout.addRow("Ед. изм.:", self.inputs['unit_id'])
            layout.addRow("Тип:", self.inputs['type_id'])
            layout.addRow("Условие:", self.inputs['condition_id'])
        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(self.accept)
        layout.addRow(save_button)

    def get_data(self):
        data = {}
        for key, widget in self.inputs.items():
            if isinstance(widget, QLineEdit):
                data[key] = widget.text().strip()
            elif isinstance(widget, QComboBox):
                data[key] = widget.currentData()
        return data

class AddEditDeliveryDialog(QDialog):
    def __init__(self, delivery=None):
        super().__init__()
        self.setWindowTitle("Добавить поставку" if not delivery else "Редактировать поставку")
        self.setWindowIcon(QIcon("./logo.svg"))
        self.setMinimumSize(1000, 900)
        self.delivery = delivery
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        form_layout = QFormLayout()
        self.supplier = QComboBox()
        self.supplier.setMinimumWidth(300)
        self.supplier.setFixedHeight(35)
        self.planned_date = QDateEdit(QDate.currentDate())
        self.planned_date.setCalendarPopup(True)
        self.planned_date.setFixedHeight(35)
        self.actual_date = QDateEdit(QDate.currentDate())
        self.actual_date.setCalendarPopup(True)
        self.actual_date.setEnabled(False)
        self.actual_date.setFixedHeight(35)
        self.actual_date_check = QCheckBox("Указать факт. дату")
        self.doc_number = QLineEdit()
        self.doc_number.setFixedHeight(35)
        self.doc_date = QDateEdit(QDate.currentDate())
        self.doc_date.setCalendarPopup(True)
        self.doc_date.setFixedHeight(35)
        with Session() as s:
            suppliers = s.query(Supplier).all()
            self.supplier.addItem("Выберите", None)
            for sup in suppliers:
                self.supplier.addItem(sup.name, sup.id)
            if delivery:
                self.supplier.setCurrentIndex(self.supplier.findData(delivery.supplier_id))
                self.planned_date.setDate(delivery.planned_date or QDate.currentDate())
                if delivery.actual_date:
                    self.actual_date.setDate(delivery.actual_date)
                    self.actual_date_check.setChecked(True)
                    self.actual_date.setEnabled(True)
                self.doc_number.setText(delivery.doc_number or "")
                self.doc_date.setDate(delivery.doc_date or QDate.currentDate())
        form_layout.addRow("Поставщик:", self.supplier)
        form_layout.addRow("План. дата:", self.planned_date)
        form_layout.addRow("", self.actual_date_check)
        form_layout.addRow("Факт. дата:", self.actual_date)
        form_layout.addRow("Номер док.:", self.doc_number)
        form_layout.addRow("Дата док.:", self.doc_date)
        layout.addLayout(form_layout)
        self.actual_date_check.toggled.connect(self.actual_date.setEnabled)
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(5)
        self.products_table.setHorizontalHeaderLabels([
            "Товар", "План. кол-во", "План. цена", "Факт. кол-во", "Факт. цена"
        ])
        self.products_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.products_table.setColumnWidth(0, 250)
        layout.addWidget(self.products_table)
        if delivery:
            with Session() as s:
                products = s.query(ProductInDelivery).filter_by(delivery_id=delivery.id).all()
                self.products_table.setRowCount(len(products))
                for row, pid in enumerate(products):
                    combo = QComboBox()
                    combo.setMinimumWidth(250)
                    combo.setFixedHeight(35)
                    with Session() as s:
                        all_products = s.query(Product).all()
                        combo.addItem("Выберите", None)
                        for p in all_products:
                            combo.addItem(p.name, p.id)
                        combo.setCurrentIndex(combo.findData(pid.product_id))
                    self.products_table.setCellWidget(row, 0, combo)
                    self.products_table.setItem(row, 1, QTableWidgetItem(str(pid.planned_quantity or 0)))
                    self.products_table.setItem(row, 2, QTableWidgetItem(f"{pid.planned_price or 0}"))
                    self.products_table.setItem(row, 3, QTableWidgetItem(str(pid.actual_quantity or 0)))
                    self.products_table.setItem(row, 4, QTableWidgetItem(f"{pid.actual_price or 0}"))
                    self.products_table.setRowHeight(row, 50)
                for row in range(self.products_table.rowCount()):
                    self.products_table.setRowHeight(row, 50)
        buttons_layout = QHBoxLayout()
        add_product = QPushButton("Добавить товар")
        add_product.setObjectName("add_button")
        add_product.clicked.connect(self.add_product_row)
        remove_product = QPushButton("Удалить товар")
        remove_product.setObjectName("delete_button")
        remove_product.clicked.connect(self.remove_product_row)
        buttons_layout.addWidget(add_product)
        buttons_layout.addWidget(remove_product)
        layout.addLayout(buttons_layout)
        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(self.accept)
        layout.addWidget(save_button)

    def add_product_row(self):
        row = self.products_table.rowCount()
        self.products_table.insertRow(row)
        combo = QComboBox()
        combo.setMinimumWidth(250)
        combo.setFixedHeight(35)
        with Session() as s:
            products = s.query(Product).all()
            combo.addItem("Выберите", None)
            for p in products:
                combo.addItem(p.name, p.id)
        self.products_table.setCellWidget(row, 0, combo)
        self.products_table.setItem(row, 1, QTableWidgetItem("0"))
        self.products_table.setItem(row, 2, QTableWidgetItem("0"))
        self.products_table.setItem(row, 3, QTableWidgetItem("0"))
        self.products_table.setItem(row, 4, QTableWidgetItem("0"))
        self.products_table.setRowHeight(row, 50)

    def remove_product_row(self):
        rows = self.products_table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.warning(self, "Ошибка", "Выберите строку")
            return
        for row in sorted([r.row() for r in rows], reverse=True):
            self.products_table.removeRow(row)

    def get_data(self):
        products = []
        for row in range(self.products_table.rowCount()):
            combo = self.products_table.cellWidget(row, 0)
            product_id = combo.currentData()
            if not product_id:
                continue
            try:
                planned_qty = int(self.products_table.item(row, 1).text() or 0)
                planned_price = int(self.products_table.item(row, 2).text() or 0)
                actual_qty = int(self.products_table.item(row, 3).text() or 0)
                actual_price = int(self.products_table.item(row, 4).text() or 0)
            except ValueError as e:
                logging.error(f"Ошибка парсинга данных таблицы: {e}")
                planned_qty, planned_price, actual_qty, actual_price = 0, 0, 0, 0
            products.append({
                'product_id': product_id,
                'planned_quantity': planned_qty,
                'planned_price': planned_price,
                'actual_quantity': actual_qty,
                'actual_price': actual_price
            })
        return {
            'supplier_id': self.supplier.currentData(),
            'planned_date': self.planned_date.date().toPython(),
            'actual_date': self.actual_date.date().toPython() if self.actual_date_check.isChecked() else None,
            'doc_number': self.doc_number.text().strip(),
            'doc_date': self.doc_date.date().toPython(),
            'products': products
        }

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки")
        self.setWindowIcon(QIcon("./logo.svg"))
        self.setMinimumSize(600, 400)
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Вкладка "Назначение ролей"
        role_tab = QWidget()
        role_layout = QVBoxLayout(role_tab)
        role_layout.setSpacing(10)
        role_layout.setContentsMargins(20, 20, 20, 20)
        add_user_btn = QPushButton("Добавить сотрудника")
        add_user_btn.setFixedHeight(35)
        add_user_btn.clicked.connect(self.add_employee)
        role_layout.addWidget(add_user_btn)
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(3)
        self.user_table.setHorizontalHeaderLabels(["Имя пользователя", "Роль", "ID роли"])
        self.user_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.user_table.setEditTriggers(QTableWidget.NoEditTriggers)
        role_layout.addWidget(self.user_table)
        self.tabs.addTab(role_tab, "Назначение ролей")
        self.update_user_table()

        # Вкладка "Статистика"
        stats_tab = QWidget()
        stats_layout = QVBoxLayout(stats_tab)
        stats_layout.setSpacing(10)
        stats_layout.setContentsMargins(20, 20, 20, 20)
        self.stats_label = QLabel()
        stats_layout.addWidget(self.stats_label)
        stats_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.tabs.addTab(stats_tab, "Статистика")
        self.update_statistics()

        # Вкладка "О приложении"
        about_tab = QWidget()
        about_layout = QVBoxLayout(about_tab)
        about_layout.setSpacing(10)
        about_layout.setContentsMargins(20, 20, 20, 20)
        about_text = (
            "Название: Deliveries\n"
            "Версия: 1.0.0\n"
            "Разработчик: xAI\n"
            "Дата выпуска: 02.06.2025"
        )
        about_label = QLabel(about_text)
        about_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        about_layout.addWidget(about_label)
        about_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.tabs.addTab(about_tab, "О приложении")

        close_button = QPushButton("Закрыть")
        close_button.setFixedHeight(35)
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

    def add_employee(self):
        username, ok = QInputDialog.getText(self, "Добавить сотрудника", "Имя пользователя:")
        if not ok or not username.strip():
            return
        password, ok = QInputDialog.getText(self, "Добавить сотрудника", "Пароль:", QLineEdit.Password)
        if not ok or not password.strip():
            return
        with Session() as s:
            try:
                if s.query(User).filter_by(username=username).first():
                    QMessageBox.critical(self, "Ошибка", "Пользователь с таким именем уже существует")
                    return
                employee_role = s.query(Role).filter_by(name='employee').first()
                if not employee_role:
                    QMessageBox.critical(self, "Ошибка", "Роль 'employee' не найдена в базе данных")
                    return
                s.add(User(
                    username=username,
                    password=password,
                    role_id=employee_role.id
                ))
                s.commit()
                self.update_user_table()
                logging.info(f"Добавлен сотрудник: {username}")
                QMessageBox.information(self, "Успех", "Сотрудник успешно добавлен")
            except Exception as e:
                s.rollback()
                logging.error(f"Ошибка добавления сотрудника: {e}")
                QMessageBox.critical(self, "Ошибка", f"Не удалось добавить сотрудника: {str(e)}")

    def update_user_table(self):
        with Session() as s:
            users = s.query(User).options(joinedload(User.role)).all()
            self.user_table.setRowCount(len(users))
            for row, user in enumerate(users):
                self.user_table.setItem(row, 0, QTableWidgetItem(user.username))
                self.user_table.setItem(row, 1, QTableWidgetItem(user.role.name if user.role else ""))
                self.user_table.setItem(row, 2, QTableWidgetItem(str(user.role_id or "")))
                self.user_table.setRowHeight(row, 50)

    def update_statistics(self):
        with Session() as s:
            delivery_count = s.query(Delivery).count()
            product_count = s.query(ProductInDelivery).count()
            stats_text = (
                f"Общее количество поставок: {delivery_count}\n"
                f"Общее количество товаров в поставках: {product_count}"
            )
            self.stats_label.setText(stats_text)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Deliveries")
        self.setWindowIcon(QIcon("logo.svg"))
        self.current_user = None
        self.current_report = None
        self.report_widget = None
        self.show_login_dialog()

    def show_login_dialog(self):
        self.current_user = None  # Очистка текущего пользователя
        dialog = LoginDialog()
        if dialog.exec_():
            username, password = dialog.get_credentials()
            with Session() as s:
                user = s.query(User).options(joinedload(User.role)).filter_by(username=username, password=password).first()
                if user:
                    if not user.role:
                        # Принудительно загрузим роль
                        user.role = s.query(Role).get(user.role_id)
                        if not user.role:
                            logging.error(f"Роль с role_id={user.role_id} не найдена для пользователя {username}")
                            QMessageBox.critical(self, "Ошибка", "Роль пользователя не найдена")
                            return
                    self.current_user = user
                    logging.info(f"Авторизация: username={username}, role_id={user.role_id}, role_name={user.role.name}")
                    self.setup_ui()
                else:
                    QMessageBox.critical(self, "Ошибка", "Неверный логин или пароль")
                    self.show_login_dialog()

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        # Меню настроек для админа
        logging.info(f"Проверка роли: role_name={self.current_user.role.name if self.current_user.role else 'None'}")
        if self.current_user.role and self.current_user.role.name.lower() == 'admin':
            menubar = self.menuBar()
            settings_menu = menubar.addMenu("Настройки")
            settings_action = settings_menu.addAction("Открыть настройки")
            settings_action.triggered.connect(self.open_settings)
            logging.info("Добавлено меню настроек для администратора")
        else:
            logging.info("Меню настроек не добавлено: пользователь не администратор")

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self.on_tab_changed)
        left_layout.addWidget(self.tabs)

        # Вкладка "Справочники" только для админа
        if self.current_user.role and self.current_user.role.name.lower() == 'admin':
            ref_tab = QWidget()
            ref_layout = QVBoxLayout(ref_tab)
            self.ref_list = QListWidget()
            self.ref_list.addItems(["Единицы измерения", "Типы товаров", "Условия поставки", "Поставщики", "Товары"])
            self.ref_list.currentItemChanged.connect(self.show_reference)
            ref_layout.addWidget(self.ref_list)
            self.tabs.addTab(ref_tab, "Справочники")
            logging.info("Добавлена вкладка Справочники для администратора")
        else:
            logging.info("Вкладка Справочники не добавлена: пользователь не администратор")

        # Вкладка "Поставки"
        delivery_tab = QWidget()
        delivery_layout = QVBoxLayout(delivery_tab)
        filters_group = QGroupBox("")
        filters_group.setObjectName("delivery_filters")
        filters_group.setFixedHeight(200)
        filters_group.setMinimumWidth(350)
        filters_layout = QVBoxLayout(filters_group)
        filters_layout.setSpacing(15)
        filters_layout.setContentsMargins(20, 25, 20, 20)
        start_row = QHBoxLayout()
        start_label = QLabel("Дата с:")
        start_label.setFixedWidth(80)
        start_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        start_label.setStyleSheet("padding-right: 10px;")
        self.delivery_start_date = QDateEdit(QDate.currentDate().addMonths(-1))
        self.delivery_start_date.setCalendarPopup(True)
        self.delivery_start_date.setFixedHeight(35)
        start_row.addWidget(start_label)
        start_row.addWidget(self.delivery_start_date)
        filters_layout.addLayout(start_row)
        end_row = QHBoxLayout()
        end_label = QLabel("по:")
        end_label.setFixedWidth(80)
        end_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        end_label.setStyleSheet("padding-right: 10px;")
        self.delivery_end_date = QDateEdit(QDate.currentDate())
        self.delivery_end_date.setCalendarPopup(True)
        self.delivery_end_date.setFixedHeight(35)
        end_row.addWidget(end_label)
        end_row.addWidget(self.delivery_end_date)
        filters_layout.addLayout(end_row)
        supplier_row = QHBoxLayout()
        supplier_label = QLabel("Поставщик:")
        supplier_label.setFixedWidth(80)
        supplier_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        supplier_label.setStyleSheet("padding-right: 10px;")
        self.delivery_supplier_filter = QComboBox()
        self.delivery_supplier_filter.setFixedHeight(35)
        self.delivery_supplier_filter.setMinimumWidth(300)
        with Session() as s:
            suppliers = s.query(Supplier).all()
            self.delivery_supplier_filter.addItem("Все", None)
            for sup in suppliers:
                self.delivery_supplier_filter.addItem(sup.name, sup.id)
        supplier_row.addWidget(supplier_label)
        supplier_row.addWidget(self.delivery_supplier_filter)
        filters_layout.addLayout(supplier_row)
        delivery_layout.addWidget(filters_group)
        self.delivery_list = QListWidget()
        self.delivery_list.currentItemChanged.connect(self.show_delivery)
        delivery_layout.addWidget(self.delivery_list)
        add_delivery = QPushButton("Добавить поставку")
        add_delivery.setObjectName("add_button")
        add_delivery.clicked.connect(self.add_delivery)
        delivery_layout.addWidget(add_delivery)
        self.delivery_start_date.dateChanged.connect(self.update_deliveries)
        self.delivery_end_date.dateChanged.connect(self.update_deliveries)
        self.delivery_supplier_filter.currentIndexChanged.connect(self.update_deliveries)
        self.tabs.addTab(delivery_tab, "Поставки")

        # Вкладка "Отчёты"
        report_tab = QWidget()
        report_layout = QHBoxLayout(report_tab)
        filters = QWidget()
        filters_layout = QVBoxLayout(filters)
        filters_group = QGroupBox("")
        filters_group.setObjectName("report_filters")
        filters_group.setFixedHeight(200)
        filters_group.setMinimumWidth(350)
        filters_group_layout = QVBoxLayout(filters_group)
        filters_group_layout.setSpacing(15)
        filters_group_layout.setContentsMargins(20, 25, 20, 20)
        start_row = QHBoxLayout()
        start_label = QLabel("Дата с:")
        start_label.setFixedWidth(80)
        start_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        start_label.setStyleSheet("padding-right: 10px;")
        self.report_start_date = QDateEdit(QDate.currentDate().addMonths(-1))
        self.report_start_date.setCalendarPopup(True)
        self.report_start_date.setFixedHeight(35)
        start_row.addWidget(start_label)
        start_row.addWidget(self.report_start_date)
        filters_group_layout.addLayout(start_row)
        end_row = QHBoxLayout()
        end_label = QLabel("по:")
        end_label.setFixedWidth(80)
        end_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        end_label.setStyleSheet("padding-right: 10px;")
        self.report_end_date = QDateEdit(QDate.currentDate())
        self.report_end_date.setCalendarPopup(True)
        self.report_end_date.setFixedHeight(35)
        end_row.addWidget(end_label)
        end_row.addWidget(self.report_end_date)
        filters_group_layout.addLayout(end_row)
        supplier_row = QHBoxLayout()
        supplier_label = QLabel("Поставщик:")
        supplier_label.setFixedWidth(80)
        supplier_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        supplier_label.setStyleSheet("padding-right: 10px;")
        self.report_supplier_filter = QComboBox()
        self.report_supplier_filter.setFixedHeight(35)
        self.report_supplier_filter.setMinimumWidth(300)
        with Session() as s:
            suppliers = s.query(Supplier).all()
            self.report_supplier_filter.addItem("Все", None)
            for sup in suppliers:
                self.report_supplier_filter.addItem(sup.name, sup.id)
        supplier_row.addWidget(supplier_label)
        supplier_row.addWidget(self.report_supplier_filter)
        filters_group_layout.addLayout(supplier_row)
        filters_layout.addWidget(filters_group)
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        planned_btn = QPushButton("Плановые")
        planned_btn.setMinimumWidth(120)
        planned_btn.setFixedHeight(35)
        planned_btn.clicked.connect(lambda: self.generate_report("planned"))
        buttons_layout.addWidget(planned_btn)
        completed_btn = QPushButton("Выполненные")
        completed_btn.setMinimumWidth(120)
        completed_btn.setFixedHeight(35)
        completed_btn.clicked.connect(lambda: self.generate_report("completed"))
        buttons_layout.addWidget(completed_btn)
        detailed_btn = QPushButton("Детализация")
        detailed_btn.setMinimumWidth(120)
        detailed_btn.setFixedHeight(35)
        detailed_btn.clicked.connect(lambda: self.generate_report("detailed"))
        buttons_layout.addWidget(detailed_btn)
        filters_layout.addLayout(buttons_layout)
        filters_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        report_layout.addWidget(filters, 1)
        self.report_view = QTableView()
        self.report_widget = QWidget()
        report_widget_layout = QVBoxLayout(self.report_widget)
        preview_group = QGroupBox("")
        preview_group.setObjectName("report_preview")
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.addWidget(self.report_view)
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        save_report = QPushButton("Сохранить отчёт")
        save_report.setMinimumWidth(150)
        save_report.setFixedHeight(35)
        save_report.clicked.connect(self.save_report)
        save_layout.addWidget(save_report)
        preview_layout.addLayout(save_layout)
        report_widget_layout.addWidget(preview_group)
        report_layout.addWidget(self.report_widget, 2)
        self.tabs.addTab(report_tab, "Отчёты")
        main_layout.addWidget(left_panel, 1)
        self.right_panel = QStackedWidget()
        main_layout.addWidget(self.right_panel, 3)
        self.right_panel.addWidget(QWidget())
        self.update_deliveries()

        # Таймер для уведомлений
        self.notification_timer = QTimer(self)
        self.notification_timer.timeout.connect(self.show_upcoming_deliveries_notification)
        self.notification_timer.start(3600 * 1000)  # Каждые 60 минут
        self.show_upcoming_deliveries_notification()

    def show_upcoming_deliveries_notification(self):
        today = date.today()
        in_three_days = today + timedelta(days=3)
        with Session() as s:
            upcoming_deliveries = s.query(Delivery).options(joinedload(Delivery.supplier)).filter(
                Delivery.planned_date >= today,
                Delivery.planned_date <= in_three_days,
                Delivery.actual_date.is_(None)
            ).all()
            if upcoming_deliveries:
                message = "Предстоящие поставки в ближайшие 3 дня:\n\n"
                for delivery in upcoming_deliveries:
                    supplier_name = delivery.supplier.name if delivery.supplier else "Неизвестно"
                    planned_date = delivery.planned_date.strftime("%d.%m.%Y") if delivery.planned_date else "-"
                    doc_number = delivery.doc_number or "-"
                    message += f"• {supplier_name} — {planned_date} (Документ: {doc_number})\n"
                QMessageBox.information(self, "Уведомление о поставках", message)
                logging.info(f"Показано уведомление о {len(upcoming_deliveries)} предстоящих поставках")
            else:
                logging.info("Нет предстоящих поставок для уведомления")

    def open_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec_()

    def on_tab_changed(self, index):
        if self.tabs.tabText(index) == "Отчёты":
            if self.right_panel.count() > 1:
                self.right_panel.removeWidget(self.right_panel.widget(1))
            self.right_panel.addWidget(self.report_widget)
            self.right_panel.setCurrentIndex(1)
        else:
            self.report_widget.setParent(None)
            if self.right_panel.count() > 1:
                self.right_panel.setCurrentIndex(1)
            else:
                self.right_panel.setCurrentIndex(0)

    def show_reference(self):
        item = self.ref_list.currentItem()
        if not item:
            self.right_panel.setCurrentIndex(0)
            return
        ref_type = item.text()
        widget = QWidget()
        layout = QVBoxLayout(widget)
        search_layout = QHBoxLayout()
        search = QLineEdit()
        search.setPlaceholderText("Поиск...")
        search.setFixedHeight(35)
        search_layout.addWidget(QLabel("Поиск:"))
        search_layout.addWidget(search)
        layout.addLayout(search_layout)
        table = QTableWidget()
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(table)
        buttons = QHBoxLayout()
        add_btn = QPushButton("Добавить")
        add_btn.setObjectName("add_button")
        add_btn.clicked.connect(self.add_record)
        edit_btn = QPushButton("Редактировать")
        edit_btn.setObjectName("edit_button")
        edit_btn.clicked.connect(self.edit_record)
        delete_btn = QPushButton("Удалить")
        delete_btn.setObjectName("delete_button")
        delete_btn.clicked.connect(self.delete_record)
        buttons.addWidget(add_btn)
        buttons.addWidget(edit_btn)
        buttons.addWidget(delete_btn)
        layout.addLayout(buttons)

        def update_table():
            search_text = search.text().lower()
            with Session() as s:
                if ref_type == "Единицы измерения":
                    records = s.query(Unit).all()
                    table.setColumnCount(1)
                    table.setHorizontalHeaderLabels(["Название"])
                    filtered = [r for r in records if not search_text or search_text in (r.name or "").lower()]
                    table.setRowCount(len(filtered))
                    for row, r in enumerate(filtered):
                        item = QTableWidgetItem(r.name or "")
                        item.setData(Qt.UserRole, r.id)
                        table.setItem(row, 0, item)
                        table.setRowHeight(row, 50)
                elif ref_type == "Типы товаров":
                    records = s.query(ProductType).all()
                    table.setColumnCount(1)
                    table.setHorizontalHeaderLabels(["Название"])
                    filtered = [r for r in records if not search_text or search_text in (r.name or "").lower()]
                    table.setRowCount(len(filtered))
                    for row, r in enumerate(filtered):
                        item = QTableWidgetItem(r.name or "")
                        item.setData(Qt.UserRole, r.id)
                        table.setItem(row, 0, item)
                        table.setRowHeight(row, 50)
                elif ref_type == "Условия поставки":
                    records = s.query(DeliveryCondition).all()
                    table.setColumnCount(1)
                    table.setHorizontalHeaderLabels(["Название"])
                    filtered = [r for r in records if not search_text or search_text in (r.name or "").lower()]
                    table.setRowCount(len(filtered))
                    for row, r in enumerate(filtered):
                        item = QTableWidgetItem(r.name or "")
                        item.setData(Qt.UserRole, r.id)
                        table.setItem(row, 0, item)
                        table.setRowHeight(row, 50)
                elif ref_type == "Поставщики":
                    records = s.query(Supplier).all()
                    table.setColumnCount(3)
                    table.setHorizontalHeaderLabels(["ИНН", "Название", "Телефон"])
                    filtered = [r for r in records if not search_text or
                                search_text in (r.inn or "").lower() or
                                search_text in (r.name or "").lower() or
                                search_text in (r.phone or "").lower()]
                    table.setRowCount(len(filtered))
                    for row, r in enumerate(filtered):
                        item = QTableWidgetItem(r.inn or "")
                        item.setData(Qt.UserRole, r.id)
                        table.setItem(row, 0, item)
                        table.setItem(row, 1, QTableWidgetItem(r.name or ""))
                        table.setItem(row, 2, QTableWidgetItem(r.phone or ""))
                        table.setRowHeight(row, 50)
                elif ref_type == "Товары":
                    records = s.query(Product).options(
                        joinedload(Product.unit),
                        joinedload(Product.type),
                        joinedload(Product.condition)
                    ).all()
                    table.setColumnCount(4)
                    table.setHorizontalHeaderLabels(["Название", "Ед. изм.", "Тип", "Условие"])
                    filtered = [r for r in records if not search_text or search_text in (r.name or "").lower()]
                    table.setRowCount(len(filtered))
                    for row, r in enumerate(filtered):
                        item = QTableWidgetItem(r.name or "")
                        item.setData(Qt.UserRole, r.id)
                        table.setItem(row, 0, item)
                        table.setItem(row, 1, QTableWidgetItem(r.unit.name if r.unit else ""))
                        table.setItem(row, 2, QTableWidgetItem(r.type.name if r.type else ""))
                        table.setItem(row, 3, QTableWidgetItem(r.condition.name if r.condition else ""))
                        table.setRowHeight(row, 50)
                table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        search.textChanged.connect(update_table)
        update_table()
        if self.right_panel.count() > 1:
            self.right_panel.removeWidget(self.right_panel.widget(1))
        self.right_panel.addWidget(widget)
        self.right_panel.setCurrentIndex(1)

    def update_deliveries(self):
        start = self.delivery_start_date.date().toPython()
        end = self.delivery_end_date.date().toPython()
        supplier_id = self.delivery_supplier_filter.currentData()
        with Session() as s:
            query = s.query(Delivery).options(joinedload(Delivery.supplier)).filter(
                Delivery.planned_date >= start,
                Delivery.planned_date <= end
            )
            if supplier_id:
                query = query.filter(Delivery.supplier_id == supplier_id)
            deliveries = query.order_by(Delivery.supplier_id.asc()).all()
            self.delivery_list.clear()
            for d in deliveries:
                supplier_name = d.supplier.name if d.supplier else "Неизвестно"
                date_str = (d.actual_date.strftime("%d.%m.%Y") if d.actual_date
                            else d.planned_date.strftime("%d.%m.%Y") if d.planned_date else "-")
                text = f"{supplier_name} - {date_str}"
                item = QListWidgetItem(text)
                item.setData(Qt.UserRole, d.id)
                if not d.actual_date:
                    item.setBackground(QBrush(QColor("#FFCCCC")))
                self.delivery_list.addItem(item)
        self.show_upcoming_deliveries_notification()

    def show_delivery(self):
        item = self.delivery_list.currentItem()
        if not item:
            self.right_panel.setCurrentIndex(0)
            return
        delivery_id = item.data(Qt.UserRole)
        widget = QWidget()
        layout = QVBoxLayout(widget)
        info = QFormLayout()
        supplier = QLabel()
        planned = QLabel()
        actual = QLabel()
        doc_num = QLabel()
        doc_date = QLabel()
        planned_cost = QLabel()
        actual_cost = QLabel()
        info.addRow("Поставщик:", supplier)
        info.addRow("План. дата:", planned)
        info.addRow("Факт. дата:", actual)
        info.addRow("Номер док.:", doc_num)
        info.addRow("Дата док.:", doc_date)
        info.addRow("План. стоимость:", planned_cost)
        info.addRow("Факт. стоимость:", actual_cost)
        layout.addLayout(info)
        buttons = QHBoxLayout()
        edit_btn = QPushButton("Редактировать")
        edit_btn.setObjectName("edit_button")
        edit_btn.clicked.connect(self.edit_delivery)
        delete_btn = QPushButton("Удалить")
        delete_btn.setObjectName("delete_button")
        delete_btn.clicked.connect(self.delete_delivery)
        buttons.addWidget(edit_btn)
        buttons.addWidget(delete_btn)
        layout.addLayout(buttons)
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Товар", "План. кол-во", "План. цена", "Факт. кол-во", "Факт. цена"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(table)
        with Session() as s:
            delivery = s.query(Delivery).options(joinedload(Delivery.supplier)).filter(
                Delivery.id == delivery_id
            ).first()
            if not delivery:
                self.right_panel.setCurrentIndex(0)
                return
            supplier.setText(delivery.supplier.name if delivery.supplier else "")
            planned.setText(delivery.planned_date.strftime("%d.%m.%Y") if delivery.planned_date else "")
            actual.setText(delivery.actual_date.strftime("%d.%m.%Y") if delivery.actual_date else "")
            doc_num.setText(delivery.doc_number or "")
            doc_date.setText(delivery.doc_date.strftime("%d.%m.%Y") if delivery.doc_date else "")
            products = s.query(ProductInDelivery).options(
                joinedload(ProductInDelivery.product)
            ).filter_by(delivery_id=delivery_id).all()
            planned_total = sum((p.planned_quantity or 0) * (p.planned_price or 0) for p in products)
            actual_total = sum((p.actual_quantity or 0) * (p.actual_price or 0) for p in products)
            planned_cost.setText(f"{planned_total}")
            actual_cost.setText(f"{actual_total}")
            table.setRowCount(len(products))
            for row, p in enumerate(products):
                item = QTableWidgetItem(p.product.name if p.product else "")
                item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                table.setItem(row, 0, item)
                item = QTableWidgetItem(str(p.planned_quantity or 0))
                item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                table.setItem(row, 1, item)
                item = QTableWidgetItem(f"{p.planned_price or 0}")
                item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                table.setItem(row, 2, item)
                item = QTableWidgetItem(str(p.actual_quantity or 0))
                item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                table.setItem(row, 3, item)
                item = QTableWidgetItem(f"{p.actual_price or 0}")
                item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                table.setItem(row, 4, item)
                table.setRowHeight(row, 50)
        if self.right_panel.count() > 1:
            self.right_panel.removeWidget(self.right_panel.widget(1))
        self.right_panel.addWidget(widget)
        self.right_panel.setCurrentIndex(1)

    def add_record(self):
        item = self.ref_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Ошибка", "Выберите справочник")
            return
        dialog = AddEditRecordDialog(item.text())
        if dialog.exec_():
            data = dialog.get_data()
            with Session() as s:
                try:
                    if item.text() == "Единицы измерения":
                        s.add(Unit(name=data['name']))
                    elif item.text() == "Типы товаров":
                        s.add(ProductType(name=data['name']))
                    elif item.text() == "Условия поставки":
                        s.add(DeliveryCondition(name=data['name']))
                    elif item.text() == "Поставщики":
                        s.add(Supplier(inn=data['inn'], name=data['name'], phone=data['phone']))
                    elif item.text() == "Товары":
                        if not all([data['unit_id'], data['type_id'], data['condition_id']]):
                            QMessageBox.critical(self, "Ошибка", "Заполните все поля")
                            return
                        s.add(Product(
                            name=data['name'],
                            unit_id=data['unit_id'],
                            type_id=data['type_id'],
                            condition_id=data['condition_id']
                        ))
                    s.commit()
                    self.show_reference()
                except Exception as e:
                    s.rollback()
                    logging.error(f"Ошибка добавления: {e}")
                    QMessageBox.critical(self, "Ошибка", f"Не удалось добавить: {str(e)}")

    def edit_record(self):
        item = self.ref_list.currentItem()
        if not item or self.right_panel.currentIndex() == 0:
            QMessageBox.warning(self, "Ошибка", "Выберите справочник")
            return
        table = self.right_panel.currentWidget().findChild(QTableWidget)
        rows = table.selectedItems()
        if not rows:
            QMessageBox.warning(self, "Ошибка", "Выберите запись")
            return
        record_id = table.item(rows[0].row(), 0).data(Qt.UserRole)
        with Session() as s:
            try:
                if item.text() == "Единицы измерения":
                    record = s.query(Unit).get(record_id)
                elif item.text() == "Типы товаров":
                    record = s.query(ProductType).get(record_id)
                elif item.text() == "Условия поставки":
                    record = s.query(DeliveryCondition).get(record_id)
                elif item.text() == "Поставщики":
                    record = s.query(Supplier).get(record_id)
                elif item.text() == "Товары":
                    record = s.query(Product).get(record_id)
                if not record:
                    QMessageBox.warning(self, "Ошибка", "Запись не найдена")
                    return
                dialog = AddEditRecordDialog(item.text(), record)
                if dialog.exec_():
                    data = dialog.get_data()
                    if item.text() == "Единицы измерения":
                        record.name = data['name']
                    elif item.text() == "Типы товаров":
                        record.name = data['name']
                    elif item.text() == "Условия поставки":
                        record.name = data['name']
                    elif item.text() == "Поставщики":
                        record.inn = data['inn']
                        record.name = data['name']
                        record.phone = data['phone']
                    elif item.text() == "Товары":
                        if not all([data['unit_id'], data['type_id'], data['condition_id']]):
                            QMessageBox.critical(self, "Ошибка", "Заполните все поля")
                            return
                        record.name = data['name']
                        record.unit_id = data['unit_id']
                        record.type_id = data['type_id']
                        record.condition_id = data['condition_id']
                    s.commit()
                    self.show_reference()
                    logging.info(f"Запись отредактирована: {item.text()}, ID={record_id}")
                else:
                    return
            except Exception as e:
                s.rollback()
                logging.error(f"Ошибка редактирования: {e}")
                QMessageBox.critical(self, "Ошибка", f"Не удалось редактировать: {str(e)}")

    def delete_record(self):
        item = self.ref_list.currentItem()
        if not item or self.right_panel.currentIndex() == 0:
            QMessageBox.warning(self, "Ошибка", "Выберите справочник")
            return
        table = self.right_panel.currentWidget().findChild(QTableWidget)
        rows = table.selectedItems()
        if not rows:
            QMessageBox.warning(self, "Ошибка", "Выберите запись")
            return
        if QMessageBox.question(self, "Подтверждение", "Удалить запись?") != QMessageBox.Yes:
            return
        record_id = table.item(rows[0].row(), 0).data(Qt.UserRole)
        with Session() as s:
            try:
                if item.text() == "Единицы измерения":
                    record = s.query(Unit).get(record_id)
                elif item.text() == "Типы товаров":
                    record = s.query(ProductType).get(record_id)
                elif item.text() == "Условия поставки":
                    record = s.query(DeliveryCondition).get(record_id)
                elif item.text() == "Поставщики":
                    record = s.query(Supplier).get(record_id)
                elif item.text() == "Товары":
                    record = s.query(Product).get(record_id)
                if record:
                    s.delete(record)
                    s.commit()
                    self.show_reference()
                    logging.info(f"Запись удалена: {item.text()}, ID={record_id}")
                else:
                    QMessageBox.warning(self, "Ошибка", "Запись не найдена")
            except Exception as e:
                s.rollback()
                logging.error(f"Ошибка удаления: {e}")
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить: {str(e)}")

    def add_delivery(self):
        dialog = AddEditDeliveryDialog()
        if dialog.exec_():
            data = dialog.get_data()
            if not data['supplier_id'] or not data['products']:
                QMessageBox.critical(self, "Ошибка", "Выберите поставщика и добавьте товары")
                return
            with Session() as s:
                try:
                    delivery = Delivery(
                        supplier_id=data['supplier_id'],
                        planned_date=data['planned_date'],
                        actual_date=data['actual_date'],
                        doc_number=data['doc_number'],
                        doc_date=data['doc_date']
                    )
                    s.add(delivery)
                    s.flush()
                    for p in data['products']:
                        s.add(ProductInDelivery(
                            delivery_id=delivery.id,
                            product_id=p['product_id'],
                            planned_quantity=p['planned_quantity'],
                            planned_price=p['planned_price'],
                            actual_quantity=p['actual_quantity'],
                            actual_price=p['actual_price']
                        ))
                    s.commit()
                    self.update_deliveries()
                    logging.info(f"Поставка добавлена: {data['doc_number']}")
                except Exception as e:
                    s.rollback()
                    logging.error(f"Ошибка добавления поставки: {e}")
                    QMessageBox.critical(self, "Ошибка", f"Не удалось добавить: {str(e)}")

    def edit_delivery(self):
        item = self.delivery_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Ошибка", "Выберите поставку")
            return
        delivery_id = item.data(Qt.UserRole)
        with Session() as s:
            try:
                delivery = s.query(Delivery).get(delivery_id)
                if not delivery:
                    QMessageBox.warning(self, "Ошибка", "Поставка не найдена")
                    return
                dialog = AddEditDeliveryDialog(delivery)
                if dialog.exec_():
                    data = dialog.get_data()
                    if not data['supplier_id'] or not data['products']:
                        QMessageBox.critical(self, "Ошибка", "Выберите поставщика и добавьте товары")
                        return
                    delivery.supplier_id = data['supplier_id']
                    delivery.planned_date = data['planned_date']
                    delivery.actual_date = data['actual_date']
                    delivery.doc_number = data['doc_number']
                    delivery.doc_date = data['doc_date']
                    s.query(ProductInDelivery).filter_by(delivery_id=delivery.id).delete()
                    for p in data['products']:
                        s.add(ProductInDelivery(
                            delivery_id=delivery.id,
                            product_id=p['product_id'],
                            planned_quantity=p['planned_quantity'],
                            planned_price=p['planned_price'],
                            actual_quantity=p['actual_quantity'],
                            actual_price=p['actual_price']
                        ))
                    s.commit()
                    self.update_deliveries()
                    self.show_delivery()
                    logging.info(f"Поставка отредактирована: ID={delivery_id}")
            except Exception as e:
                s.rollback()
                logging.error(f"Ошибка редактирования поставки: {e}")
                QMessageBox.critical(self, "Ошибка", f"Не удалось редактировать: {str(e)}")

    def delete_delivery(self):
        item = self.delivery_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Ошибка", "Выберите поставку")
            return
        if QMessageBox.question(self, "Подтверждение", "Удалить поставку?") != QMessageBox.Yes:
            return
        delivery_id = item.data(Qt.UserRole)
        with Session() as s:
            try:
                delivery = s.query(Delivery).get(delivery_id)
                if delivery:
                    s.query(ProductInDelivery).filter_by(delivery_id=delivery_id).delete()
                    s.delete(delivery)
                    s.commit()
                    self.update_deliveries()
                    self.right_panel.setCurrentIndex(0)
                    logging.info(f"Поставка удалена: ID={delivery_id}")
                else:
                    QMessageBox.warning(self, "Ошибка", "Поставка не найдена")
            except Exception as e:
                s.rollback()
                logging.error(f"Ошибка удаления поставки: {e}")
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить: {str(e)}")

    def generate_report(self, report_type):
        logging.info(f"Генерация отчёта: {report_type}")
        with Session() as s:
            try:
                start = self.report_start_date.date().toPython()
                end = self.report_end_date.date().toPython()
                supplier_id = self.report_supplier_filter.currentData()
                query = s.query(Delivery).options(joinedload(Delivery.supplier)).filter(
                    Delivery.planned_date >= start,
                    Delivery.planned_date <= end
                )
                if supplier_id:
                    query = query.filter_by(supplier_id=supplier_id)
                deliveries = query.all()
                products = s.query(ProductInDelivery).join(Delivery).filter(
                    Delivery.planned_date >= start,
                    Delivery.planned_date <= end
                ).options(joinedload(ProductInDelivery.product)).all()
                if not deliveries:
                    QMessageBox.warning(self, "Ошибка", "Нет поставок за выбранный период")
                    return
                if not products:
                    QMessageBox.warning(self, "Ошибка", "Нет товаров в поставках за выбранный период")
                    return
                deliveries_data = []
                for d in deliveries:
                    delivery_products = [
                        {
                            "name": p.product.name if p.product else "",
                            "planned_quantity": p.planned_quantity or 0,
                            "planned_price": p.planned_price or 0,
                            "actual_quantity": p.actual_quantity or 0,
                            "actual_price": p.actual_price or 0
                        }
                        for p in products if p.delivery_id == d.id
                    ]
                    if delivery_products:
                        deliveries_data.append({
                            "id": d.id,
                            "supplier_name": d.supplier.name if d.supplier else "",
                            "planned_date": d.planned_date if d.planned_date else start,
                            "actual_date": d.actual_date,
                            "doc_number": d.doc_number or "",
                            "products": delivery_products
                        })
                if not deliveries_data:
                    QMessageBox.warning(self, "Ошибка", "Нет данных для отчёта после фильтрации")
                    return
                if report_type == "planned":
                    report = self.generate_planned_report(deliveries, products, start, end)
                elif report_type == "completed":
                    report = self.generate_completed_report(deliveries, products, start, end)
                elif report_type == "detailed":
                    report = self.generate_detailed_report(deliveries, products, start, end)
                else:
                    logging.error(f"Неизвестный тип отчёта: {report_type}")
                    return
                report['deliveries_data'] = deliveries_data
                self.current_report = report
                self.display_report(report)
                logging.info(f"Отчёт сгенерирован: {report_type}")
            except Exception as e:
                logging.error(f"Ошибка генерации отчёта: {e}")
                QMessageBox.critical(self, "Ошибка", f"Не удалось сгенерировать отчёт: {str(e)}")

    def display_report(self, report):
        try:
            model = QStandardItemModel()
            table = report['table']
            if not table:
                QMessageBox.warning(self, "Ошибка", "Отчёт не содержит данных")
                return
            model.setHorizontalHeaderLabels(table[0])
            for row in table[1:]:
                items = []
                for cell in row:
                    if isinstance(cell, (int, float)):
                        cell_str = str(cell)
                    elif cell is None:
                        cell_str = ""
                    else:
                        cell_str = str(cell)
                    logging.debug(f"Создание QStandardItem для значения: {cell_str} (тип: {type(cell)})")
                    items.append(QStandardItem(cell_str))
                model.appendRow(items)
            self.report_view.setModel(model)
            self.report_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            for row in range(model.rowCount()):
                self.report_view.setRowHeight(row, 50)
            logging.info(f"Отчёт отображён: {model.rowCount()} строк")
        except Exception as e:
            logging.error(f"Ошибка отображения отчёта: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось отобразить отчёт: {str(e)}")

    def generate_planned_report(self, deliveries, products, start, end):
        header = [
            "Плановые поставки",
            f"Период: {start.strftime('%d.%m.%Y')} - {end.strftime('%d.%m.%Y')}",
            f"Поставщик: {self.report_supplier_filter.currentText()}"
        ]
        table = [["Поставщик", "План. дата", "План. сумма"]]
        for d in deliveries:
            total = sum((p.planned_quantity or 0) * (p.planned_price or 0) for p in products if p.delivery_id == d.id)
            table.append([
                d.supplier.name if d.supplier else "",
                d.planned_date.strftime("%d.%m.%Y") if d.planned_date else "",
                str(total)
            ])
        total_sum = sum((p.planned_quantity or 0) * (p.planned_price or 0) for p in products)
        table.append(["", "ИТОГО", str(total_sum)])
        return {"header": header, "table": table, "col_widths": [60, 35, 45]}

    def generate_completed_report(self, deliveries, products, start, end):
        header = [
            "Выполненные поставки",
            f"Период: {start.strftime('%d.%m.%Y')} - {end.strftime('%d.%m.%Y')}",
            f"Поставщик: {self.report_supplier_filter.currentText()}"
        ]
        table = [["Поставщик", "Номер док.", "Факт. дата", "Факт. сумма"]]
        completed = [d for d in deliveries if d.actual_date]
        if not completed:
            QMessageBox.warning(self, "Нет данных", "Нет выполненных поставок")
            return {"header": header, "table": [], "col_widths": []}
        for d in completed:
            delivery_products = [p for p in products if p.delivery_id == d.id]
            if not delivery_products:
                continue
            total = sum((p.actual_quantity or 0) * (p.actual_price or 0) for p in delivery_products)
            table.append([
                d.supplier.name if d.supplier else "",
                d.doc_number or "",
                d.actual_date.strftime("%d.%m.%Y") if d.actual_date else "",
                str(total)
            ])
        total_sum = sum((p.actual_quantity or 0) * (p.actual_price or 0) for p in products if any(d.id == p.delivery_id for d in completed))
        table.append(["", "Итого", "", str(total_sum)])
        return {"header": header, "table": table, "col_widths": [60, 60, 35, 45]}

    def generate_detailed_report(self, deliveries, products, start, end):
        header = [
            "Детализация",
            f"Период: {start.strftime('%d.%m.%Y')} - {end.strftime('%d.%m.%Y')}",
            f"Поставщик: {self.report_supplier_filter.currentText()}"
        ]
        table = [["Поставщик", "Номер док.", "План. дата", "Факт. дата", "Товар", "План. кол/цена", "Факт. кол/цена"]]
        for d in deliveries:
            for p in products:
                if p.delivery_id == d.id:
                    table.append([
                        d.supplier.name if d.supplier else "",
                        d.doc_number or "",
                        d.planned_date.strftime("%d.%m.%Y") if d.planned_date else "",
                        d.actual_date.strftime("%d.%m.%Y") if d.actual_date else "",
                        p.product.name if p.product else "",
                        f"{p.planned_quantity or 0}/{p.planned_price or 0}",
                        f"{p.actual_quantity or 0}/{p.actual_price or 0}"
                    ])
        return {"header": header, "table": table, "col_widths": [50, 60, 35, 35, 50, 40, 40]}

    def save_report(self):
        if not self.current_report:
            QMessageBox.warning(self, "Ошибка", "Сначала сформируйте отчёт")
            return
        file_name, _ = QFileDialog.getSaveFileName(self, "Сохранить отчёт", "", "PDF (*.pdf)")
        if not file_name:
            return
        if not file_name.endswith('.pdf'):
            file_name += '.pdf'
        try:
            doc = SimpleDocTemplate(file_name, pagesize=landscape(A4), rightMargin=10*mm, leftMargin=10*mm, topMargin=10*mm, bottomMargin=10*mm)
            elements = []
            styles = getSampleStyleSheet()
            try:
                pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
                font = 'DejaVuSans'
            except Exception as e:
                font = 'Helvetica'
                logging.warning(f"Шрифт DejaVuSans не найден, используется Helvetica: {e}")
            styles.add(ParagraphStyle(name='Header', fontName=font, fontSize=14, alignment=1, spaceAfter=6))
            styles.add(ParagraphStyle(name='Table', fontName=font, fontSize=10, leading=12))
            for line in self.current_report['header']:
                elements.append(Paragraph(line, styles['Header']))
            elements.append(Spacer(1, 10*mm))
            table_data = [[Paragraph(str(cell) if cell is not None else '', styles['Table']) for cell in row] for row in self.current_report['table']]
            col_widths = self.current_report.get('col_widths', [40] * len(table_data[0]))
            if len(col_widths) != len(table_data[0]):
                col_widths = [40] * len(table_data[0])
            col_widths = [w * mm for w in col_widths]
            table = Table(table_data, colWidths=col_widths, rowHeights=[6*mm] * len(table_data))
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, -1), font),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('LEADING', (0, 0), (-1, -1), 12)
            ]))
            elements.append(table)
            elements.append(Spacer(1, 10*mm))
            elements.append(Paragraph("Список поставок", styles['Table']))
            for d in self.current_report.get('deliveries_data', []):
                text = f"Поставщик: {d.get('supplier_name', '')}, Номер: {d.get('doc_number', '')}, " \
                    f"План: {d.get('planned_date').strftime('%d.%m.%Y') if d.get('planned_date') else ''}, " \
                    f"Факт: {d.get('actual_date').strftime('%d.%m.%Y') if d.get('actual_date') else ''}"
                elements.append(Paragraph(text, styles['Table']))
                for p in d.get('products', []):
                    name = p.get('name', '') or '-'
                    planned_qty = p.get('planned_quantity', 0)
                    planned_price = p.get('planned_price', 0)
                    actual_qty = p.get('actual_quantity', 0)
                    actual_price = p.get('actual_price', 0)
                    text = f" - {name}: План: {planned_qty}/{planned_price}, Факт: {actual_qty}/{actual_price}"
                    elements.append(Paragraph(text, styles['Table']))
            doc.build(elements)
            QMessageBox.information(self, "Успех", "Отчёт успешно сохранён")
            logging.info(f"Отчёт сохранён: {file_name}")
        except Exception as e:
            logging.error(f"Ошибка сохранения отчёта: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec_())