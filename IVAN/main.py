import sys
import logging
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QLineEdit, QPushButton, QListWidget, QStackedWidget, QLabel, QComboBox,
    QTableWidgetItem, QMessageBox, QDialog, QFormLayout, QDateEdit, QListWidgetItem,
    QHeaderView, QTabWidget, QTableView, QGroupBox, QFileDialog, QSizePolicy
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QIcon, QPixmap, QStandardItemModel, QStandardItem
from sqlalchemy.orm import joinedload
from db import (
    User, Unit, ProductType, DeliveryCondition, Supplier, Product, Delivery,
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
        self.username.setMinimumHeight(40)
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setPlaceholderText("Пароль")
        self.password.setMinimumHeight(40)
        login_button = QPushButton("Войти")
        login_button.setMinimumHeight(40)
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
        self.setMinimumSize(600, 400)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
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
        self.setMinimumSize(1000, 800)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
        self.delivery = delivery
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        form_layout = QFormLayout()
        self.supplier = QComboBox()
        self.planned_date = QDateEdit(QDate.currentDate())
        self.planned_date.setCalendarPopup(True)
        self.actual_date = QDateEdit(QDate.currentDate())
        self.actual_date.setCalendarPopup(True)
        self.doc_number = QLineEdit()
        self.doc_date = QDateEdit(QDate.currentDate())
        self.doc_date.setCalendarPopup(True)
        with Session() as s:
            suppliers = s.query(Supplier).all()
            self.supplier.addItem("Выберите", None)
            for sup in suppliers:
                self.supplier.addItem(sup.name, sup.id)
            if delivery:
                self.supplier.setCurrentIndex(self.supplier.findData(delivery.supplier_id))
                self.planned_date.setDate(delivery.planned_date or QDate.currentDate())
                self.actual_date.setDate(delivery.actual_date or QDate.currentDate())
                self.doc_number.setText(delivery.doc_number or "")
                self.doc_date.setDate(delivery.doc_date or QDate.currentDate())
        form_layout.addRow("Поставщик:", self.supplier)
        form_layout.addRow("План. дата:", self.planned_date)
        form_layout.addRow("Факт. дата:", self.actual_date)
        form_layout.addRow("Номер док.:", self.doc_number)
        form_layout.addRow("Дата док.:", self.doc_date)
        layout.addLayout(form_layout)
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(5)
        self.products_table.setHorizontalHeaderLabels([
            "Товар", "План. кол-во", "План. цена", "Факт. кол-во", "Факт. цена"
        ])
        self.products_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.products_table.setColumnWidth(0, 250)
        self.products_table.setStyleSheet("QTableWidget QLineEdit:focus { border: none; }")
        layout.addWidget(self.products_table)
        for row in range(self.products_table.rowCount()):
            self.products_table.setRowHeight(row, 50)
        if delivery:
            with Session() as s:
                products = s.query(ProductInDelivery).filter_by(delivery_id=delivery.id).all()
                self.products_table.setRowCount(len(products))
                for row, pid in enumerate(products):
                    combo = QComboBox()
                    combo.setMinimumWidth(250)
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
                    self.products_table.setRowHeight(row, 50)
        buttons_layout = QHBoxLayout()
        add_product = QPushButton("Добавить товар")
        add_product.clicked.connect(self.add_product_row)
        remove_product = QPushButton("Удалить товар")
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
            except Exception as e:
                logging.error(f"Ошибка парсинга данных таблицы: {e}")
                planned_qty, planned_price, actual_qty, actual_price = 0, 0.0, 0, 0.0
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
            'actual_date': self.actual_date.date().toPython(),
            'doc_number': self.doc_number.text().strip(),
            'doc_date': self.doc_date.date().toPython(),
            'products': products
        }

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Магазин")
        self.setWindowIcon(QIcon("logo.svg"))
        self.setStyleSheet(STYLESHEET)
        self.current_user = None
        self.current_report = None
        self.report_widget = None
        self.show_login_dialog()

    def show_login_dialog(self):
        dialog = LoginDialog()
        if dialog.exec():
            username, password = dialog.get_credentials()
            with Session() as s:
                user = s.query(User).filter_by(username=username, password=password).first()
                if user:
                    self.current_user = user
                    self.setup_ui()
                else:
                    QMessageBox.critical(self, "Ошибка", "Неверный логин или пароль")
                    self.show_login_dialog()
        else:
            sys.exit()

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self.on_tab_changed)
        left_layout.addWidget(self.tabs)
        ref_tab = QWidget()
        ref_layout = QVBoxLayout(ref_tab)
        self.ref_list = QListWidget()
        self.ref_list.addItems(["Единицы измерения", "Типы товаров", "Условия поставки", "Поставщики", "Товары"])
        self.ref_list.currentItemChanged.connect(self.show_reference)
        ref_layout.addWidget(self.ref_list)
        self.tabs.addTab(ref_tab, "Справочники")
        delivery_tab = QWidget()
        delivery_layout = QVBoxLayout(delivery_tab)
        self.delivery_list = QListWidget()
        self.delivery_list.currentItemChanged.connect(self.show_delivery)
        delivery_layout.addWidget(self.delivery_list)
        add_delivery = QPushButton("Добавить поставку")
        add_delivery.clicked.connect(self.add_delivery)
        delivery_layout.addWidget(add_delivery)
        self.tabs.addTab(delivery_tab, "Поставки")
        report_tab = QWidget()
        report_layout = QHBoxLayout(report_tab)
        filters = QWidget()
        filters_layout = QVBoxLayout(filters)
        filters_group = QGroupBox("Фильтры")
        filters_group.setStyleSheet("QGroupBox::title { top: -10px; }")
        filters_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        filters_group_layout = QVBoxLayout(filters_group)
        filters_group_layout.setSpacing(5)
        filters_group_layout.setContentsMargins(15, 20, 15, 15)
        self.start_date = QDateEdit(QDate.currentDate().addMonths(-1))
        self.start_date.setCalendarPopup(True)
        self.start_date.setFixedHeight(30)
        filters_group_layout.addWidget(QLabel("Дата с:"))
        filters_group_layout.addWidget(self.start_date)
        self.end_date = QDateEdit(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        self.end_date.setFixedHeight(30)
        filters_group_layout.addWidget(QLabel("по:"))
        filters_group_layout.addWidget(self.end_date)
        self.supplier_filter = QComboBox()
        self.supplier_filter.setFixedHeight(30)
        with Session() as s:
            suppliers = s.query(Supplier).all()
            self.supplier_filter.addItem("Все", None)
            for sup in suppliers:
                self.supplier_filter.addItem(sup.name, sup.id)
        filters_group_layout.addWidget(QLabel("Поставщик:"))
        filters_group_layout.addWidget(self.supplier_filter)
        filters_group_layout.addStretch()
        buttons_container = QWidget()
        buttons_layout = QVBoxLayout(buttons_container)
        buttons_layout.setSpacing(5)
        planned_btn = QPushButton("Плановые")
        planned_btn.setMinimumWidth(120)
        planned_btn.clicked.connect(lambda: self.generate_report("planned"))
        buttons_layout.addWidget(planned_btn)
        completed_btn = QPushButton("Выполненные")
        completed_btn.setMinimumWidth(120)
        completed_btn.clicked.connect(lambda: self.generate_report("completed"))
        buttons_layout.addWidget(completed_btn)
        detailed_btn = QPushButton("Детализация")
        detailed_btn.setMinimumWidth(120)
        detailed_btn.clicked.connect(lambda: self.generate_report("detailed"))
        buttons_layout.addWidget(detailed_btn)
        filters_group_layout.addWidget(buttons_container)
        filters_layout.addWidget(filters_group)
        filters_layout.addStretch()
        report_layout.addWidget(filters, 1)
        self.report_view = QTableView()
        save_report = QPushButton("Сохранить отчёт")
        save_report.setMinimumWidth(120)
        self.report_widget = QWidget()
        report_widget_layout = QVBoxLayout(self.report_widget)
        preview_group = QGroupBox("Просмотр")
        preview_group_layout = QVBoxLayout(preview_group)
        preview_group_layout.addWidget(self.report_view)
        preview_group_layout.addWidget(save_report)
        report_widget_layout.addWidget(preview_group)
        report_layout.addWidget(self.report_widget, 2)
        self.tabs.addTab(report_tab, "Отчёты")
        main_layout.addWidget(left_panel, 1)
        self.right_panel = QStackedWidget()
        main_layout.addWidget(self.right_panel, 3)
        self.right_panel.addWidget(QWidget())
        self.update_deliveries()

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
        filter_layout = QHBoxLayout()
        search = QLineEdit()
        search.setPlaceholderText("Поиск...")
        filter_combo = QComboBox()
        if ref_type == "Единицы измерения":
            filter_combo.addItems(["Все", "Название"])
        elif ref_type == "Типы товаров":
            filter_combo.addItems(["Все", "Название"])
        elif ref_type == "Условия поставки":
            filter_combo.addItems(["Все", "Название"])
        elif ref_type == "Поставщики":
            filter_combo.addItems(["Все", "ИНН", "Название", "Телефон"])
        elif ref_type == "Товары":
            filter_combo.addItems(["Все", "Название", "Ед. изм.", "Тип", "Условие"])
        filter_layout.addWidget(QLabel("Поиск:"))
        filter_layout.addWidget(search)
        filter_layout.addWidget(QLabel("Фильтр:"))
        filter_layout.addWidget(filter_combo)
        layout.addLayout(filter_layout)
        table = QTableWidget()
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(table)
        buttons = QHBoxLayout()
        add_btn = QPushButton("Добавить")
        add_btn.clicked.connect(self.add_record)
        edit_btn = QPushButton("Редактировать")
        edit_btn.clicked.connect(self.edit_record)
        delete_btn = QPushButton("Удалить")
        delete_btn.clicked.connect(self.delete_record)
        buttons.addWidget(add_btn)
        buttons.addWidget(edit_btn)
        buttons.addWidget(delete_btn)
        layout.addLayout(buttons)

        def update_table():
            search_text = search.text().lower()
            filter_field = filter_combo.currentText()
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
                    filtered = []
                    for r in records:
                        if not search_text:
                            filtered.append(r)
                        elif filter_field == "Все":
                            if (search_text in (r.inn or "").lower() or
                                search_text in (r.name or "").lower() or
                                search_text in (r.phone or "").lower()):
                                filtered.append(r)
                        elif filter_field == "ИНН" and search_text in (r.inn or "").lower():
                            filtered.append(r)
                        elif filter_field == "Название" and search_text in (r.name or "").lower():
                            filtered.append(r)
                        elif filter_field == "Телефон" and search_text in (r.phone or "").lower():
                            filtered.append(r)
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
                    filtered = []
                    for r in records:
                        if not search_text:
                            filtered.append(r)
                        elif filter_field == "Все":
                            if (search_text in (r.name or "").lower() or
                                search_text in (r.unit.name if r.unit else "").lower() or
                                search_text in (r.type.name if r.type else "").lower() or
                                search_text in (r.condition.name if r.condition else "").lower()):
                                filtered.append(r)
                        elif filter_field == "Название" and search_text in (r.name or "").lower():
                            filtered.append(r)
                        elif filter_field == "Ед. изм." and search_text in (r.unit.name if r.unit else "").lower():
                            filtered.append(r)
                        elif filter_field == "Тип" and search_text in (r.type.name if r.type else "").lower():
                            filtered.append(r)
                        elif filter_field == "Условие" and search_text in (r.condition.name if r.condition else "").lower():
                            filtered.append(r)
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
        filter_combo.currentIndexChanged.connect(update_table)
        update_table()
        if self.right_panel.count() > 1:
            self.right_panel.removeWidget(self.right_panel.widget(1))
        self.right_panel.addWidget(widget)
        self.right_panel.setCurrentIndex(1)

    def update_deliveries(self):
        with Session() as s:
            deliveries = s.query(Delivery).all()
            self.delivery_list.clear()
            for d in deliveries:
                doc = d.doc_number or f"Поставка #{d.id}"
                item = QListWidgetItem(doc)
                item.setData(Qt.UserRole, d.id)
                self.delivery_list.addItem(item)

    def show_delivery(self):
        item = self.delivery_list.currentItem()
        if not item:
            self.right_panel.setCurrentIndex(0)
            return
        delivery_id = item.data(Qt.UserRole)
        widget = QWidget()
        layout = QVBoxLayout(widget)
        filter_layout = QHBoxLayout()
        search = QLineEdit()
        search.setPlaceholderText("Поиск по номеру/поставщику")
        filter_combo = QComboBox()
        filter_combo.addItems(["Все", "Номер док.", "Поставщик"])
        start_date = QDateEdit(QDate.currentDate().addMonths(-1))
        start_date.setCalendarPopup(True)
        end_date = QDateEdit(QDate.currentDate())
        end_date.setCalendarPopup(True)
        filter_layout.addWidget(QLabel("Поиск:"))
        filter_layout.addWidget(search)
        filter_layout.addWidget(QLabel("Фильтр:"))
        filter_layout.addWidget(filter_combo)
        filter_layout.addWidget(QLabel("Дата с:"))
        filter_layout.addWidget(start_date)
        filter_layout.addWidget(QLabel("по:"))
        filter_layout.addWidget(end_date)
        layout.addLayout(filter_layout)
        info = QFormLayout()
        supplier = QLabel()
        planned = QLabel()
        actual = QLabel()
        doc_num = QLabel()
        doc_date = QLabel()
        info.addRow("Поставщик:", supplier)
        info.addRow("План. дата:", planned)
        info.addRow("Факт. дата:", actual)
        info.addRow("Номер док.:", doc_num)
        info.addRow("Дата док.:", doc_date)
        layout.addLayout(info)
        buttons = QHBoxLayout()
        edit_btn = QPushButton("Редактировать")
        edit_btn.clicked.connect(self.edit_delivery)
        delete_btn = QPushButton("Удалить")
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

        def update_delivery():
            search_text = search.text().lower()
            filter_field = filter_combo.currentText()
            start = start_date.date().toPython()
            end = end_date.date().toPython()
            with Session() as s:
                query = s.query(Delivery).options(joinedload(Delivery.supplier)).filter(
                    Delivery.id == delivery_id,
                    Delivery.planned_date >= start,
                    Delivery.planned_date <= end
                )
                if search_text:
                    if filter_field in ["Все", "Номер док."]:
                        query = query.filter(Delivery.doc_number.ilike(f"%{search_text}%"))
                    elif filter_field == "Поставщик":
                        query = query.join(Supplier).filter(Supplier.name.ilike(f"%{search_text}%"))
                delivery = query.first()
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
                ).all()
                table.setRowCount(len(products))
                for row, p in enumerate(products):
                    table.setItem(row, 0, QTableWidgetItem(p.product.name if p.product else ""))
                    table.setItem(row, 1, QTableWidgetItem(str(p.planned_quantity or 0)))
                    table.setItem(row, 2, QTableWidgetItem(f"{p.planned_price or 0:.2f}"))
                    table.setItem(row, 3, QTableWidgetItem(str(p.actual_quantity or 0)))
                    table.setItem(row, 4, QTableWidgetItem(f"{p.actual_price or 0:.2f}"))
                    table.setRowHeight(row, 50)

        search.textChanged.connect(update_delivery)
        filter_combo.currentIndexChanged.connect(update_delivery)
        start_date.dateChanged.connect(update_delivery)
        end_date.dateChanged.connect(update_delivery)
        update_delivery()
        if self.right_panel.count() > 0:
            self.right_panel.removeWidget(self.right_panel.widget(1))
        self.right_panel.addWidget(widget)
        self.right_panel.setCurrentIndex(1)

    def add_record(self):
        item = self.ref_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Ошибка", "Выберите справочник")
            return
        dialog = AddEditRecordDialog(item.text())
        if dialog.exec():
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
                if dialog.exec():
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
        if dialog.exec():
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
            delivery = s.query(Delivery).get(delivery_id)
            if not delivery:
                QMessageBox.warning(self, "Ошибка", "Поставка не найдена")
                return
            dialog = AddEditDeliveryDialog(delivery)
            if dialog.exec():
                data = dialog.get_data()
                if not data['supplier_id'] or not data['products']:
                    QMessageBox.critical(self, "Ошибка", "Выберите поставщика и добавьте товары")
                    return
                try:
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
        try:
            with Session() as s:
                start = self.start_date.date().toPython()
                end = self.end_date.date().toPython()
                supplier_id = self.supplier_filter.currentData()
                query = s.query(Delivery).options(joinedload(Delivery.supplier)).filter(
                    Delivery.planned_date >= start,
                    Delivery.planned_date <= end
                )
                if supplier_id:
                    query = query.filter(Delivery.supplier_id == supplier_id)
                deliveries = query.all()
                products = s.query(ProductInDelivery).join(Delivery).options(
                    joinedload(ProductInDelivery.product)
                ).filter(
                    Delivery.planned_date >= start,
                    Delivery.planned_date <= end
                ).all()
                if not deliveries or not products:
                    logging.warning("Нет данных для отчёта")
                    QMessageBox.warning(self, "Ошибка", "Нет данных за указанный период")
                    return
                deliveries_data = []
                for d in deliveries:
                    delivery_products = [
                        {
                            "name": p.product.name if p.product else "-",
                            "planned_quantity": p.planned_quantity or 0,
                            "planned_price": p.planned_price or 0.0,
                            "actual_quantity": p.actual_quantity or 0,
                            "actual_price": p.actual_price or 0.0
                        }
                        for p in products if p.delivery_id == d.id
                    ]
                    if delivery_products:
                        deliveries_data.append({
                            "id": d.id,
                            "supplier_name": d.supplier.name if d.supplier else "-",
                            "planned_date": d.planned_date if d.planned_date else start,
                            "actual_date": d.actual_date if d.actual_date else start,
                            "doc_number": d.doc_number or "-",
                            "doc_date": d.doc_date if d.doc_date else start,
                            "products": delivery_products
                        })
                if not deliveries_data:
                    logging.warning("Нет подходящих данных после фильтрации")
                    QMessageBox.warning(self, "Ошибка", "Нет подходящих данных для отчёта")
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
                logging.info(f"Отчёт успешно сгенерирован: {report_type}")
        except Exception as e:
            logging.error(f"Ошибка генерации отчёта: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось сгенерировать отчёт: {str(e)}")

    def display_report(self, report):
        try:
            model = QStandardItemModel()
            table = report['table']
            model.setHorizontalHeaderLabels(table[0])
            for row in table[1:]:
                items = [QStandardItem(str(cell) if isinstance(cell, (int, float)) else cell or '-') for cell in row]
                model.appendRow(items)
            self.report_view.setModel(model)
            self.report_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            for row in range(model.rowCount()):
                self.report_view.setRowHeight(row, 50)
            logging.info("Отчёт успешно отображён")
        except Exception as e:
            logging.error(f"Ошибка отображения отчёта: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось отобразить отчёт: {str(e)}")

    def generate_planned_report(self, deliveries, products, start, end):
        header = [
            "Плановые поставки",
            f"Период: {start.strftime('%d.%m.%Y')} - {end.strftime('%d.%m.%Y')}",
            f"Поставщик: {self.supplier_filter.currentText()}"
        ]
        table = [["Поставщик", "План. дата", "План. сумма"]]
        for d in deliveries:
            total = sum((p.planned_quantity or 0) * (p.planned_price or 0) for p in products if p.delivery_id == d.id)
            table.append([
                d.supplier.name if d.supplier else "-",
                d.planned_date.strftime("%d.%m.%Y") if d.planned_date else "-",
                f"{total:.2f}"
            ])
        total_sum = sum((p.planned_quantity or 0) * (p.planned_price or 0) for p in products)
        table.append(["ИТОГО", "-", f"{total_sum:.2f}"])
        return {'header': header, 'table': table, 'col_widths': [60, 40, 40]}

    def generate_completed_report(self, deliveries, products, start, end):
        header = [
            "Выполненные поставки",
            f"Период: {start.strftime('%d.%m.%Y')} - {end.strftime('%d.%m.%Y')}",
            f"Поставщик: {self.supplier_filter.currentText()}"
        ]
        table = [["Поставщик", "Номер док.", "Факт. дата", "Факт. сумма"]]
        completed = [
            d for d in deliveries
            if all(
                (p.planned_quantity or 0) == (p.actual_quantity or 0) and
                (p.planned_price or 0) == (p.actual_price or 0)
                for p in products if p.delivery_id == d.id
            )
        ]
        for d in completed:
            total = sum((p.actual_quantity or 0) * (p.actual_price or 0) for p in products if p.delivery_id == d.id)
            table.append([
                d.supplier.name if d.supplier else "-",
                d.doc_number or "-",
                d.actual_date.strftime("%d.%m.%Y") if d.actual_date else "-",
                f"{total:.2f}"
            ])
        total_sum = sum((p.actual_quantity or 0) * (p.actual_price or 0) for p in products if any(d.id == p.delivery_id for d in completed))
        table.append(["ИТОГО", "-", "-", f"{total_sum:.2f}"])
        return {'header': header, 'table': table, 'col_widths': [60, 40, 40, 40]}

    def generate_detailed_report(self, deliveries, products, start, end):
        header = [
            "Детализация",
            f"Период: {start.strftime('%d.%m.%Y')} - {end.strftime('%d.%m.%Y')}",
            f"Поставщик: {self.supplier_filter.currentText()}"
        ]
        table = [["Поставщик", "Номер док.", "План. дата", "Факт. дата", "Дата док.", "Товар", "План. кол/цена", "Факт. кол/цена"]]
        for d in deliveries:
            for p in products:
                if p.delivery_id == d.id:
                    table.append([
                        d.supplier.name if d.supplier else "-",
                        d.doc_number or "-",
                        d.planned_date.strftime("%d.%m.%Y") if d.planned_date else "-",
                        d.actual_date.strftime("%d.%m.%Y") if d.actual_date else "-",
                        d.doc_date.strftime("%d.%m.%Y") if d.doc_date else "-",
                        p.product.name if p.product else "-",
                        f"{p.planned_quantity or 0}/{p.planned_price or 0:.2f}",
                        f"{p.actual_quantity or 0}/{p.actual_price or 0:.2f}"
                    ])
        return {'header': header, 'table': table, 'col_widths': [50, 30, 30, 30, 30, 50, 40, 40]}

    def save_report(self):
        if not self.current_report:
            QMessageBox.warning(self, "Ошибка", "Сначала сформируйте отчёт")
            return
        file_name, _ = QFileDialog.getSaveFileName(self, "Сохранить отчёт", "", "PDF (*.pdf)")
        if file_name:
            if not file_name.endswith('.pdf'):
                file_name += '.pdf'
            try:
                doc = SimpleDocTemplate(file_name, pagesize=landscape(A4), rightMargin=10*mm, leftMargin=10*mm, topMargin=10*mm, bottomMargin=10*mm)
                elements = []
                styles = getSampleStyleSheet()
                try:
                    pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
                    font = 'DejaVuSans'
                except Exception:
                    font = 'Helvetica'
                styles.add(ParagraphStyle(name='Header', fontName=font, fontSize=14, alignment=1))
                styles.add(ParagraphStyle(name='Table', fontName=font, fontSize=10))
                try:
                    elements.append(Image("logo.svg", width=50*mm, height=20*mm))
                    elements.append(Spacer(1, 5*mm))
                except Exception:
                    pass
                for line in self.current_report['header']:
                    elements.append(Paragraph(line, styles['Header']))
                elements.append(Spacer(1, 10*mm))
                table_data = [[Paragraph(str(cell), styles['Table']) for cell in row] for row in self.current_report['table']]
                col_widths = [w * mm for w in self.current_report.get('col_widths', [40] * len(table_data[0]))]
                table = Table(table_data, colWidths=col_widths)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
                ]))
                elements.append(table)
                elements.append(Spacer(1, 10*mm))
                elements.append(Paragraph("Список поставок", styles['Table']))
                for d in self.current_report.get('deliveries_data', []):
                    text = f"Поставщик: {d['supplier_name']}, Номер: {d['doc_number']}, План: {d['planned_date'].strftime('%d.%m.%Y') if d['planned_date'] else '-'}, Факт: {d['actual_date'].strftime('%d.%m.%Y') if d['actual_date'] else '-'}"
                    elements.append(Paragraph(text, styles['Table']))
                    for p in d.get('products', []):
                        name = p.get('name', '-')
                        planned_qty = p.get('planned_quantity', 0)
                        planned_price = p.get('planned_price', 0.0)
                        actual_qty = p.get('actual_quantity', 0)
                        actual_price = p.get('actual_price', 0.0)
                        elements.append(Paragraph(
                            f" - {name}: План {planned_qty}/{planned_price:.2f}, Факт {actual_qty}/{actual_price:.2f}",
                            styles['Table']
                        ))
                doc.build(elements)
                QMessageBox.information(self, "Успех", "Отчёт сохранён")
                logging.info(f"Отчёт сохранён: {file_name}")
            except Exception as e:
                logging.error(f"Ошибка сохранения отчёта: {e}")
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())