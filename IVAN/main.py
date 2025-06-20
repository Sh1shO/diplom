import sys
import logging
from datetime import date
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QLineEdit, QPushButton, QListWidget, QStackedWidget, QLabel, QComboBox,
    QTableWidgetItem, QMessageBox, QDialog, QFormLayout, QDateEdit, QHeaderView,
    QTabWidget, QTableView, QGroupBox, QFileDialog, QSizePolicy, QCheckBox,
    QSpacerItem, QListWidgetItem
)
from PySide6.QtCore import Qt, QDate, QTimer
from PySide6.QtGui import QIcon, QPixmap, QStandardItemModel, QStandardItem, QBrush, QColor
from sqlalchemy.orm import joinedload
from db import (
    User, Unit, ProductType, DeliveryCondition, Supplier, Product, Delivery,
    ProductInDelivery, Session, Role
)
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
from styles import STYLESHEET

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
        self.setMinimumSize(1800, 900)
        self.delivery = delivery
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        form_layout = QFormLayout()
        self.supplier = QComboBox()
        self.supplier.setMinimumWidth(300)
        self.supplier.setFixedHeight(35)
        self.supplier.setMaxVisibleItems(10)
        self.supplier.setStyleSheet("QComboBox QListView { max-height: 200px; }")
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
        form_layout.addRow("Поставщик:", self.supplier)
        form_layout.addRow("План. дата:", self.planned_date)
        form_layout.addRow("", self.actual_date_check)
        form_layout.addRow("Факт. дата:", self.actual_date)
        form_layout.addRow("Номер док.:", self.doc_number)
        layout.addLayout(form_layout)
        self.actual_date_check.toggled.connect(self.actual_date.setEnabled)
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(6)
        self.products_table.setHorizontalHeaderLabels([
            "Товар", "План. кол-во", "План. цена", "Факт. кол-во", "Факт. цена", "Причина отказа"
        ])
        self.products_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.products_table.setColumnWidth(0, 250)
        self.products_table.setColumnWidth(5, 200)
        layout.addWidget(self.products_table)
        if delivery:
            with Session() as s:
                products = s.query(ProductInDelivery).filter_by(delivery_id=delivery.id).all()
                self.products_table.setRowCount(len(products))
                for row, pid in enumerate(products):
                    combo = QComboBox()
                    combo.setMinimumWidth(250)
                    combo.setFixedHeight(35)
                    combo.setMaxVisibleItems(10)
                    combo.setStyleSheet("QComboBox QListView { max-height: 200px; }")
                    with Session() as s:
                        all_products = s.query(Product).all()
                        combo.addItem("Выберите", None)
                        for p in all_products:
                            combo.addItem(p.name, p.id)
                        combo.setCurrentIndex(combo.findData(pid.product_id))
                    self.products_table.setCellWidget(row, 0, combo)
                    self.products_table.setItem(row, 1, QTableWidgetItem(str(pid.planned_quantity or 0)))
                    self.products_table.setItem(row, 2, QTableWidgetItem(f"{pid.planned_price or 0:.2f}"))
                    self.products_table.setItem(row, 3, QTableWidgetItem(str(pid.actual_quantity or 0)))
                    self.products_table.setItem(row, 4, QTableWidgetItem(f"{pid.actual_price or 0:.2f}"))
                    self.products_table.setItem(row, 5, QTableWidgetItem(pid.rejection_reason or ""))
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
        combo.setMaxVisibleItems(10)
        combo.setStyleSheet("QComboBox QListView { max-height: 200px; }")
        with Session() as s:
            products = s.query(Product).all()
            combo.addItem("Выберите", None)
            for p in products:
                combo.addItem(p.name, p.id)
        self.products_table.setCellWidget(row, 0, combo)
        self.products_table.setItem(row, 1, QTableWidgetItem("0"))
        self.products_table.setItem(row, 2, QTableWidgetItem("0.00"))
        self.products_table.setItem(row, 3, QTableWidgetItem("0"))
        self.products_table.setItem(row, 4, QTableWidgetItem("0.00"))
        self.products_table.setItem(row, 5, QTableWidgetItem(""))
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
                planned_price = float(self.products_table.item(row, 2).text() or 0)
                actual_qty = int(self.products_table.item(row, 3).text() or 0)
                actual_price = float(self.products_table.item(row, 4).text() or 0)
                rejection_reason = self.products_table.item(row, 5).text() or None
            except ValueError as e:
                logging.error(f"Ошибка парсинга данных таблицы: {e}")
                planned_qty, planned_price, actual_qty, actual_price, rejection_reason = 0, 0.0, 0, 0.0, None
            products.append({
                'product_id': product_id,
                'planned_quantity': planned_qty,
                'planned_price': planned_price,
                'actual_quantity': actual_qty,
                'actual_price': actual_price,
                'rejection_reason': rejection_reason
            })
        return {
            'supplier_id': self.supplier.currentData(),
            'planned_date': self.planned_date.date().toPython(),
            'actual_date': self.actual_date.date().toPython() if self.actual_date_check.isChecked() else None,
            'doc_number': self.doc_number.text().strip(),
            'products': products
        }

