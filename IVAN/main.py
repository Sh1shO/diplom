import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QLineEdit, QPushButton, QListWidget, QStackedWidget, QLabel, QComboBox,
    QTableWidgetItem, QMessageBox, QDialog, QFormLayout, QDateEdit, QListWidgetItem,
    QHeaderView, QTabWidget
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QIcon, QPixmap
from sqlalchemy.orm import joinedload
from db import (
    User, Role, Unit, ProductType, DeliveryCondition, Supplier, Product, Delivery,
    ProductInDelivery, Session
)
from styles import STYLESHEET

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("loginDialog")
        self.setWindowTitle("Авторизация")
        self.setFixedSize(600, 800)

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(50, 50, 50, 50)

        logo_label = QLabel()
        logo_label.setObjectName("logo_label")
        pixmap = QPixmap(150, 150)
        pixmap.fill(Qt.transparent)
        logo_label.setPixmap(pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(logo_label)

        title_label = QLabel("Добро пожаловать!")
        title_label.setObjectName("login_title_label")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        subtitle_label = QLabel("Войдите, чтобы управлять товаром")
        subtitle_label.setObjectName("login_subtitle_label")
        subtitle_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(subtitle_label)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignLeft)
        form_layout.setFormAlignment(Qt.AlignCenter)
        form_layout.setSpacing(15)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Имя пользователя")
        self.username_input.setMinimumHeight(50)
        self.username_input.setMaximumWidth(400)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Пароль")
        self.password_input.setMinimumHeight(50)
        self.password_input.setMaximumWidth(400)

        form_layout.addRow("Пользователь:", self.username_input)
        form_layout.addRow("Пароль:", self.password_input)
        main_layout.addLayout(form_layout)

        self.login_button = QPushButton("Войти")
        self.login_button.setObjectName("login_button")
        self.login_button.clicked.connect(self.accept)
        self.login_button.setMinimumHeight(60)
        self.login_button.setMinimumWidth(300)
        main_layout.addWidget(self.login_button, alignment=Qt.AlignCenter)

        main_layout.addStretch()

    def get_credentials(self):
        return self.username_input.text().strip(), self.password_input.text().strip()

class AddEditRecordDialog(QDialog):
    def __init__(self, parent, table_name, record=None):
        super().__init__(parent)
        self.setWindowTitle(f"{'Редактировать' if record else 'Добавить'} {table_name}")
        self.setMinimumSize(700, 600)
        self.table_name = table_name
        self.record = record
        layout = QFormLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        self.inputs = {}
        if table_name == "Единицы измерения":
            self.inputs['name'] = QLineEdit(record.name if record else "")
            self.inputs['name'].setMinimumHeight(45)
            layout.addRow("Название:", self.inputs['name'])
        elif table_name == "Типы товаров":
            self.inputs['name'] = QLineEdit(record.name if record else "")
            self.inputs['name'].setMinimumHeight(45)
            layout.addRow("Название:", self.inputs['name'])
        elif table_name == "Условия поставки":
            self.inputs['name'] = QLineEdit(record.name if record else "")
            self.inputs['name'].setMinimumHeight(45)
            layout.addRow("Название:", self.inputs['name'])
        elif table_name == "Поставщики":
            self.inputs['inn'] = QLineEdit(record.inn if record else "")
            self.inputs['name'] = QLineEdit(record.name if record else "")
            self.inputs['phone'] = QLineEdit(record.phone if record else "")
            self.inputs['inn'].setMinimumHeight(45)
            self.inputs['name'].setMinimumHeight(45)
            self.inputs['phone'].setMinimumHeight(45)
            layout.addRow("ИНН:", self.inputs['inn'])
            layout.addRow("Название:", self.inputs['name'])
            layout.addRow("Телефон:", self.inputs['phone'])
        elif table_name == "Товары":
            self.inputs['name'] = QLineEdit(record.name if record else "")
            self.inputs['name'].setMinimumHeight(45)
            self.inputs['unit_id'] = QComboBox()
            self.inputs['type_id'] = QComboBox()
            self.inputs['condition_id'] = QComboBox()
            self.inputs['unit_id'].setMinimumHeight(45)
            self.inputs['type_id'].setMinimumHeight(45)
            self.inputs['condition_id'].setMinimumHeight(45)
            with Session() as s:
                units = s.query(Unit).all()
                types = s.query(ProductType).all()
                conditions = s.query(DeliveryCondition).all()
                self.inputs['unit_id'].addItem("Не выбрано", None)
                self.inputs['unit_id'].addItems([u.name for u in units])
                self.inputs['type_id'].addItem("Не выбрано", None)
                self.inputs['type_id'].addItems([t.name for t in types])
                self.inputs['condition_id'].addItem("Не выбрано", None)
                self.inputs['condition_id'].addItems([c.name for c in conditions])
                if record:
                    self.inputs['unit_id'].setCurrentText(record.unit.name if record.unit else "")
                    self.inputs['type_id'].setCurrentText(record.type.name if record.type else "")
                    self.inputs['condition_id'].setCurrentText(record.condition.name if record.condition else "")
            layout.addRow("Название:", self.inputs['name'])
            layout.addRow("Единица измерения:", self.inputs['unit_id'])
            layout.addRow("Тип товара:", self.inputs['type_id'])
            layout.addRow("Условие поставки:", self.inputs['condition_id'])

        self.save_button = QPushButton("Сохранить")
        self.save_button.setMinimumHeight(60)
        self.save_button.setMinimumWidth(250)
        self.save_button.clicked.connect(self.accept)
        layout.addRow(self.save_button)

    def get_data(self):
        data = {key: widget.text() if isinstance(widget, QLineEdit) else widget.currentData() or widget.currentText()
                for key, widget in self.inputs.items()}
        return data