class ChangePasswordDialog(QDialog):
    def __init__(self, user):
        super().__init__()
        self.setWindowTitle("Смена пароля")
        self.user = user
        layout = QFormLayout(self)
        self.old_password = QLineEdit()
        self.old_password.setEchoMode(QLineEdit.Password)
        self.new_password = QLineEdit()
        self.new_password.setEchoMode(QLineEdit.Password)
        self.confirm_password = QLineEdit()
        self.confirm_password.setEchoMode(QLineEdit.Password)
        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(self.save_password)
        layout.addRow("Старый пароль:", self.old_password)
        layout.addRow("Новый пароль:", self.new_password)
        layout.addRow("Подтвердить пароль:", self.confirm_password)
        layout.addRow(save_button)

    def save_password(self):
        old = self.old_password.text().strip()
        new = self.new_password.text().strip()
        confirm = self.confirm_password.text().strip()
        if old != self.user.password:
            QMessageBox.critical(self, "Ошибка", "Неверный старый пароль")
            return
        if new != confirm:
            QMessageBox.critical(self, "Ошибка", "Пароли не совпадают")
            return
        if not new:
            QMessageBox.critical(self, "Ошибка", "Новый пароль не может быть пустым")
            return
        with Session() as s:
            try:
                user = s.query(User).get(self.user.id)
                user.password = new
                s.commit()
                QMessageBox.information(self, "Успех", "Пароль изменён")
                self.accept()
            except Exception as e:
                s.rollback()
                logging.error(f"Ошибка смены пароля: {e}")
                QMessageBox.critical(self, "Ошибка", f"Не удалось сменить пароль: {str(e)}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Цветочный магазин «Привет, я – букет»")
        self.setWindowIcon(QIcon("logo.svg"))
        self.current_user = None
        self.current_report = None
        self.report_widget = QWidget()  # Инициализируем явно
        self.report_widget_layout = QVBoxLayout(self.report_widget)
        preview_group = QGroupBox("")
        preview_group.setObjectName("report_preview")
        preview_layout = QVBoxLayout(preview_group)
        self.report_view = QTableView()
        preview_layout.addWidget(self.report_view)
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        save_report = QPushButton("Сохранить отчёт")
        save_report.setMinimumWidth(150)
        save_report.setFixedHeight(35)
        save_report.clicked.connect(self.save_report)
        save_layout.addWidget(save_report)
        preview_layout.addLayout(save_layout)
        self.report_widget_layout.addWidget(preview_group)
        self.show_login_dialog()
        self.notification_timer = QTimer(self)
        self.notification_timer.timeout.connect(self.check_active_deliveries)
        self.notification_timer.start(30 * 60 * 1000)

    def show_login_dialog(self):
        dialog = LoginDialog()
        if dialog.exec_():
            username, password = dialog.get_credentials()
            with Session() as s:
                user = s.query(User).join(Role).filter(User.username == username, User.password == password).first()
                if user:
                    self.current_user = user
                    self.setup_ui()
                    self.tabs.setCurrentIndex(self.tabs.indexOf(self.delivery_tab))
                    QMessageBox.information(self, "Напоминание", "Не забудьте создать резервную копию базы данных!")
                else:
                    QMessageBox.critical(self, "Ошибка", "Неверный логин или пароль")
                    self.show_login_dialog()

    def check_active_deliveries(self):
        with Session() as s:
            start = self.delivery_start_date.date().toPython()
            end = self.delivery_end_date.date().toPython()
            active_deliveries = s.query(Delivery).options(joinedload(Delivery.supplier)).filter(
                Delivery.planned_date >= start,
                Delivery.planned_date <= end,
                Delivery.actual_date.is_(None)
            ).all()
            self.notification_count = len(active_deliveries)
            if self.notification_count > 0:
                self.notification_button.setText(f"Уведомления ({self.notification_count})")
            else:
                self.notification_button.setText("Уведомления")
            self.update_notification_list(active_deliveries)

    def update_notification_list(self, deliveries):
        self.notification_list.clear()
        for d in deliveries:
            supplier_name = d.supplier.name if d.supplier else "Неизвестно"
            date_str = d.planned_date.strftime("%d.%m.%Y") if d.planned_date else "-"
            text = f"Активная поставка: {supplier_name} - {date_str}"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, d.id)
            self.notification_list.addItem(item)

    def show_notifications(self):
        self.tabs.setCurrentIndex(self.tabs.indexOf(self.notification_tab))
        self.check_active_deliveries()

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self.on_tab_changed)
        left_layout.addWidget(self.tabs)

        # Проверка роли пользователя
        with Session() as session:
            user = session.query(User).options(joinedload(User.role)).filter(User.id == self.current_user.id).first()
            if user and user.role and user.role.name == "florist":
                # Для роли "Флорист" показываем только вкладки "Поставки", "Уведомления" и "Отчёты"
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
                self.delivery_start_date = QDateEdit(QDate(2025, 6, 1))
                self.delivery_start_date.setCalendarPopup(True)
                self.delivery_start_date.setFixedHeight(35)
                start_row.addWidget(start_label)
                start_row.addWidget(self.delivery_start_date)
                filters_layout.addLayout(start_row)
                end_row = QHBoxLayout()
                end_label = QLabel("по:")
                end_label.setFixedWidth(80)
                end_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.delivery_end_date = QDateEdit(QDate(2025, 6, 30))
                self.delivery_end_date.setCalendarPopup(True)
                self.delivery_end_date.setFixedHeight(35)
                end_row.addWidget(end_label)
                end_row.addWidget(self.delivery_end_date)
                filters_layout.addLayout(end_row)
                supplier_row = QHBoxLayout()
                supplier_label = QLabel("Поставщик:")
                supplier_label.setFixedWidth(80)
                supplier_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
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
                add_delivery.setEnabled(self.current_user.can_edit)
                delivery_layout.addWidget(add_delivery)
                self.delivery_start_date.dateChanged.connect(self.update_deliveries)
                self.delivery_end_date.dateChanged.connect(self.update_deliveries)
                self.delivery_supplier_filter.currentIndexChanged.connect(self.update_deliveries)
                self.tabs.addTab(delivery_tab, "Поставки")
                self.delivery_tab = delivery_tab

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
                self.report_start_date = QDateEdit(QDate(2025, 6, 1))
                self.report_start_date.setCalendarPopup(True)
                self.report_start_date.setFixedHeight(35)
                start_row.addWidget(start_label)
                start_row.addWidget(self.report_start_date)
                filters_group_layout.addLayout(start_row)
                end_row = QHBoxLayout()
                end_label = QLabel("по:")
                end_label.setFixedWidth(80)
                end_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.report_end_date = QDateEdit(QDate(2025, 6, 30))
                self.report_end_date.setCalendarPopup(True)
                self.report_end_date.setFixedHeight(35)
                end_row.addWidget(end_label)
                end_row.addWidget(self.report_end_date)
                filters_group_layout.addLayout(end_row)
                supplier_row = QHBoxLayout()
                supplier_label = QLabel("Поставщик:")
                supplier_label.setFixedWidth(80)
                supplier_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
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
                report_layout.addWidget(self.report_widget, 2)
                self.tabs.addTab(report_tab, "Отчёты")


            else:
                # Для других ролей (например, Admin) отображаем полный интерфейс
                ref_tab = QWidget()
                ref_layout = QVBoxLayout(ref_tab)
                self.ref_list = QListWidget()
                self.ref_list.addItems(["Единицы измерения", "Типы товаров", "Условия поставки", "Поставщики", "Товары"])
                self.ref_list.currentItemChanged.connect(self.show_reference)
                ref_layout.addWidget(self.ref_list)
                self.tabs.addTab(ref_tab, "Справочники")
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
                self.delivery_start_date = QDateEdit(QDate(2025, 6, 1))
                self.delivery_start_date.setCalendarPopup(True)
                self.delivery_start_date.setFixedHeight(35)
                start_row.addWidget(start_label)
                start_row.addWidget(self.delivery_start_date)
                filters_layout.addLayout(start_row)
                end_row = QHBoxLayout()
                end_label = QLabel("по:")
                end_label.setFixedWidth(80)
                end_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.delivery_end_date = QDateEdit(QDate(2025, 6, 30))
                self.delivery_end_date.setCalendarPopup(True)
                self.delivery_end_date.setFixedHeight(35)
                end_row.addWidget(end_label)
                end_row.addWidget(self.delivery_end_date)
                filters_layout.addLayout(end_row)
                supplier_row = QHBoxLayout()
                supplier_label = QLabel("Поставщик:")
                supplier_label.setFixedWidth(80)
                supplier_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
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
                self.delivery_tab = delivery_tab
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
                self.report_start_date = QDateEdit(QDate(2025, 6, 1))
                self.report_start_date.setCalendarPopup(True)
                self.report_start_date.setFixedHeight(35)
                start_row.addWidget(start_label)
                start_row.addWidget(self.report_start_date)
                filters_group_layout.addLayout(start_row)
                end_row = QHBoxLayout()
                end_label = QLabel("по:")
                end_label.setFixedWidth(80)
                end_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.report_end_date = QDateEdit(QDate(2025, 6, 30))
                self.report_end_date.setCalendarPopup(True)
                self.report_end_date.setFixedHeight(35)
                end_row.addWidget(end_label)
                end_row.addWidget(self.report_end_date)
                filters_group_layout.addLayout(end_row)
                supplier_row = QHBoxLayout()
                supplier_label = QLabel("Поставщик:")
                supplier_label.setFixedWidth(80)
                supplier_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
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
                report_layout.addWidget(self.report_widget, 2)
                self.tabs.addTab(report_tab, "Отчёты")
                if self.current_user.role.name.lower() == "admin":
                    settings_tab = QWidget()
                    settings_layout = QVBoxLayout(settings_tab)
                    settings_tabs = QTabWidget()
                    role_tab = QWidget()
                    role_layout = QVBoxLayout(role_tab)
                    self.user_combo = QComboBox()
                    with Session() as s:
                        users = s.query(User).all()
                        self.user_combo.addItem("Выберите пользователя", None)
                        for u in users:
                            self.user_combo.addItem(u.username, u.id)
                    self.user_combo.currentIndexChanged.connect(self.load_user_permissions)
                    self.edit_check = QCheckBox("Редактирование")
                    self.delete_check = QCheckBox("Удаление")
                    self.view_check = QCheckBox("Просмотр")
                    save_permissions = QPushButton("Сохранить права")
                    save_permissions.clicked.connect(self.save_permissions)
                    role_layout.addWidget(QLabel("Выберите пользователя:"))
                    role_layout.addWidget(self.user_combo)
                    role_layout.addWidget(self.edit_check)
                    role_layout.addWidget(self.delete_check)
                    role_layout.addWidget(self.view_check)
                    role_layout.addWidget(save_permissions)
                    role_layout.addStretch()
                    settings_tabs.addTab(role_tab, "Назначение ролей")
                    stats_tab = QWidget()
                    stats_layout = QVBoxLayout(stats_tab)
                    self.stats_label = QLabel()
                    self.update_statistics()
                    stats_layout.addWidget(self.stats_label)
                    stats_layout.addStretch()
                    settings_tabs.addTab(stats_tab, "Статистика")
                    account_tab = QWidget()
                    account_layout = QVBoxLayout(account_tab)
                    logout_button = QPushButton("Выйти из учётной записи")
                    logout_button.clicked.connect(self.logout)
                    change_password_button = QPushButton("Сменить пароль")
                    change_password_button.clicked.connect(self.change_password)
                    account_layout.addWidget(logout_button)
                    account_layout.addWidget(change_password_button)
                    account_layout.addStretch()
                    settings_tabs.addTab(account_tab, "Учётная запись")
                    about_tab = QWidget()
                    about_layout = QVBoxLayout(about_tab)
                    about_text = QLabel(
                        "Название: Deliveries\n"
                        "Версия: 1.0\n"
                        "Разработчик: IVAN\n"
                        "Дата выпуска: 07.06.2025"
                    )
                    about_layout.addWidget(about_text)
                    about_layout.addStretch()
                    settings_tabs.addTab(about_tab, "О приложении")
                    settings_layout.addWidget(settings_tabs)
                    self.tabs.addTab(settings_tab, "Настройки")

        notification_tab = QWidget()
        notification_layout = QVBoxLayout(notification_tab)
        self.notification_list = QListWidget()
        self.notification_list.setObjectName("notificationList")
        self.notification_list.itemDoubleClicked.connect(self.on_notification_double_click)
        notification_layout.addWidget(self.notification_list)
        self.tabs.addTab(notification_tab, "Уведомления")
        self.notification_tab = notification_tab
        self.notification_button = QPushButton("Уведомления")
        self.notification_button.setObjectName("notificationButton")
        self.notification_button.setFixedHeight(35)
        self.notification_button.clicked.connect(self.show_notifications)
        left_layout.addWidget(self.notification_button)
        main_layout.addWidget(left_panel, 1)
        self.right_panel = QStackedWidget()
        main_layout.addWidget(self.right_panel, 3)
        self.right_panel.addWidget(QWidget())
        self.update_deliveries()
        self.check_active_deliveries()

    def on_notification_double_click(self, item):
        delivery_id = item.data(Qt.UserRole)
        self.tabs.setCurrentIndex(self.tabs.indexOf(self.delivery_tab))
        self.delivery_list.setCurrentRow(-1)
        for i in range(self.delivery_list.count()):
            if self.delivery_list.item(i).data(Qt.UserRole) == delivery_id:
                self.delivery_list.setCurrentRow(i)
                self.show_delivery()
                break

    def load_user_permissions(self):
        user_id = self.user_combo.currentData()
        if not user_id:
            self.edit_check.setChecked(False)
            self.delete_check.setChecked(False)
            self.view_check.setChecked(False)
            return
        with Session() as s:
            user = s.query(User).get(user_id)
            self.edit_check.setChecked(bool(user.can_edit))
            self.delete_check.setChecked(bool(user.can_delete))
            self.view_check.setChecked(bool(user.can_view))

    def save_permissions(self):
        user_id = self.user_combo.currentData()
        if not user_id:
            QMessageBox.warning(self, "Ошибка", "Выберите пользователя")
            return
        with Session() as s:
            try:
                user = s.query(User).get(user_id)
                user.can_edit = 1 if self.edit_check.isChecked() else 0
                user.can_delete = 1 if self.delete_check.isChecked() else 0
                user.can_view = 1 if self.view_check.isChecked() else 0
                s.commit()
                QMessageBox.information(self, "Успех", "Права сохранены")
            except Exception as e:
                s.rollback()
                logging.error(f"Ошибка сохранения прав: {e}")
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить права: {str(e)}")

    def update_statistics(self):
        with Session() as s:
            delivery_count = s.query(Delivery).count()
            product_count = s.query(Product).count()
            self.stats_label.setText(f"Всего поставок: {delivery_count}\nВсего товаров: {product_count}")

    def logout(self):
        self.current_user = None
        self.close()
        self.__init__()

    def change_password(self):
        dialog = ChangePasswordDialog(self.current_user)
        dialog.exec_()

    def on_tab_changed(self, index):
        if self.tabs.tabText(index) == "Отчёты":
            if self.right_panel.count() > 1:
                self.right_panel.removeWidget(self.right_panel.widget(1))
            if self.report_widget:
                self.right_panel.addWidget(self.report_widget)
                self.right_panel.setCurrentIndex(1)
        elif self.tabs.tabText(index) == "Поставки":
            self.update_deliveries()
        else:
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
        add_btn.setEnabled(self.current_user.can_edit)
        edit_btn.setEnabled(self.current_user.can_edit)
        delete_btn.setEnabled(self.current_user.can_delete)
        buttons.addWidget(add_btn)
        buttons.addWidget(edit_btn)
        buttons.addWidget(delete_btn)
        layout.addLayout(buttons)

        def update_table():
            if not self.current_user.can_view:
                table.setRowCount(0)
                return
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
        if not self.current_user.can_view:
            self.delivery_list.clear()
            logging.warning("Нет прав на просмотр, список поставок очищен")
            return
        start = self.delivery_start_date.date().toPython()
        end = self.delivery_end_date.date().toPython()
        supplier_id = self.delivery_supplier_filter.currentData()
        logging.info(f"Обновление поставок: дата с {start} по {end}, поставщик {supplier_id}")
        with Session() as s:
            query = s.query(Delivery).options(joinedload(Delivery.supplier)).filter(
                Delivery.planned_date >= start,
                Delivery.planned_date <= end
            )
            if supplier_id:
                query = query.filter(Delivery.supplier_id == supplier_id)
            deliveries = query.all()
            logging.info(f"Всего записей в запросе: {len(deliveries)}")
            for d in deliveries:
                log_date = d.planned_date.strftime("%d.%m.%Y") if d.planned_date else "NULL"
                logging.info(f"Поставка ID={d.id}, planned_date={log_date}, supplier={d.supplier.name if d.supplier else 'None'}")
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
            self.check_active_deliveries()

    def show_delivery(self):
        item = self.delivery_list.currentItem()
        if not item or not self.current_user.can_view:
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
        planned_cost = QLabel()
        actual_cost = QLabel()
        info.addRow("Поставщик:", supplier)
        info.addRow("План. дата:", planned)
        info.addRow("Факт. дата:", actual)
        info.addRow("Номер док.:", doc_num)
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
        edit_btn.setEnabled(self.current_user.can_edit)
        delete_btn.setEnabled(self.current_user.can_delete)
        buttons.addWidget(edit_btn)
        buttons.addWidget(delete_btn)
        layout.addLayout(buttons)
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["Товар", "План. кол-во", "План. цена", "Факт. кол-во", "Факт. цена", "Причина отказа"])
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
            products = s.query(ProductInDelivery).options(
                joinedload(ProductInDelivery.product)
            ).filter_by(delivery_id=delivery_id).all()
            planned_total = sum((p.planned_quantity or 0) * (p.planned_price or 0) for p in products)
            actual_total = sum((p.actual_quantity or 0) * (p.actual_price or 0) for p in products) if delivery.actual_date else 0
            planned_cost.setText(f"{planned_total:.2f}")
            actual_cost.setText(f"{actual_total:.2f}")
            table.setRowCount(len(products))
            for row, p in enumerate(products):
                item = QTableWidgetItem(p.product.name if p.product else "")
                item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                table.setItem(row, 0, item)
                item = QTableWidgetItem(str(p.planned_quantity or 0))
                item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                table.setItem(row, 1, item)
                item = QTableWidgetItem(f"{p.planned_price or 0:.2f}")
                item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                table.setItem(row, 2, item)
                item = QTableWidgetItem(str(p.actual_quantity or 0))
                item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                table.setItem(row, 3, item)
                item = QTableWidgetItem(f"{p.actual_price or 0:.2f}")
                item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                table.setItem(row, 4, item)
                item = QTableWidgetItem(p.rejection_reason or "")
                item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                table.setItem(row, 5, item)
                table.setRowHeight(row, 50)
        if self.right_panel.count() > 1:
            self.right_panel.removeWidget(self.right_panel.widget(1))
        self.right_panel.addWidget(widget)
        self.right_panel.setCurrentIndex(1)

    def add_record(self):
        if not self.current_user.can_edit:
            QMessageBox.warning(self, "Ошибка", "Нет прав на редактирование")
            return
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
        if not self.current_user.can_edit:
            QMessageBox.warning(self, "Ошибка", "Нет прав на редактирование")
            return
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
        if not self.current_user.can_delete:
            QMessageBox.warning(self, "Ошибка", "Нет прав на удаление")
            return
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
        if not self.current_user.can_edit:
            QMessageBox.warning(self, "Ошибка", "Нет прав на редактирование")
            return
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
                        doc_number=data['doc_number']
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
                            actual_price=p['actual_price'],
                            rejection_reason=p['rejection_reason']
                        ))
                    s.commit()
                    self.update_deliveries()
                    logging.info(f"Поставка добавлена: {data['doc_number']}")
                except Exception as e:
                    s.rollback()
                    logging.error(f"Ошибка добавления поставки: {e}")
                    QMessageBox.critical(self, "Ошибка", f"Не удалось добавить: {str(e)}")

    def edit_delivery(self):
        if not self.current_user.can_edit:
            QMessageBox.warning(self, "Ошибка", "Нет прав на редактирование")
            return
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
                    s.query(ProductInDelivery).filter_by(delivery_id=delivery.id).delete()
                    for p in data['products']:
                        s.add(ProductInDelivery(
                            delivery_id=delivery.id,
                            product_id=p['product_id'],
                            planned_quantity=p['planned_quantity'],
                            planned_price=p['planned_price'],
                            actual_quantity=p['actual_quantity'],
                            actual_price=p['actual_price'],
                            rejection_reason=p['rejection_reason']
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
        if not self.current_user.can_delete:
            QMessageBox.warning(self, "Ошибка", "Нет прав на удаление")
            return
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
        if not self.current_user.can_view:
            QMessageBox.warning(self, "Ошибка", "Нет прав на просмотр")
            return
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
                logging.info(f"Найдено поставок: {len(deliveries)}, товаров: {len(products)}")
                if not deliveries:
                    QMessageBox.warning(self, "Ошибка", "Нет поставок за выбранный период")
                    self.display_report({"header": [], "table": [["Нет данных"]], "col_widths": [100]})
                    return
                if not products:
                    QMessageBox.warning(self, "Ошибка", "Нет товаров в поставках за выбранный период")
                    self.display_report({"header": [], "table": [["Нет данных"]], "col_widths": [100]})
                    return
                deliveries_data = []
                for d in deliveries:
                    delivery_products = [
                        {
                            "name": p.product.name if p.product else "",
                            "planned_quantity": p.planned_quantity or 0,
                            "planned_price": p.planned_price or 0.0,
                            "actual_quantity": p.actual_quantity or 0,
                            "actual_price": p.actual_price or 0.0,
                            "rejection_reason": p.rejection_reason or ""
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
                    self.display_report({"header": [], "table": [["Нет данных"]], "col_widths": [100]})
                    return
                if report_type == "planned":
                    report = self.generate_planned_report(deliveries, products, start, end)
                elif report_type == "completed":
                    report = self.generate_completed_report(deliveries, products, start, end)
                elif report_type == "detailed":
                    report = self.generate_detailed_report(deliveries, products, start, end)
                else:
                    logging.error(f"Неизвестный тип отчёта: {report_type}")
                    self.display_report({"header": [], "table": [["Ошибка"]], "col_widths": [100]})
                    return
                report['deliveries_data'] = deliveries_data
                self.current_report = report
                self.display_report(report)
                logging.info(f"Отчёт сгенерирован: {report_type}")
            except Exception as e:
                logging.error(f"Ошибка генерации отчёта: {e}")
                QMessageBox.critical(self, "Ошибка", f"Не удалось сгенерировать отчёт: {str(e)}")
                self.display_report({"header": [], "table": [["Ошибка"]], "col_widths": [100]})

    def display_report(self, report):
        try:
            model = QStandardItemModel()
            table = report['table']
            if not table or not any(table):
                model.setHorizontalHeaderLabels(["Нет данных"])
                model.appendRow([QStandardItem("Нет данных")])
            else:
                model.setHorizontalHeaderLabels(table[0])
                for row in table[1:]:
                    items = []
                    for cell in row:
                        if isinstance(cell, (int, float)):
                            cell_str = f"{cell:.2f}" if isinstance(cell, float) else str(cell)
                        elif cell is None:
                            cell_str = ""
                        else:
                            cell_str = str(cell)
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
            model = QStandardItemModel()
            model.setHorizontalHeaderLabels(["Ошибка"])
            model.appendRow([QStandardItem("Ошибка отображения")])
            self.report_view.setModel(model)

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
        table = [["Поставщик", "Номер док.", "План. дата", "Факт. дата", "Товар", "План. кол/цена", "Факт. кол/цена", "Причина отказа"]]
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
                        f"{p.actual_quantity or 0}/{p.actual_price or 0}",
                        p.rejection_reason or ""
                    ])
        return {"header": header, "table": table, "col_widths": [50, 60, 35, 35, 50, 40, 40, 50]}

    def save_report(self):
        if not hasattr(self, 'current_report') or not self.current_report['header']:
            QMessageBox.warning(self, "Ошибка", "Сначала сформируйте отчёт")
            return
        file_name, _ = QFileDialog.getSaveFileName(self, "Сохранить отчёт", "", "PDF (*.pdf)")
        if not file_name:
            return
        if not file_name.endswith('.pdf'):
            file_name += '.pdf'
        try:
            # Определяем альбомную ориентацию для детализированного отчёта
            is_detailed = self.current_report['header'][0] == "Детализация"
            doc = SimpleDocTemplate(
                file_name,
                pagesize=landscape(A4) if is_detailed else A4,
                rightMargin=10*mm,
                leftMargin=10*mm,
                topMargin=10*mm,
                bottomMargin=10*mm
            )
            elements = []
            styles = getSampleStyleSheet()
            try:
                pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
                font = 'DejaVuSans'
            except Exception as e:
                font = 'Helvetica'
                logging.warning(f"Шрифт DejaVuSans не найден, используется Helvetica: {e}")
            styles.add(ParagraphStyle(name='Header', fontName=font, fontSize=14, alignment=1, spaceAfter=6))
            styles.add(ParagraphStyle(name='Table', fontName=font, fontSize=10, leading=12, wordWrap='CJK'))
            for line in self.current_report['header']:
                elements.append(Paragraph(line, styles['Header']))
            elements.append(Spacer(1, 10*mm))
            
            # Преобразование данных таблицы в Paragraph для каждой ячейки
            table_data = self.current_report['table']
            pdf_table_data = []
            for row in table_data:
                pdf_row = []
                for cell in row:
                    if cell is None:
                        cell_text = ""
                    elif isinstance(cell, (int, float)):
                        cell_text = f"{cell:.2f}" if isinstance(cell, float) else str(cell)
                    else:
                        cell_text = str(cell)
                    pdf_row.append(Paragraph(cell_text, styles['Table']))
                pdf_table_data.append(pdf_row)
            
            # Динамическая настройка ширины столбцов
            page_width = (landscape(A4)[0] if is_detailed else A4[0]) - 20*mm  # Учитываем поля
            col_count = len(table_data[0])
            col_widths = self.current_report.get('col_widths', [page_width / col_count] * col_count)
            if len(col_widths) != col_count:
                col_widths = [page_width / col_count] * col_count
            col_widths = [min(w * mm, page_width / col_count) for w in col_widths]
            total_width = sum(col_widths)
            if total_width > page_width:
                scale_factor = page_width / total_width
                col_widths = [w * scale_factor for w in col_widths]
            
            # Создание таблицы с поддержкой разбиения
            table = Table(pdf_table_data, colWidths=col_widths, splitByRow=True, splitInRow=False)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, -1), font),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('LEADING', (0, 0), (-1, -1), 12),
                ('WORDWRAP', (0, 0), (-1, -1), 'CJK'),  # Поддержка переноса текста
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4)
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
                    rejection_reason = p.get('rejection_reason', '') or '-'
                    text = f" - {name}: План: {planned_qty}/{planned_price}, Факт: {actual_qty}/{actual_price}, Причина отказа: {rejection_reason}"
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