class AddEditDeliveryDialog(QDialog):
    def __init__(self, parent, delivery=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить поставку" if not delivery else "Редактировать поставку")
        self.setMinimumSize(1200, 900)
        self.delivery = delivery
        layout = QVBoxLayout(self)
        layout.setSpacing(25)
        layout.setContentsMargins(40, 40, 40, 40)

        form_layout = QFormLayout()
        form_layout.setSpacing(20)
        self.supplier_combo = QComboBox()
        self.supplier_combo.setMinimumHeight(45)
        self.planned_date = QDateEdit()
        self.planned_date.setCalendarPopup(True)
        self.planned_date.setDate(QDate.currentDate())
        self.planned_date.setMinimumHeight(45)
        self.actual_date = QDateEdit()
        self.actual_date.setCalendarPopup(True)
        self.actual_date.setDate(QDate.currentDate())
        self.actual_date.setMinimumHeight(45)
        self.doc_number = QLineEdit()
        self.doc_number.setMinimumHeight(45)
        self.doc_date = QDateEdit()
        self.doc_date.setCalendarPopup(True)
        self.doc_date.setDate(QDate.currentDate())
        self.doc_date.setMinimumHeight(45)
        
        with Session() as s:
            suppliers = s.query(Supplier).all()
            self.supplier_combo.addItem("Не выбрано", None)
            self.supplier_combo.addItems([s.name for s in suppliers])
            if delivery and delivery.supplier:
                self.supplier_combo.setCurrentText(delivery.supplier.name)
        
        form_layout.addRow("Поставщик:", self.supplier_combo)
        form_layout.addRow("План. дата:", self.planned_date)
        form_layout.addRow("Факт. дата:", self.actual_date)
        form_layout.addRow("Номер док.:", self.doc_number)
        form_layout.addRow("Дата док.:", self.doc_date)
        layout.addLayout(form_layout)
        
        if delivery:
            self.planned_date.setDate(QDate(delivery.planned_date.year, delivery.planned_date.month, delivery.planned_date.day) if delivery.planned_date else QDate.currentDate())
            self.actual_date.setDate(QDate(delivery.actual_date.year, delivery.actual_date.month, delivery.actual_date.day) if delivery.actual_date else QDate.currentDate())
            self.doc_number.setText(delivery.doc_number or "")
            self.doc_date.setDate(QDate(delivery.doc_date.year, delivery.doc_date.month, delivery.doc_date.day) if delivery.doc_date else QDate.currentDate())
        
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(5)
        self.products_table.setHorizontalHeaderLabels([
            "Товар", "План. кол-во", "План. цена", "Факт. кол-во", "Факт. цена"
        ])
        self.products_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.products_table.setMinimumHeight(500)
        self.products_table.setRowHeight(0, 60)
        layout.addWidget(self.products_table)
        
        if delivery:
            with Session() as s:
                products_in_delivery = s.query(ProductInDelivery).options(joinedload(ProductInDelivery.product)).filter(ProductInDelivery.delivery_id == delivery.id).all()
                self.products_table.setRowCount(len(products_in_delivery))
                for row, pid in enumerate(products_in_delivery):
                    self.products_table.setRowHeight(row, 60)
                    product_combo = QComboBox()
                    product_combo.setMinimumHeight(40)
                    with Session() as s:
                        products = s.query(Product).all()
                        product_combo.addItem("Не выбрано", None)
                        product_combo.addItems([p.name for p in products])
                        product_combo.setCurrentText(pid.product.name if pid.product else "")
                    self.products_table.setCellWidget(row, 0, product_combo)
                    self.products_table.setItem(row, 1, QTableWidgetItem(str(pid.planned_quantity or 0)))
                    self.products_table.setItem(row, 2, QTableWidgetItem(str(pid.planned_price or 0)))
                    self.products_table.setItem(row, 3, QTableWidgetItem(str(pid.actual_quantity or 0)))
                    self.products_table.setItem(row, 4, QTableWidgetItem(str(pid.actual_price or 0)))
        
        products_buttons_layout = QHBoxLayout()
        self.add_product_button = QPushButton("Добавить товар")
        self.add_product_button.setObjectName("add_button")
        self.add_product_button.clicked.connect(self.add_product_row)
        self.add_product_button.setMinimumHeight(60)
        self.add_product_button.setMinimumWidth(250)
        self.remove_product_button = QPushButton("Удалить товар")
        self.remove_product_button.setObjectName("delete_button")
        self.remove_product_button.clicked.connect(self.remove_product_row)
        self.remove_product_button.setMinimumHeight(60)
        self.remove_product_button.setMinimumWidth(250)
        products_buttons_layout.addWidget(self.add_product_button)
        products_buttons_layout.addWidget(self.remove_product_button)
        layout.addLayout(products_buttons_layout)
        
        self.save_button = QPushButton("Сохранить")
        self.save_button.setMinimumHeight(60)
        self.save_button.setMinimumWidth(300)
        layout.addWidget(self.save_button, alignment=Qt.AlignCenter)
        self.save_button.clicked.connect(self.accept)
        
    def add_product_row(self):
        row = self.products_table.rowCount()
        self.products_table.insertRow(row)
        self.products_table.setRowHeight(row, 60)
        
        product_combo = QComboBox()
        product_combo.setMinimumHeight(35)
        product_combo.setMinimumWidth(150)
        with Session() as s:
            products = s.query(Product).all()
            product_combo.addItem("Не выбрано", None)
            product_combo.addItems([p.name for p in products])
        
        self.products_table.setCellWidget(row, 0, product_combo)
        self.products_table.setItem(row, 1, QTableWidgetItem("0"))
        self.products_table.setItem(row, 2, QTableWidgetItem("0"))
        self.products_table.setItem(row, 3, QTableWidgetItem("0"))
        self.products_table.setItem(row, 4, QTableWidgetItem("0"))
        self.products_table.clearSelection()
    
    def remove_product_row(self):
        selected_rows = self.products_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Предупреждение", "Выберите строку для удаления")
            return
        for row in sorted([r.row() for r in selected_rows], reverse=True):
            self.products_table.removeRow(row)
    
    def get_data(self):
        products = []
        for row in range(self.products_table.rowCount()):
            product_combo = self.products_table.cellWidget(row, 0)
            product_name = product_combo.currentText()
            with Session() as s:
                product = s.query(Product).filter(Product.name == product_name).first()
                product_id = product.id if product else None
            try:
                products.append({
                    'product_id': product_id,
                    'planned_quantity': int(self.products_table.item(row, 1).text() or 0),
                    'planned_price': float(self.products_table.item(row, 2).text() or 0),
                    'actual_quantity': int(self.products_table.item(row, 3).text() or 0),
                    'actual_price': float(self.products_table.item(row, 4).text() or 0)
                })
            except:
                products.append({
                    'product_id': product_id,
                    'planned_quantity': 0,
                    'planned_price': 0.0,
                    'actual_quantity': 0,
                    'actual_price': 0.0
                })
        return {
            'supplier_id': self.supplier_combo.currentData() or self.supplier_combo.currentText(),
            'planned_date': self.planned_date.date().toPython(),
            'actual_date': self.actual_date.date().toPython(),
            'doc_number': self.doc_number.text(),
            'doc_date': self.doc_date.date().toPython(),
            'products': products
        }

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Магазин")
        self.setStyleSheet(STYLESHEET)
        self.setMinimumSize(1400, 900)
        self.current_user = None
        self.show_login_dialog()
    
    def show_login_dialog(self):
        dialog = LoginDialog(self)
        if dialog.exec():
            username, password = dialog.get_credentials()
            with Session() as s:
                try:
                    user = s.query(User).filter(User.username == username).first()
                    if user and user.password == password:
                        self.current_user = user
                        self.setup_ui()
                    else:
                        QMessageBox.critical(self, "Ошибка", "Неверное имя пользователя или пароль")
                        self.show_login_dialog()
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка", f"Ошибка подключения к базе данных: {str(e)}")
                    self.show_login_dialog()
        else:
            sys.exit()
    
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        left_panel = QWidget()
        left_panel.setMinimumWidth(350)
        left_layout = QVBoxLayout(left_panel)
        
        self.tabs = QTabWidget()
        left_layout.addWidget(self.tabs)
        
        references_tab = QWidget()
        references_layout = QVBoxLayout(references_tab)
        references_layout.addWidget(QLabel("Справочники"))
        self.references_list = QListWidget()
        self.references_list.addItems([
            "Единицы измерения", "Типы товаров", "Условия поставки",
            "Поставщики", "Товары"
        ])
        self.references_list.setMinimumHeight(400)
        self.references_list.currentItemChanged.connect(self.show_reference_table)
        references_layout.addWidget(self.references_list)
        self.tabs.addTab(references_tab, "Справочники")
        
        deliveries_tab = QWidget()
        deliveries_layout = QVBoxLayout(deliveries_tab)
        deliveries_layout.addWidget(QLabel("Поставки"))
        self.deliveries_list = QListWidget()
        self.deliveries_list.setMinimumHeight(400)
        self.deliveries_list.currentItemChanged.connect(self.show_delivery_details)
        deliveries_layout.addWidget(self.deliveries_list)
        self.add_delivery_button = QPushButton("Добавить поставку")
        self.add_delivery_button.setObjectName("add_button")
        self.add_delivery_button.clicked.connect(self.add_delivery)
        self.add_delivery_button.setMinimumHeight(60)
        self.add_delivery_button.setMinimumWidth(300)
        deliveries_layout.addWidget(self.add_delivery_button)
        self.tabs.addTab(deliveries_tab, "Поставки")
        
        main_layout.addWidget(left_panel, 1)
        
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)
        self.stack = QStackedWidget()
        self.right_layout.addWidget(self.stack)
        
        empty_widget = QWidget()
        self.stack.addWidget(empty_widget)
        
        main_layout.addWidget(self.right_panel, 3)
        
        self.update_deliveries_list()
        self.showMaximized()
    
    def show_reference_table(self):
        if not self.references_list.currentItem():
            return
        
        table_name = self.references_list.currentItem().text()
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(25)
        layout.setContentsMargins(20, 20, 20, 20)
        
        buttons_layout = QHBoxLayout()
        add_button = QPushButton("Добавить")
        add_button.setObjectName("add_button")
        add_button.clicked.connect(self.add_record)
        add_button.setMinimumHeight(60)
        add_button.setMinimumWidth(250)
        edit_button = QPushButton("Редактировать")
        edit_button.setObjectName("edit_button")
        edit_button.clicked.connect(self.edit_record)
        edit_button.setMinimumHeight(60)
        edit_button.setMinimumWidth(250)
        delete_button = QPushButton("Удалить")
        delete_button.setObjectName("delete_button")
        delete_button.clicked.connect(self.delete_record)
        delete_button.setMinimumHeight(60)
        delete_button.setMinimumWidth(250)
        buttons_layout.addWidget(add_button)
        buttons_layout.addWidget(edit_button)
        buttons_layout.addWidget(delete_button)
        layout.addLayout(buttons_layout)
        
        table = QTableWidget()
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.setMinimumHeight(500)
        table.setRowHeight(0, 60)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        with Session() as s:
            try:
                if table_name == "Единицы измерения":
                    records = s.query(Unit).all()
                    table.setColumnCount(1)
                    table.setHorizontalHeaderLabels(["Название"])
                    table.setRowCount(len(records))
                    for row, record in enumerate(records):
                        table.setRowHeight(row, 60)
                        item = QTableWidgetItem(record.name or "")
                        item.setData(Qt.UserRole, record.id)
                        table.setItem(row, 0, item)
                elif table_name == "Типы товаров":
                    records = s.query(ProductType).all()
                    table.setColumnCount(1)
                    table.setHorizontalHeaderLabels(["Название"])
                    table.setRowCount(len(records))
                    for row, record in enumerate(records):
                        table.setRowHeight(row, 60)
                        item = QTableWidgetItem(record.name or "")
                        item.setData(Qt.UserRole, record.id)
                        table.setItem(row, 0, item)
                elif table_name == "Условия поставки":
                    records = s.query(DeliveryCondition).all()
                    table.setColumnCount(1)
                    table.setHorizontalHeaderLabels(["Название"])
                    table.setRowCount(len(records))
                    for row, record in enumerate(records):
                        table.setRowHeight(row, 60)
                        item = QTableWidgetItem(record.name or "")
                        item.setData(Qt.UserRole, record.id)
                        table.setItem(row, 0, item)
                elif table_name == "Поставщики":
                    records = s.query(Supplier).all()
                    table.setColumnCount(3)
                    table.setHorizontalHeaderLabels(["ИНН", "Название", "Телефон"])
                    table.setRowCount(len(records))
                    for row, record in enumerate(records):
                        table.setRowHeight(row, 60)
                        item = QTableWidgetItem(record.inn or "")
                        item.setData(Qt.UserRole, record.id)
                        table.setItem(row, 0, item)
                        table.setItem(row, 1, QTableWidgetItem(record.name or ""))
                        table.setItem(row, 2, QTableWidgetItem(record.phone or ""))
                elif table_name == "Товары":
                    records = s.query(Product).options(
                        joinedload(Product.unit),
                        joinedload(Product.type),
                        joinedload(Product.condition)
                    ).all()
                    table.setColumnCount(4)
                    table.setHorizontalHeaderLabels([
                        "Название", "Единица измерения", "Тип товара", "Условие поставки"
                    ])
                    table.setRowCount(len(records))
                    for row, record in enumerate(records):
                        table.setRowHeight(row, 60)
                        item = QTableWidgetItem(record.name or "")
                        item.setData(Qt.UserRole, record.id)
                        table.setItem(row, 0, item)
                        table.setItem(row, 1, QTableWidgetItem(record.unit.name if record.unit else ""))
                        table.setItem(row, 2, QTableWidgetItem(record.type.name if record.type else ""))
                        table.setItem(row, 3, QTableWidgetItem(record.condition.name if record.condition else ""))
                
                table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
                layout.addWidget(table)
                
                self.stack.addWidget(widget)
                self.stack.setCurrentWidget(widget)
                while self.stack.count() > 2:
                    old_widget = self.stack.widget(1)
                    self.stack.removeWidget(old_widget)
                    old_widget.deleteLater()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить таблицу: {str(e)}")
    
    def update_deliveries_list(self):
        with Session() as s:
            try:
                deliveries = s.query(Delivery).all()
                self.deliveries_list.clear()
                for delivery in deliveries:
                    item = QListWidgetItem(delivery.doc_number or f"Поставка #{delivery.id}")
                    item.setData(Qt.UserRole, delivery.id)
                    self.deliveries_list.addItem(item)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось обновить список поставок: {str(e)}")
    
    def show_delivery_details(self):
        if not self.deliveries_list.currentItem():
            return
        
        delivery_id = self.deliveries_list.currentItem().data(Qt.UserRole)
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(25)
        layout.setContentsMargins(20, 20, 20, 20)
        
        with Session() as s:
            try:
                delivery = s.query(Delivery).options(joinedload(Delivery.supplier)).filter(Delivery.id == delivery_id).first()
                if delivery:
                    info_layout = QFormLayout()
                    info_layout.addRow("Поставщик:", QLabel(delivery.supplier.name if delivery.supplier else "Не указан"))
                    info_layout.addRow("План. дата:", QLabel(delivery.planned_date.strftime("%d.%m.%Y") if delivery.planned_date else ""))
                    info_layout.addRow("Факт. дата:", QLabel(delivery.actual_date.strftime("%d.%m.%Y") if delivery.actual_date else ""))
                    info_layout.addRow("Номер док.:", QLabel(delivery.doc_number or ""))
                    info_layout.addRow("Дата док.:", QLabel(delivery.doc_date.strftime("%d.%m.%Y") if delivery.doc_date else ""))
                    layout.addLayout(info_layout)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить информацию о поставке: {str(e)}")
        
        buttons_layout = QHBoxLayout()
        edit_button = QPushButton("Редактировать")
        edit_button.setObjectName("edit_button")
        edit_button.clicked.connect(self.edit_delivery)
        edit_button.setMinimumHeight(60)
        edit_button.setMinimumWidth(250)
        delete_button = QPushButton("Удалить")
        delete_button.setObjectName("delete_button")
        delete_button.clicked.connect(self.delete_delivery)
        delete_button.setMinimumHeight(60)
        delete_button.setMinimumWidth(250)
        buttons_layout.addWidget(edit_button)
        buttons_layout.addWidget(delete_button)
        layout.addLayout(buttons_layout)
        
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels([
            "Товар", "План. кол-во", "План. цена", "Факт. кол-во", "Факт. цена"
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setMinimumHeight(500)
        table.setRowHeight(0, 60)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        with Session() as s:
            try:
                products_in_delivery = s.query(ProductInDelivery).options(joinedload(ProductInDelivery.product)).filter(ProductInDelivery.delivery_id == delivery_id).all()
                table.setRowCount(len(products_in_delivery))
                for row, pid in enumerate(products_in_delivery):
                    table.setRowHeight(row, 60)
                    table.setItem(row, 0, QTableWidgetItem(pid.product.name if pid.product else ""))
                    table.setItem(row, 1, QTableWidgetItem(str(pid.planned_quantity or 0)))
                    table.setItem(row, 2, QTableWidgetItem(str(pid.planned_price or 0)))
                    table.setItem(row, 3, QTableWidgetItem(str(pid.actual_quantity or 0)))
                    table.setItem(row, 4, QTableWidgetItem(str(pid.actual_price or 0)))
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить товары поставки: {str(e)}")
        
        layout.addWidget(table)
        
        self.stack.addWidget(widget)
        self.stack.setCurrentWidget(widget)
        while self.stack.count() > 2:
            old_widget = self.stack.widget(1)
            self.stack.removeWidget(old_widget)
            old_widget.deleteLater()
    
    def add_record(self):
        if not self.references_list.currentItem():
            QMessageBox.warning(self, "Предупреждение", "Выберите справочник")
            return
        table_name = self.references_list.currentItem().text()
        dialog = AddEditRecordDialog(self, table_name)
        if dialog.exec():
            data = dialog.get_data()
            with Session() as s:
                try:
                    if table_name == "Единицы измерения":
                        record = Unit(name=data['name'])
                    elif table_name == "Типы товаров":
                        record = ProductType(name=data['name'])
                    elif table_name == "Условия поставки":
                        record = DeliveryCondition(name=data['name'])
                    elif table_name == "Поставщики":
                        record = Supplier(inn=data['inn'], name=data['name'], phone=data['phone'])
                    elif table_name == "Товары":
                        unit = s.query(Unit).filter(Unit.name == data['unit_id']).first()
                        type_ = s.query(ProductType).filter(ProductType.name == data['type_id']).first()
                        condition = s.query(DeliveryCondition).filter(DeliveryCondition.name == data['condition_id']).first()
                        record = Product(
                            name=data['name'],
                            unit_id=unit.id if unit else None,
                            type_id=type_.id if type_ else None,
                            condition_id=condition.id if condition else None
                        )
                    s.add(record)
                    s.commit()
                    self.show_reference_table()
                    QMessageBox.information(self, "Успех", "Запись добавлена")
                except Exception as e:
                    s.rollback()
                    QMessageBox.critical(self, "Ошибка", f"Не удалось добавить запись: {str(e)}")
    
    def edit_record(self):
        if not hasattr(self, 'stack') or self.stack.currentWidget() == self.stack.widget(0):
            QMessageBox.warning(self, "Предупреждение", "Выберите справочник")
            return
        
        table_widget = self.stack.currentWidget().findChild(QTableWidget)
        selected_rows = table_widget.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Предупреждение", "Выберите запись для редактирования")
            return
        
        row = selected_rows[0].row()
        table_name = self.references_list.currentItem().text()
        record_id = table_widget.item(row, 0).data(Qt.UserRole)
        with Session() as s:
            try:
                if table_name == "Единицы измерения":
                    record = s.query(Unit).filter(Unit.id == record_id).first()
                elif table_name == "Типы товаров":
                    record = s.query(ProductType).filter(ProductType.id == record_id).first()
                elif table_name == "Условия поставки":
                    record = s.query(DeliveryCondition).filter(DeliveryCondition.id == record_id).first()
                elif table_name == "Поставщики":
                    record = s.query(Supplier).filter(Supplier.id == record_id).first()
                elif table_name == "Товары":
                    record = s.query(Product).filter(Product.id == record_id).first()
                else:
                    return
                
                dialog = AddEditRecordDialog(self, table_name, record)
                if dialog.exec():
                    data = dialog.get_data()
                    if table_name == "Единицы измерения":
                        record.name = data['name']
                    elif table_name == "Типы товаров":
                        record.name = data['name']
                    elif table_name == "Условия поставки":
                        record.name = data['name']
                    elif table_name == "Поставщики":
                        record.inn = data['inn']
                        record.name = data['name']
                        record.phone = data['phone']
                    elif table_name == "Товары":
                        unit = s.query(Unit).filter(Unit.name == data['unit_id']).first()
                        type_ = s.query(ProductType).filter(ProductType.name == data['type_id']).first()
                        condition = s.query(DeliveryCondition).filter(DeliveryCondition.name == data['condition_id']).first()
                        record.name = data['name']
                        record.unit_id = unit.id if unit else None
                        record.type_id = type_.id if type_ else None
                        record.condition_id = condition.id if condition else None
                    s.commit()
                    self.show_reference_table()
                    QMessageBox.information(self, "Успех", "Запись обновлена")
            except Exception as e:
                s.rollback()
                QMessageBox.critical(self, "Ошибка", f"Не удалось обновить запись: {str(e)}")
    
    def delete_record(self):
        if not hasattr(self, 'stack') or self.stack.currentWidget() == self.stack.widget(0):
            QMessageBox.warning(self, "Предупреждение", "Выберите справочник")
            return
        
        table_widget = self.stack.currentWidget().findChild(QTableWidget)
        selected_rows = table_widget.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Предупреждение", "Выберите запись для удаления")
            return
        
        reply = QMessageBox.question(self, "Подтверждение", "Вы уверены, что хотите удалить эту запись?",
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            with Session() as s:
                try:
                    row = selected_rows[0].row()
                    record_id = table_widget.item(row, 0).data(Qt.UserRole)
                    table_name = self.references_list.currentItem().text()
                    if table_name == "Единицы измерения":
                        record = s.query(Unit).filter(Unit.id == record_id).first()
                    elif table_name == "Типы товаров":
                        record = s.query(ProductType).filter(ProductType.id == record_id).first()
                    elif table_name == "Условия поставки":
                        record = s.query(DeliveryCondition).filter(DeliveryCondition.id == record_id).first()
                    elif table_name == "Поставщики":
                        record = s.query(Supplier).filter(Supplier.id == record_id).first()
                    elif table_name == "Товары":
                        record = s.query(Product).filter(Product.id == record_id).first()
                    if record:
                        s.delete(record)
                        s.commit()
                        self.show_reference_table()
                        QMessageBox.information(self, "Успех", "Запись удалена")
                    else:
                        QMessageBox.warning(self, "Ошибка", "Запись не найдена")
                except Exception as e:
                    s.rollback()
                    QMessageBox.critical(self, "Ошибка", f"Не удалось удалить запись: {str(e)}")
    
    def add_delivery(self):
        dialog = AddEditDeliveryDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            with Session() as s:
                try:
                    supplier = s.query(Supplier).filter(Supplier.name == data['supplier_id']).first()
                    supplier_id = supplier.id if supplier else None
                    
                    new_delivery = Delivery(
                        supplier_id=supplier_id,
                        planned_date=data['planned_date'],
                        actual_date=data['actual_date'],
                        doc_number=data['doc_number'],
                        doc_date=data['doc_date']
                    )
                    s.add(new_delivery)
                    s.flush()
                    
                    for product_data in data['products']:
                        if product_data['product_id']:
                            new_pid = ProductInDelivery(
                                delivery_id=new_delivery.id,
                                product_id=product_data['product_id'],
                                planned_quantity=product_data['planned_quantity'],
                                planned_price=product_data['planned_price'],
                                actual_quantity=product_data['actual_quantity'],
                                actual_price=product_data['actual_price']
                            )
                            s.add(new_pid)
                    
                    s.commit()
                    self.update_deliveries_list()
                    QMessageBox.information(self, "Успех", "Поставка добавлена")
                except Exception as e:
                    s.rollback()
                    QMessageBox.critical(self, "Ошибка", f"Не удалось добавить поставку: {str(e)}")
    
    def edit_delivery(self):
        if not self.deliveries_list.currentItem():
            QMessageBox.warning(self, "Предупреждение", "Выберите поставку для редактирования")
            return
        
        delivery_id = self.deliveries_list.currentItem().data(Qt.UserRole)
        with Session() as s:
            try:
                delivery = s.query(Delivery).filter(Delivery.id == delivery_id).first()
                if not delivery:
                    QMessageBox.warning(self, "Ошибка", "Поставка не найдена")
                    return
                
                dialog = AddEditDeliveryDialog(self, delivery)
                if dialog.exec():
                    data = dialog.get_data()
                    supplier = s.query(Supplier).filter(Supplier.name == data['supplier_id']).first()
                    delivery.supplier_id = supplier.id if supplier else None
                    delivery.planned_date = data['planned_date']
                    delivery.actual_date = data['actual_date']
                    delivery.doc_number = data['doc_number']
                    delivery.doc_date = data['doc_date']
                    
                    s.query(ProductInDelivery).filter(ProductInDelivery.delivery_id == delivery_id).delete()
                    
                    for product_data in data['products']:
                        if product_data['product_id']:
                            new_pid = ProductInDelivery(
                                delivery_id=delivery.id,
                                product_id=product_data['product_id'],
                                planned_quantity=product_data['planned_quantity'],
                                planned_price=product_data['planned_price'],
                                actual_quantity=product_data['actual_quantity'],
                                actual_price=product_data['actual_price']
                            )
                            s.add(new_pid)
                    
                    s.commit()
                    self.update_deliveries_list()
                    self.show_delivery_details()
                    QMessageBox.information(self, "Успех", "Поставка обновлена")
            except Exception as e:
                s.rollback()
                QMessageBox.critical(self, "Ошибка", f"Не удалось обновить поставку: {str(e)}")
    
    def delete_delivery(self):
        if not self.deliveries_list.currentItem():
            QMessageBox.warning(self, "Предупреждение", "Выберите поставку для удаления")
            return
        
        reply = QMessageBox.question(self, "Подтверждение", "Вы уверены, что хотите удалить эту поставку?",
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            with Session() as s:
                try:
                    delivery_id = self.deliveries_list.currentItem().data(Qt.UserRole)
                    delivery = s.query(Delivery).filter(Delivery.id == delivery_id).first()
                    if delivery:
                        s.delete(delivery)
                        s.commit()
                        self.update_deliveries_list()
                        self.stack.setCurrentIndex(0)
                        QMessageBox.information(self, "Успех", "Поставка удалена")
                    else:
                        QMessageBox.warning(self, "Ошибка", "Поставка не найдена")
                except Exception as e:
                    s.rollback()
                    QMessageBox.critical(self, "Ошибка", f"Не удалось удалить поставку: {str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())