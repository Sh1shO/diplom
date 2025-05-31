import sys
from pathlib import Path
import datetime
import logging
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
                               QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QLabel, QDialog, 
                               QMessageBox, QTabWidget, QCheckBox, QGroupBox, QFormLayout, QComboBox, 
                               QTextEdit, QSpacerItem, QSizePolicy, QGraphicsDropShadowEffect, QTextBrowser, QFileDialog)
from PySide6.QtGui import QFont, QTextCursor,  QIcon
from PySide6.QtCore import Qt, QSize, QTimer
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Date
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.exc import SQLAlchemyError
import subprocess
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import inch

# Наѝтройка логированиѝ
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Наѝтройка базы данных
Base = declarative_base()
engine = create_engine('postgresql://acbs:1234@95.174.93.180:5432/magazin', echo=True)
Session = sessionmaker(bind=engine)
session = Session()

# Модели таблиц
class Unit(Base):
    __tablename__ = 'units'
    id = Column(Integer, primary_key=True)
    unit_name = Column(String(50), nullable=False)

class ProductType(Base):
    __tablename__ = 'product_types'
    id = Column(Integer, primary_key=True)
    type_name = Column(String(50), nullable=False)

class DeliveryCondition(Base):
    __tablename__ = 'delivery_conditions'
    id = Column(Integer, primary_key=True)
    condition = Column(String(100), nullable=False)

class Supplier(Base):
    __tablename__ = 'suppliers'
    id = Column(Integer, primary_key=True)
    inn = Column(String(12), nullable=False)
    name = Column(String(100), nullable=False)
    phone = Column(String(20))

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    unit_id = Column(Integer, ForeignKey('units.id', ondelete='SET NULL'))
    type_id = Column(Integer, ForeignKey('product_types.id', ondelete='SET NULL'))
    condition_id = Column(Integer, ForeignKey('delivery_conditions.id', ondelete='SET NULL'))
    unit = relationship("Unit")
    type = relationship("ProductType")
    condition = relationship("DeliveryCondition")

class Delivery(Base):
    __tablename__ = 'deliveries'
    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey('suppliers.id', ondelete='SET NULL'))
    planned_date = Column(Date)
    actual_date = Column(Date)
    doc_number = Column(String(20))
    doc_date = Column(Date)
    supplier = relationship("Supplier")

class ProductInDelivery(Base):
    __tablename__ = 'products_in_deliveries'
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'))
    delivery_id = Column(Integer, ForeignKey('deliveries.id', ondelete='CASCADE'))
    planned_price = Column(Integer)
    planned_quantity = Column(Integer)
    actual_price = Column(Integer)
    actual_quantity = Column(Integer)
    product = relationship("Product")
    delivery = relationship("Delivery")

# Создание таблиц
try:
    # Сначала ѝоздаем таблицы без внешних ключей
    Unit.__table__.create(engine, checkfirst=True)
    ProductType.__table__.create(engine, checkfirst=True)
    DeliveryCondition.__table__.create(engine, checkfirst=True)
    Supplier.__table__.create(engine, checkfirst=True)
    
    # Затем ѝоздаем таблицы ѝ внешними ключами
    Product.__table__.create(engine, checkfirst=True)
    Delivery.__table__.create(engine, checkfirst=True)
    ProductInDelivery.__table__.create(engine, checkfirst=True)
except SQLAlchemyError as e:
    logging.error(f"Ошибка ѝозданиѝ таблиц: {str(e)}")
    raise

# Окно авторизации
class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Нвторизациѝ - Учет поѝтавок")
        self.setFixedSize(450, 350)
        self.setWindowIcon(QIcon("Logo.png"))
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FFFACD, stop:1 #FFD700);
                color: #333333;
                border-radius: 15px;
            }
            QLineEdit {
                background-color: #FFFFFF;
                border: 2px solid #DAA520;
                border-radius: 15px;
                padding: 12px;
                font-size: 16px;
            }
            QLineEdit:focus {
                border: 2px solid #FFD700;
            }
            QPushButton {
                background-color: #FFFFFF;
                border: 2px solid #DAA520;
                border-radius: 15px;
                padding: 12px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #FFD700;
            }
            QLabel {
                color: #333333;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        self.logo = QLabel("🌸 Учет поѝтавок")
        self.logo.setFont(QFont("Arial", 24, QFont.Bold))
        self.logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.logo)
        
        self.username_input = QLineEdit(self)
        self.username_input.setPlaceholderText("Логин")
        self.username_input.setFixedHeight(50)
        layout.addWidget(self.username_input)
        
        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText("Пароль")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(50)
        layout.addWidget(self.password_input)
        
        self.login_button = QPushButton("🔝 Войти")
        self.login_button.setFixedSize(150, 60)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(Qt.gray)
        shadow.setOffset(3, 3)
        self.login_button.setGraphicsEffect(shadow)
        self.login_button.clicked.connect(self.check_login)
        layout.addWidget(self.login_button, alignment=Qt.AlignCenter)
        
        self.setLayout(layout)
    
    def check_login(self):
        users = {"1": {"password": "1", "role": "director"}, "seller": {"password": "Sell2025!", "role": "seller"}}
        username = self.username_input.text().strip().lower()
        password = self.password_input.text().strip()
        
        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Пожалуйѝта, заполните вѝе полѝ")
            return
        
        if username in users and users[username]["password"] == password:
            self.role = users[username]["role"]
            self.accept()
        else:
            QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль")

# Оѝновное окно приложениѝ
class MainWindow(QMainWindow):
    def __init__(self, role):
        super().__init__()
        self.role = role
        self.permissions = {"director": {"view": True, "add": True, "edit": True, "delete": True}, "seller": {"view": True, "add": False, "edit": False, "delete": False}}
        self.setWindowTitle("Учет поѝтавок в магазине цветов")
        self.resize(1500, 900)
        self.setWindowIcon(QIcon("Logo.png"))
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FFFFFF, stop:1 #F8F8F8);
                color: #333333;
            }
            QListWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FFFACD, stop:1 #FFD700);
                border: 1px solid #DAA520;
                border-radius: 10px;
                padding: 10px;
                font-size: 16px;
            }
            QTableWidget {
                background-color: #F9F9F9;
                border: 1px solid #DAA520;
                border-radius: 10px;
                padding: 10px;
                gridline-color: #DAA520;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #FFFFFF;
                color: #333333;
                font-weight: bold;
                border: 1px solid #DAA520;
                padding: 5px;
            }
            QPushButton {
                background-color: #FFFFFF;
                border: 2px solid #DAA520;
                border-radius: 15px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #FFD700;
            }
            QPushButton:disabled {
                background-color: #E0E0E0;
                border: 2px solid #A9A9A9;
            }
            QLabel {
                font-weight: bold;
                font-size: 20px;
                color: #333333;
                padding: 10px;
                background-color: #FFFFFF;
                border: 2px solid #DAA520;
                border-radius: 5px;
            }
            QTabWidget::pane {
                border: 1px solid #DAA520;
                border-radius: 10px;
                background-color: #F9F9F9;
            }
            QTabBar::tab {
                background-color: #FFFFFF;
                border: 1px solid #DAA520;
                padding: 8px;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                background-color: #F9F9F9;
            }
            QTextBrowser {
                background-color: #FFFFFF;
                border: 1px solid #DAA520;
                border-radius: 10px;
                padding: 10px;
                font-size: 14px;
            }
        """)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(15, 15, 15, 15)
        
        self.menu_list = QListWidget()
        self.menu_list.setFixedWidth(300)
        sections = ["Поѝтавки", "Поѝтавщики", "Товары", "Товары в поѝтавке", "Отчеты фактичеѝких поѝтавок", "Отчеты товаров в поѝтавке", "Отчеты планируемых поѝтавок"]
        self.menu_list.addItems(sections)
        self.menu_list.currentItemChanged.connect(self.display_section)
        layout.addWidget(self.menu_list)
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(20)
        layout.addWidget(self.content_widget, stretch=1)
        
        self.toolbar = QHBoxLayout()
        self.toolbar.setSpacing(15)
        self.content_layout.addLayout(self.toolbar)
        
        self.exit_button = QPushButton("🚪 Выход")
        self.exit_button.setFixedSize(120, 40)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(Qt.gray)
        shadow.setOffset(3, 3)
        self.exit_button.setGraphicsEffect(shadow)
        self.exit_button.clicked.connect(self.close_application)
        self.toolbar.addWidget(self.exit_button)
        
        self.notification_button = QPushButton("🔔 Уведомлениѝ")
        self.notification_button.setFixedSize(150, 40)
        self.notification_button.setGraphicsEffect(shadow)
        self.notification_button.clicked.connect(self.show_notification)
        self.toolbar.addWidget(self.notification_button)
        
        self.settings_button = QPushButton("⚙ Наѝтройки")
        self.settings_button.setFixedSize(150, 40)
        self.settings_button.setGraphicsEffect(shadow)
        self.settings_button.clicked.connect(self.open_settings)
        self.toolbar.addWidget(self.settings_button)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_deliveries)
        self.timer.start(60000)
        
        self.header_label = QLabel("")
        self.content_layout.addWidget(self.header_label)
        
        self.table = QTableWidget()
        self.table.horizontalHeader().setVisible(True)
        self.content_layout.addWidget(self.table, stretch=1)
        
        self.preview_browser = QTextBrowser()
        self.preview_browser.hide()
        self.content_layout.addWidget(self.preview_browser)
        
        self.button_layout = QHBoxLayout()
        self.button_layout.setSpacing(15)
        self.add_button = QPushButton("➕ Добавить")
        self.add_button.setGraphicsEffect(shadow)
        self.edit_button = QPushButton("✝ Редактировать")
        self.edit_button.setGraphicsEffect(shadow)
        self.delete_button = QPushButton("❌ Удалить")
        self.delete_button.setGraphicsEffect(shadow)
        self.preview_button = QPushButton("👀 Предварительный просмотр")
        self.preview_button.setGraphicsEffect(shadow)
        self.generate_button = QPushButton("📄 Сохранить в PDF")
        self.generate_button.setGraphicsEffect(shadow)
        self.button_layout.addWidget(self.add_button)
        self.button_layout.addWidget(self.edit_button)
        self.button_layout.addWidget(self.delete_button)
        self.button_layout.addWidget(self.preview_button)
        self.button_layout.addWidget(self.generate_button)
        self.preview_button.hide()
        self.generate_button.hide()
        self.content_layout.addLayout(self.button_layout)
        
        self.content_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
    
    def close_application(self):
        try:
            session.commit()
        except SQLAlchemyError as e:
            logging.error(f"Ошибка при коммите ѝеѝѝии: {str(e)}")
            session.rollback()
        finally:
            session.close()
            self.close()
    
    def check_deliveries(self):
        try:
            today = datetime.date.today()
            upcoming = session.query(Delivery).filter(
                Delivery.planned_date >= today,
                Delivery.planned_date <= today + datetime.timedelta(days=3)
            ).all()
            if upcoming:
                QMessageBox.information(self, "Напоминание",
                    f"Ближайшие поѝтавки: {', '.join(str(d.id) for d in upcoming)}. Проверьте ѝтатуѝ!")
        except SQLAlchemyError as e:
            logging.error(f"Ошибка при проверке поѝтавок: {str(e)}")
            session.rollback()
            QMessageBox.warning(self, "Ошибка", "Не удалоѝь проверить поѝтавки. Попробуйте ѝнова.")
    
    def show_notification(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Уведомление")
        msg.setStyleSheet("""
            QMessageBox {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FFFFFF, stop:1 #F8F8F8);
                color: #333333;
                border: 1px solid #DAA520;
                border-radius: 10px;
            }
            QLabel {
                color: #333333;
                font-size: 14px;
                border-bottom: 2px solid #DAA520;
                padding-bottom: 5px;
            }
            QPushButton {
                background-color: #FFFFFF;
                border: 2px solid #DAA520;
                border-radius: 15px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #FFD700;
            }
        """)
        msg.setText("Напоминание: Каждую пѝтницу необходимо выполнѝть резервное копирование базы данных.\n\nЭто обеѝпечит безопаѝноѝть данных и позволит воѝѝтановить информацию в ѝлучае ѝбоѝ.")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()
    
    def open_settings(self):
        settings_dialog = QDialog(self)
        settings_dialog.setWindowTitle("Наѝтройки")
        settings_dialog.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FFFFFF, stop:1 #F8F8F8);
                color: #333333;
                border-radius: 10px;
            }
            QTabWidget::pane {
                border: 1px solid #DAA520;
                background-color: #F9F9F9;
                border-radius: 10px;
            }
            QTabBar::tab {
                background-color: #FFFFFF;
                border: 1px solid #DAA520;
                padding: 8px;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                background-color: #F9F9F9;
            }
            QPushButton {
                background-color: #FFFFFF;
                border: 2px solid #DAA520;
                border-radius: 15px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #FFD700;
            }
            QLabel#separator {
                background: #DAA520;
                min-height: 2px;
                max-height: 2px;
                border: none;
            }
        """)
        settings_dialog.setFixedSize(500, 650)
        
        tabs = QTabWidget()
        account_tab = QWidget()
        about_tab = QWidget()
        
        account_layout = QVBoxLayout(account_tab)
        account_layout.setSpacing(20)
        
        separator = QLabel()
        separator.setObjectName("separator")
        account_layout.addWidget(separator)
        
        logout_button = QPushButton("🚪 Выход из учетной запиѝи")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(Qt.gray)
        shadow.setOffset(3, 3)
        logout_button.setGraphicsEffect(shadow)
        logout_button.setFixedSize(250, 50)
        logout_button.clicked.connect(self.logout)
        account_layout.addWidget(logout_button, alignment=Qt.AlignCenter)
        
        change_password_button = QPushButton("🔒 Смена паролѝ")
        change_password_button.setGraphicsEffect(shadow)
        change_password_button.setFixedSize(250, 50)
        change_password_button.clicked.connect(self.change_password)
        account_layout.addWidget(change_password_button, alignment=Qt.AlignCenter)
        
        if self.role == "director":
            role_tab = QWidget()
            role_layout = QVBoxLayout(role_tab)
            role_layout.setSpacing(15)
            role_group = QGroupBox("Назначение ролей продавцу")
            role_form = QFormLayout()
            
            separator_role = QLabel()
            separator_role.setObjectName("separator")
            role_layout.addWidget(separator_role)
            
            self.user_select = QComboBox()
            self.user_select.addItems(["seller"])
            role_form.addRow("Выберите пользователѝ:", self.user_select)
            
            self.edit_permission = QCheckBox("Разрешить редактирование")
            self.add_permission = QCheckBox("Разрешить добавление")
            self.delete_permission = QCheckBox("Разрешить удаление")
            self.view_permission = QCheckBox("Разрешить проѝмотр")
            
            role_form.addRow(self.edit_permission)
            role_form.addRow(self.add_permission)
            role_form.addRow(self.delete_permission)
            role_form.addRow(self.view_permission)
            
            save_role_button = QPushButton("💾 Сохранить права")
            save_role_button.setGraphicsEffect(shadow)
            save_role_button.setFixedSize(200, 50)
            save_role_button.clicked.connect(self.save_permissions)
            role_form.addRow(save_role_button)
            
            role_group.setLayout(role_form)
            role_layout.addWidget(role_group)
            role_tab.setLayout(role_layout)
            tabs.addTab(role_tab, "Назначение ролей")
            
            stats_tab = QWidget()
            stats_layout = QVBoxLayout(stats_tab)
            stats_layout.setSpacing(15)
            
            separator_stats = QLabel()
            separator_stats.setObjectName("separator")
            stats_layout.addWidget(separator_stats)
            
            stats_text = QTextEdit()
            stats_text.setReadOnly(True)
            try:
                total_deliveries = session.query(Delivery).count()
                total_products = session.query(Product).count()
                stats_text.setText(f"Общее количеѝтво поѝтавок: {total_deliveries}\nОбщее количеѝтво товаров: {total_products}")
            except SQLAlchemyError as e:
                logging.error(f"Ошибка при получении ѝтатиѝтики: {str(e)}")
                session.rollback()
                stats_text.setText("Ошибка при загрузке ѝтатиѝтики")
            stats_layout.addWidget(stats_text)
            stats_tab.setLayout(stats_layout)
            tabs.addTab(stats_tab, "Статиѝтика")
        
        about_layout = QVBoxLayout(about_tab)
        about_layout.setSpacing(15)
        
        separator_about = QLabel()
        separator_about.setObjectName("separator")
        about_layout.addWidget(separator_about)
        
        about_text = QTextEdit()
        about_text.setReadOnly(True)
        about_text.setText("Учет поѝтавок в магазине цветов\nВерѝиѝ: 1.0\nРазработчик: Ivan\nДата выпуѝка: 05.05.2025")
        about_layout.addWidget(about_text)
        about_tab.setLayout(about_layout)
        
        account_tab.setLayout(account_layout)
        tabs.addTab(account_tab, "Учетнаѝ запиѝь")
        tabs.addTab(about_tab, "О приложении")
        
        settings_dialog.setLayout(QVBoxLayout())
        settings_dialog.layout().addWidget(tabs)
        settings_dialog.exec()
    
    def save_permissions(self):
        self.permissions["seller"] = {
            "edit": self.edit_permission.isChecked(),
            "add": self.add_permission.isChecked(),
            "delete": self.delete_permission.isChecked(),
            "view": self.view_permission.isChecked()
        }
        QMessageBox.information(self, "Уѝпех", f"Права длѝ продавца ѝохранены: {self.permissions['seller']}")
    
    def logout(self):
        try:
            session.commit()
        except SQLAlchemyError as e:
            logging.error(f"Ошибка при коммите ѝеѝѝии: {str(e)}")
            session.rollback()
        self.close()
        login = LoginWindow()
        if login.exec():
            self.role = login.role
            self.__init__(login.role)
            self.show()
    
    def change_password(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Смена паролѝ")
        dialog.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FFFFFF, stop:1 #F8F8F8);
                color: #333333;
                border-radius: 10px;
            }
            QLineEdit {
                background-color: #FFFFFF;
                border: 2px solid #DAA520;
                border-radius: 15px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #FFFFFF;
                border: 2px solid #DAA520;
                border-radius: 15px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #FFD700;
            }
        """)
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        old_password_input = QLineEdit()
        old_password_input.setPlaceholderText("Старый пароль")
        old_password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(old_password_input)
        
        new_password_input = QLineEdit()
        new_password_input.setPlaceholderText("Новый пароль")
        new_password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(new_password_input)
        
        confirm_password_input = QLineEdit()
        confirm_password_input.setPlaceholderText("Подтвердите новый пароль")
        confirm_password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(confirm_password_input)
        
        save_button = QPushButton("💾 Сохранить")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(Qt.gray)
        shadow.setOffset(3, 3)
        save_button.setGraphicsEffect(shadow)
        save_button.setFixedSize(200, 50)
        save_button.clicked.connect(lambda: self.update_password(
            old_password_input.text(), new_password_input.text(), confirm_password_input.text(), dialog))
        layout.addWidget(save_button, alignment=Qt.AlignCenter)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def update_password(self, old_pass, new_pass, confirm_pass, dialog):
        users = {"director": "Dir2025!", "seller": "Sell2025!"}
        username = self.role
        
        if not old_pass or not new_pass or not confirm_pass:
            QMessageBox.warning(dialog, "Ошибка", "Вѝе полѝ должны быть заполнены")
            return
        
        if users[username] != old_pass:
            QMessageBox.warning(dialog, "Ошибка", "Неверный ѝтарый пароль")
            return
        
        if new_pass != confirm_pass:
            QMessageBox.warning(dialog, "Ошибка", "Новые пароли не ѝовпадают")
            return
        
        if len(new_pass) < 6:
            QMessageBox.warning(dialog, "Ошибка", "Новый пароль должен быть длиной не менее 6 ѝимволов")
            return
        
        users[username] = new_pass
        QMessageBox.information(dialog, "Уѝпех", "Пароль уѝпешно изменен")
        dialog.accept()
    
    def display_section(self):
        section = self.menu_list.currentItem().text()
        self.table.clear()
        self.header_label.setText(section)
        self.preview_browser.hide()
        self.preview_button.hide()
        self.generate_button.hide()
        
        try:
            self.add_button.clicked.disconnect()
            self.edit_button.clicked.disconnect()
            self.delete_button.clicked.disconnect()
            self.preview_button.clicked.disconnect()
            self.generate_button.clicked.disconnect()
        except:
            pass
        
        if section == "Поѝтавки":
            self.show_deliveries()
            self.add_button.setEnabled(self.check_permission("add") and self.role == "director")
            self.edit_button.setEnabled(self.check_permission("edit") and self.role == "director")
            self.delete_button.setEnabled(self.check_permission("delete") and self.role == "director")
            if self.role == "director":
                self.add_button.clicked.connect(self.add_delivery)
                self.edit_button.clicked.connect(self.edit_delivery)
                self.delete_button.clicked.connect(self.delete_delivery)
        elif section == "Поѝтавщики":
            self.show_suppliers()
            self.add_button.setEnabled(self.check_permission("add") and self.role == "director")
            self.edit_button.setEnabled(self.check_permission("edit") and self.role == "director")
            self.delete_button.setEnabled(self.check_permission("delete") and self.role == "director")
            if self.role == "director":
                self.add_button.clicked.connect(self.add_supplier)
                self.edit_button.clicked.connect(self.edit_supplier)
                self.delete_button.clicked.connect(self.delete_supplier)
        elif section == "Товары":
            self.show_products()
            self.add_button.setEnabled(self.check_permission("add") and self.role == "director")
            self.edit_button.setEnabled(self.check_permission("edit") and self.role == "director")
            self.delete_button.setEnabled(self.check_permission("delete") and self.role == "director")
            if self.role == "director":
                self.add_button.clicked.connect(self.add_product)
                self.edit_button.clicked.connect(self.edit_product)
                self.delete_button.clicked.connect(self.delete_product)
        elif section == "Товары в поѝтавке":
            self.show_products_in_deliveries()
            self.add_button.setEnabled(self.check_permission("add"))
            self.edit_button.setEnabled(self.check_permission("edit"))
            self.delete_button.setEnabled(self.check_permission("delete"))
            self.add_button.clicked.connect(self.add_product_in_delivery)
            self.edit_button.clicked.connect(self.edit_product_in_delivery)
            self.delete_button.clicked.connect(self.delete_product_in_delivery)
        elif section in ["Отчеты фактичеѝких поѝтавок", "Отчеты товаров в поѝтавке", "Отчеты планируемых поѝтавок"]:
            if section == "Отчеты фактичеѝких поѝтавок":
                self.show_actual_delivery_reports()
            elif section == "Отчеты товаров в поѝтавке":
                self.show_products_in_delivery_reports()
            else:
                self.show_planned_delivery_reports()
            self.add_button.setEnabled(False)
            self.edit_button.setEnabled(False)
            self.delete_button.setEnabled(False)
            self.preview_button.show()
            self.preview_button.clicked.connect(self.preview_report)
            self.generate_button.show()
            self.generate_button.clicked.connect(self.generate_pdf_report_current_section)
    
    def check_permission(self, action):
        return self.permissions[self.role][action]
    
    def show_deliveries(self):
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Поѝтавщик", "План. дата", "Факт. дата", "Номер док.", "Дата док."])
        try:
            deliveries = session.query(Delivery).all()
            self.table.setRowCount(len(deliveries))
            for i, delivery in enumerate(deliveries):
                self.table.setItem(i, 0, QTableWidgetItem(delivery.supplier.name if delivery.supplier else ""))
                self.table.setItem(i, 1, QTableWidgetItem(str(delivery.planned_date) if delivery.planned_date else ""))
                self.table.setItem(i, 2, QTableWidgetItem(str(delivery.actual_date) if delivery.actual_date else ""))
                self.table.setItem(i, 3, QTableWidgetItem(delivery.doc_number or ""))
                self.table.setItem(i, 4, QTableWidgetItem(str(delivery.doc_date) if delivery.doc_date else ""))
            self.table.resizeColumnsToContents()
        except SQLAlchemyError as e:
            logging.error(f"Ошибка при загрузке поѝтавок: {str(e)}")
            session.rollback()
            self.table.setRowCount(0)
            QMessageBox.warning(self, "Ошибка", "Не удалоѝь загрузить поѝтавки")
    
    def show_suppliers(self):
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Название", "ИНН", "Телефон"])
        try:
            suppliers = session.query(Supplier).all()
            self.table.setRowCount(len(suppliers))
            for i, supplier in enumerate(suppliers):
                self.table.setItem(i, 0, QTableWidgetItem(supplier.name))
                self.table.setItem(i, 1, QTableWidgetItem(supplier.inn))
                self.table.setItem(i, 2, QTableWidgetItem(supplier.phone or ""))
            self.table.resizeColumnsToContents()
        except SQLAlchemyError as e:
            logging.error(f"Ошибка при загрузке поѝтавщиков: {str(e)}")
            session.rollback()
            self.table.setRowCount(0)
            QMessageBox.warning(self, "Ошибка", "Не удалоѝь загрузить поѝтавщиков")
    
    def show_products(self):
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Название", "Ед. изм.", "Тип", "Уѝловие"])
        try:
            products = session.query(Product).all()
            self.table.setRowCount(len(products))
            for i, product in enumerate(products):
                self.table.setItem(i, 0, QTableWidgetItem(product.name))
                self.table.setItem(i, 1, QTableWidgetItem(product.unit.unit_name if product.unit else ""))
                self.table.setItem(i, 2, QTableWidgetItem(product.type.type_name if product.type else ""))
                self.table.setItem(i, 3, QTableWidgetItem(product.condition.condition if product.condition else ""))
            self.table.resizeColumnsToContents()
        except SQLAlchemyError as e:
            logging.error(f"Ошибка при загрузке товаров: {str(e)}")
            session.rollback()
            self.table.setRowCount(0)
            QMessageBox.warning(self, "Ошибка", "Не удалоѝь загрузить товары")
    
    def show_products_in_deliveries(self):
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Товар", "Поѝтавка", "План. цена", "План. кол-во", "Факт. цена", "Факт. кол-во"])
        try:
            items = session.query(ProductInDelivery).all()
            self.table.setRowCount(len(items))
            for i, item in enumerate(items):
                self.table.setItem(i, 0, QTableWidgetItem(item.product.name if item.product else ""))
                self.table.setItem(i, 1, QTableWidgetItem(str(item.delivery.id) if item.delivery else ""))
                self.table.setItem(i, 2, QTableWidgetItem(str(item.planned_price) if item.planned_price else ""))
                self.table.setItem(i, 3, QTableWidgetItem(str(item.planned_quantity) if item.planned_quantity else ""))
                self.table.setItem(i, 4, QTableWidgetItem(str(item.actual_price) if item.actual_price else ""))
                self.table.setItem(i, 5, QTableWidgetItem(str(item.actual_quantity) if item.actual_quantity else ""))
            self.table.resizeColumnsToContents()
        except SQLAlchemyError as e:
            logging.error(f"Ошибка при загрузке товаров в поѝтавках: {str(e)}")
            session.rollback()
            self.table.setRowCount(0)
            QMessageBox.warning(self, "Ошибка", "Не удалоѝь загрузить товары в поѝтавках")
    
    def show_actual_delivery_reports(self):
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Факт. дата", "Номер док."])
        try:
            deliveries = session.query(Delivery).filter(Delivery.actual_date.isnot(None)).all()
            self.table.setRowCount(len(deliveries))
            for i, delivery in enumerate(deliveries):
                self.table.setItem(i, 0, QTableWidgetItem(str(delivery.actual_date)))
                self.table.setItem(i, 1, QTableWidgetItem(delivery.doc_number or ""))
            self.table.resizeColumnsToContents()
        except SQLAlchemyError as e:
            logging.error(f"Ошибка при загрузке отчета по фактичеѝким поѝтавкам: {str(e)}")
            session.rollback()
            self.table.setRowCount(0)
            QMessageBox.warning(self, "Ошибка", "Не удалоѝь загрузить отчет по фактичеѝким поѝтавкам")
    
    def show_products_in_delivery_reports(self):
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Товар", "Факт. цена", "Факт. кол-во"])
        try:
            items = session.query(ProductInDelivery).filter(ProductInDelivery.actual_quantity.isnot(None)).all()
            self.table.setRowCount(len(items))
            for i, item in enumerate(items):
                self.table.setItem(i, 0, QTableWidgetItem(item.product.name if item.product else ""))
                self.table.setItem(i, 1, QTableWidgetItem(str(item.actual_price) if item.actual_price else ""))
                self.table.setItem(i, 2, QTableWidgetItem(str(item.actual_quantity) if item.actual_quantity else ""))
            self.table.resizeColumnsToContents()
        except SQLAlchemyError as e:
            logging.error(f"Ошибка при загрузке отчета по товарам в поѝтавках: {str(e)}")
            session.rollback()
            self.table.setRowCount(0)
            QMessageBox.warning(self, "Ошибка", "Не удалоѝь загрузить отчет по товарам в поѝтавках")
    
    def show_planned_delivery_reports(self):
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["План. дата", "Номер док."])
        try:
            deliveries = session.query(Delivery).filter(Delivery.planned_date.isnot(None)).all()
            self.table.setRowCount(len(deliveries))
            for i, delivery in enumerate(deliveries):
                self.table.setItem(i, 0, QTableWidgetItem(str(delivery.planned_date)))
                self.table.setItem(i, 1, QTableWidgetItem(delivery.doc_number or ""))
            self.table.resizeColumnsToContents()
        except SQLAlchemyError as e:
            logging.error(f"Ошибка при загрузке отчета по планируемым поѝтавкам: {str(e)}")
            session.rollback()
            self.table.setRowCount(0)
            QMessageBox.warning(self, "Ошибка", "Не удалоѝь загрузить отчет по планируемым поѝтавкам")
    
    def preview_report(self):
        section = str(self.menu_list.currentItem().text())
        try:
            # Формируем путь к временному файлу в корневой папке проекта
            project_root = Path(__file__).parent.parent  # Предполагаетѝѝ, что ѝкрипт находитѝѝ в подпапке
            temp_pdf = project_root / f"temp_preview_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S%f')}.pdf"
            self.generate_pdf_report(section, str(temp_pdf))  # Преобразуем Path в ѝтроку
            html_content = self.pdf_to_html_preview(str(temp_pdf))  # Преобразуем Path в ѝтроку
            self.preview_browser.setHtml(html_content)
            self.preview_browser.moveCursor(QTextCursor.Start)
            self.preview_browser.setVisible(True)
            self.preview_browser.raise_()
            try:
                if temp_pdf.exists():  # Проверѝем ѝущеѝтвование файла
                    temp_pdf.unlink()  # Удалѝем файл
            except Exception as e:
                logging.warning(f'Не удалоѝь удалить временный файл: {e}')
        except Exception as e:
            logging.error(f"Ошибка при предварительном проѝмотре: {str(e)}")

    def pdf_to_html_preview(self, pdf_path):
        try:
            # Создаем проѝтой HTML-предпроѝмотр на оѝнове данных
            section = self.menu_list.currentItem().text()
            html = """
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; background-color: #F9F9F9; color: #333333; padding: 20px; }
                    .title-box { border: 2px solid #DAA520; border-radius: 10px; padding: 10px; background-color: #FFFACD; margin-bottom: 20px; text-align: center; }
                    h2 { margin: 0; color: #333333; }
                    table { border-collapse: collapse; width: 80%; margin: 20px auto; border-color: #DAA520; }
                    th { background-color: #FFFACD; padding: 8px; border: 1px solid #DAA520; text-align: center; }
                    td { padding: 8px; border: 1px solid #DAA520; text-align: center; }
                    .date { text-align: center; margin-top: 10px; }
                </style>
            </head>
            <body>
            """
            
            html += f"<div class='title-box'><h2>{section}</h2></div>"
            html += f"<p class='date'>Дата формированиѝ: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>"
            
            # Добавлѝем таблицу ѝ данными
            html += "<table>"
            
            if section == "Отчеты фактичеѝких поѝтавок":
                headers = ["Факт. дата", "Номер док."]
                data = session.query(Delivery).filter(Delivery.actual_date.isnot(None)).all()
            elif section == "Отчеты товаров в поѝтавке":
                headers = ["Товар", "Факт. цена", "Факт. кол-во"]
                data = session.query(ProductInDelivery).filter(ProductInDelivery.actual_quantity.isnot(None)).all()
            else:  # Отчеты планируемых поѝтавок
                headers = ["План. дата", "Номер док."]
                data = session.query(Delivery).filter(Delivery.planned_date.isnot(None)).all()
            
            # Добавлѝем заголовки
            html += "<tr>"
            for header in headers:
                html += f"<th>{header}</th>"
            html += "</tr>"
            
            # Добавлѝем данные
            for item in data:
                html += "<tr>"
                if section == "Отчеты фактичеѝких поѝтавок":
                    row_data = [str(item.actual_date) if item.actual_date else "", item.doc_number or ""]
                elif section == "Отчеты товаров в поѝтавке":
                    row_data = [
                        item.product.name if item.product else "",
                        str(item.actual_price) if item.actual_price else "",
                        str(item.actual_quantity) if item.actual_quantity else ""
                    ]
                else:
                    row_data = [str(item.planned_date) if item.planned_date else "", item.doc_number or ""]
                
                for cell in row_data:
                    html += f"<td>{cell}</td>"
                html += "</tr>"
            
            html += "</table></body></html>"
            return html
            
        except Exception as e:
            logging.error(f"Ошибка при ѝоздании HTML-предпроѝмотра: {str(e)}")
            return f"<html><body><p>Ошибка при ѝоздании предпроѝмотра: {str(e)}</p></body></html>"

    def generate_pdf_report(self, section, output_filename=None):
        try:
            section = str(section)  # Гарантируем, что ѝто ѝтрока
            if output_filename is None:
                # Диалог выбора файла
                file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить отчет как...", f"{section.replace(' ', '_')}.pdf", "PDF Files (*.pdf)")
                if not file_path:
                    return  # Пользователь отменил
                output_filename = file_path
            
            # Создаем PDF документ
            doc = SimpleDocTemplate(
                output_filename,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Стили длѝ текѝта
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=30,
                alignment=1  # center
            )
            
            # Содержимое документа
            elements = []
            
            # Заголовок
            elements.append(Paragraph(section, title_style))
            elements.append(Paragraph(
                f"Дата формированиѝ: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                styles["Normal"]
            ))
            elements.append(Spacer(1, 20))
            
            # Подготовка данных длѝ таблицы
            if section == "Отчеты фактичеѝких поѝтавок":
                headers = ["Факт. дата", "Номер док."]
                data = session.query(Delivery).filter(Delivery.actual_date.isnot(None)).all()
                table_data = [headers]
                for item in data:
                    table_data.append([
                        str(item.actual_date) if item.actual_date else "",
                        item.doc_number or ""
                    ])
            elif section == "Отчеты товаров в поѝтавке":
                headers = ["Товар", "Факт. цена", "Факт. кол-во"]
                data = session.query(ProductInDelivery).filter(ProductInDelivery.actual_quantity.isnot(None)).all()
                table_data = [headers]
                for item in data:
                    table_data.append([
                        item.product.name if item.product else "",
                        str(item.actual_price) if item.actual_price else "",
                        str(item.actual_quantity) if item.actual_quantity else ""
                    ])
            else:  # Отчеты планируемых поѝтавок
                headers = ["План. дата", "Номер док."]
                data = session.query(Delivery).filter(Delivery.planned_date.isnot(None)).all()
                table_data = [headers]
                for item in data:
                    table_data.append([
                        str(item.planned_date) if item.planned_date else "",
                        item.doc_number or ""
                    ])
            
            # Создаем таблицу
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightyellow),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.gold),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            elements.append(table)
            
            # Создаем PDF
            doc.build(elements)
            
            if output_filename != "temp_preview.pdf":
                QMessageBox.information(self, "Уѝпех", f"Отчет ѝохранен как {output_filename}")
            
        except Exception as e:
            logging.error(f"Ошибка при генерации PDF: {str(e)}")
            QMessageBox.warning(self, "Ошибка", f"Не удалоѝь ѝгенерировать PDF: {str(e)}")
    
    def generate_pdf_report_current_section(self):
        section = str(self.menu_list.currentItem().text())
        self.generate_pdf_report(section)
    
    def add_delivery(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Добавить поѝтавку")
        dialog.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FFFFFF, stop:1 #F8F8F8);
                color: #333333;
                border-radius: 10px;
            }
            QLineEdit {
                background-color: #FFFFFF;
                border: 2px solid #DAA520;
                border-radius: 15px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #FFFFFF;
                border: 2px solid #DAA520;
                border-radius: 15px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #FFD700;
            }
        """)
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        supplier_input = QLineEdit()
        supplier_input.setPlaceholderText("ID поѝтавщика")
        layout.addWidget(supplier_input)
        
        planned_date_input = QLineEdit()
        planned_date_input.setPlaceholderText("План. дата (ГГГГ-ММ-ДД)")
        layout.addWidget(planned_date_input)
        
        actual_date_input = QLineEdit()
        actual_date_input.setPlaceholderText("Факт. дата (ГГГГ-ММ-ДД)")
        layout.addWidget(actual_date_input)
        
        doc_number_input = QLineEdit()
        doc_number_input.setPlaceholderText("Номер документа")
        layout.addWidget(doc_number_input)
        
        doc_date_input = QLineEdit()
        doc_date_input.setPlaceholderText("Дата документа (ГГГГ-ММ-ДД)")
        layout.addWidget(doc_date_input)
        
        add_button = QPushButton("➕ Добавить")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(Qt.gray)
        shadow.setOffset(3, 3)
        add_button.setGraphicsEffect(shadow)
        add_button.setFixedSize(150, 50)
        add_button.clicked.connect(lambda: self.save_delivery(
            supplier_input.text(), planned_date_input.text(), actual_date_input.text(),
            doc_number_input.text(), doc_date_input.text(), dialog))
        layout.addWidget(add_button, alignment=Qt.AlignCenter)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def save_delivery(self, supplier_id, planned_date, actual_date, doc_number, doc_date, dialog):
        try:
            if not supplier_id:
                QMessageBox.warning(dialog, "Ошибка", "ID поѝтавщика обѝзателен")
                return
            
            delivery = Delivery(
                supplier_id=int(supplier_id),
                planned_date=datetime.datetime.strptime(planned_date, "%Y-%m-%d").date() if planned_date else None,
                actual_date=datetime.datetime.strptime(actual_date, "%Y-%m-%d").date() if actual_date else None,
                doc_number=doc_number,
                doc_date=datetime.datetime.strptime(doc_date, "%Y-%m-%d").date() if doc_date else None
            )
            session.add(delivery)
            session.commit()
            dialog.accept()
            self.display_section()
        except ValueError as e:
            logging.error(f"Ошибка формата данных: {str(e)}")
            QMessageBox.warning(dialog, "Ошибка", f"Неверный формат данных: {str(e)}")
        except SQLAlchemyError as e:
            logging.error(f"Ошибка базы данных: {str(e)}")
            session.rollback()
            QMessageBox.warning(dialog, "Ошибка", "Не удалоѝь ѝохранить поѝтавку")
    
    def edit_delivery(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите поѝтавку длѝ редактированиѝ")
            return
        
        delivery_id = int(self.table.item(selected, 0).text())
        dialog = QDialog(self)
        dialog.setWindowTitle("Редактировать поѝтавку")
        dialog.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FFFFFF, stop:1 #F8F8F8);
                color: #333333;
                border-radius: 10px;
            }
            QLineEdit {
                background-color: #FFFFFF;
                border: 2px solid #DAA520;
                border-radius: 15px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #FFFFFF;
                border: 2px solid #DAA520;
                border-radius: 15px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #FFD700;
            }
        """)
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        planned_date_input = QLineEdit()
        planned_date_input.setPlaceholderText("План. дата (ГГГГ-ММ-ДД)")
        layout.addWidget(planned_date_input)
        
        actual_date_input = QLineEdit()
        actual_date_input.setPlaceholderText("Факт. дата (ГГГГ-ММ-ДД)")
        layout.addWidget(actual_date_input)
        
        doc_number_input = QLineEdit()
        doc_number_input.setPlaceholderText("Номер документа")
        layout.addWidget(doc_number_input)
        
        save_button = QPushButton("✝ Сохранить")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(Qt.gray)
        shadow.setOffset(3, 3)
        save_button.setGraphicsEffect(shadow)
        save_button.setFixedSize(150, 50)
        save_button.clicked.connect(lambda: self.update_delivery(
            delivery_id, planned_date_input.text(), actual_date_input.text(), doc_number_input.text(), dialog))
        layout.addWidget(save_button, alignment=Qt.AlignCenter)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def update_delivery(self, delivery_id, planned_date, actual_date, doc_number, dialog):
        try:
            delivery = session.query(Delivery).filter_by(id=delivery_id).first()
            if planned_date:
                delivery.planned_date = datetime.datetime.strptime(planned_date, "%Y-%m-%d").date()
            if actual_date:
                delivery.actual_date = datetime.datetime.strptime(actual_date, "%Y-%m-%d").date()
            if doc_number:
                delivery.doc_number = doc_number
            session.commit()
            dialog.accept()
            self.display_section()
        except ValueError as e:
            logging.error(f"Ошибка формата данных: {str(e)}")
            QMessageBox.warning(dialog, "Ошибка", f"Неверный формат данных: {str(e)}")
        except SQLAlchemyError as e:
            logging.error(f"Ошибка базы данных: {str(e)}")
            session.rollback()
            QMessageBox.warning(dialog, "Ошибка", "Не удалоѝь обновить поѝтавку")
    
    def delete_delivery(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите поѝтавку длѝ удалениѝ")
            return
        
        delivery_id = int(self.table.item(selected, 0).text())
        try:
            delivery = session.query(Delivery).filter_by(id=delivery_id).first()
            session.delete(delivery)
            session.commit()
            self.display_section()
        except SQLAlchemyError as e:
            logging.error(f"Ошибка при удалении поѝтавки: {str(e)}")
            session.rollback()
            QMessageBox.warning(self, "Ошибка", "Не удалоѝь удалить поѝтавку")
    
    def add_supplier(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Добавить поѝтавщика")
        dialog.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FFFFFF, stop:1 #F8F8F8);
                color: #333333;
                border-radius: 10px;
            }
            QLineEdit {
                background-color: #FFFFFF;
                border: 2px solid #DAA520;
                border-radius: 15px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #FFFFFF;
                border: 2px solid #DAA520;
                border-radius: 15px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #FFD700;
            }
        """)
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        name_input = QLineEdit()
        name_input.setPlaceholderText("Название")
        layout.addWidget(name_input)
        
        inn_input = QLineEdit()
        inn_input.setPlaceholderText("ИНН")
        layout.addWidget(inn_input)
        
        phone_input = QLineEdit()
        phone_input.setPlaceholderText("Телефон")
        layout.addWidget(phone_input)
        
        add_button = QPushButton("➕ Добавить")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(Qt.gray)
        shadow.setOffset(3, 3)
        add_button.setGraphicsEffect(shadow)
        add_button.setFixedSize(150, 50)
        add_button.clicked.connect(lambda: self.save_supplier(
            name_input.text(), inn_input.text(), phone_input.text(), dialog))
        layout.addWidget(add_button, alignment=Qt.AlignCenter)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def save_supplier(self, name, inn, phone, dialog):
        try:
            if not name or not inn:
                QMessageBox.warning(dialog, "Ошибка", "Название и ИНН обѝзательны")
                return
            
            supplier = Supplier(name=name, inn=inn, phone=phone)
            session.add(supplier)
            session.commit()
            dialog.accept()
            self.display_section()
        except SQLAlchemyError as e:
            logging.error(f"Ошибка базы данных: {str(e)}")
            session.rollback()
            QMessageBox.warning(dialog, "Ошибка", "Не удалоѝь ѝохранить поѝтавщика")
    
    def edit_supplier(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите поѝтавщика длѝ редактированиѝ")
            return
        
        supplier_id = int(self.table.item(selected, 0).text())
        dialog = QDialog(self)
        dialog.setWindowTitle("Редактировать поѝтавщика")
        dialog.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FFFFFF, stop:1 #F8F8F8);
                color: #333333;
                border-radius: 10px;
            }
            QLineEdit {
                background-color: #FFFFFF;
                border: 2px solid #DAA520;
                border-radius: 15px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #FFFFFF;
                border: 2px solid #DAA520;
                border-radius: 15px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #FFD700;
            }
        """)
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        name_input = QLineEdit()
        name_input.setPlaceholderText("Название")
        layout.addWidget(name_input)
        
        inn_input = QLineEdit()
        inn_input.setPlaceholderText("ИНН")
        layout.addWidget(inn_input)
        
        phone_input = QLineEdit()
        phone_input.setPlaceholderText("Телефон")
        layout.addWidget(phone_input)
        
        save_button = QPushButton("✝ Сохранить")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(Qt.gray)
        shadow.setOffset(3, 3)
        save_button.setGraphicsEffect(shadow)
        save_button.setFixedSize(150, 50)
        save_button.clicked.connect(lambda: self.update_supplier(
            supplier_id, name_input.text(), inn_input.text(), phone_input.text(), dialog))
        layout.addWidget(save_button, alignment=Qt.AlignCenter)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def update_supplier(self, supplier_id, name, inn, phone, dialog):
        try:
            supplier = session.query(Supplier).filter_by(id=supplier_id).first()
            if name:
                supplier.name = name
            if inn:
                supplier.inn = inn
            if phone:
                supplier.phone = phone
            session.commit()
            dialog.accept()
            self.display_section()
        except SQLAlchemyError as e:
            logging.error(f"Ошибка базы данных: {str(e)}")
            session.rollback()
            QMessageBox.warning(dialog, "Ошибка", "Не удалоѝь обновить поѝтавщика")
    
    def delete_supplier(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите поѝтавщика длѝ удалениѝ")
            return
        
        supplier_id = int(self.table.item(selected, 0).text())
        try:
            supplier = session.query(Supplier).filter_by(id=supplier_id).first()
            session.delete(supplier)
            session.commit()
            self.display_section()
        except SQLAlchemyError as e:
            logging.error(f"Ошибка при удалении поѝтавщика: {str(e)}")
            session.rollback()
            QMessageBox.warning(self, "Ошибка", "Не удалоѝь удалить поѝтавщика")
    
    def add_product(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Добавить товар")
        dialog.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FFFFFF, stop:1 #F8F8F8);
                color: #333333;
                border-radius: 10px;
            }
            QLineEdit, QComboBox {
                background-color: #FFFFFF;
                border: 2px solid #DAA520;
                border-radius: 15px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #FFFFFF;
                border: 2px solid #DAA520;
                border-radius: 15px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #FFD700;
            }
        """)
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        name_input = QLineEdit()
        name_input.setPlaceholderText("Название")
        layout.addWidget(name_input)
        
        unit_input = QComboBox()
        try:
            units = session.query(Unit).all()
            unit_input.addItems([unit.unit_name for unit in units])
        except SQLAlchemyError as e:
            logging.error(f"Ошибка при загрузке единиц измерениѝ: {str(e)}")
            session.rollback()
        layout.addWidget(unit_input)
        
        type_input = QComboBox()
        try:
            types = session.query(ProductType).all()
            type_input.addItems([ptype.type_name for ptype in types])
        except SQLAlchemyError as e:
            logging.error(f"Ошибка при загрузке типов товаров: {str(e)}")
            session.rollback()
        layout.addWidget(type_input)
        
        condition_input = QComboBox()
        try:
            conditions = session.query(DeliveryCondition).all()
            condition_input.addItems([condition.condition for condition in conditions])
        except SQLAlchemyError as e:
            logging.error(f"Ошибка при загрузке уѝловий поѝтавки: {str(e)}")
            session.rollback()
        layout.addWidget(condition_input)
        
        add_button = QPushButton("➕ Добавить")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(Qt.gray)
        shadow.setOffset(3, 3)
        add_button.setGraphicsEffect(shadow)
        add_button.setFixedSize(150, 50)
        add_button.clicked.connect(lambda: self.save_product(
            name_input.text(), unit_input.currentText(), type_input.currentText(), condition_input.currentText(), dialog))
        layout.addWidget(add_button, alignment=Qt.AlignCenter)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def save_product(self, name, unit_name, type_name, condition_name, dialog):
        try:
            if not name:
                QMessageBox.warning(dialog, "Ошибка", "Название обѝзательно")
                return
            
            unit = session.query(Unit).filter_by(unit_name=unit_name).first()
            ptype = session.query(ProductType).filter_by(type_name=type_name).first()
            condition = session.query(DeliveryCondition).filter_by(condition=condition_name).first()
            
            product = Product(
                name=name,
                unit_id=unit.id if unit else None,
                type_id=ptype.id if ptype else None,
                condition_id=condition.id if condition else None
            )
            session.add(product)
            session.commit()
            dialog.accept()
            self.display_section()
        except SQLAlchemyError as e:
            logging.error(f"Ошибка базы данных: {str(e)}")
            session.rollback()
            QMessageBox.warning(dialog, "Ошибка", "Не удалоѝь ѝохранить товар")
    
    def edit_product(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите товар длѝ редактированиѝ")
            return
        
        product_id = int(self.table.item(selected, 0).text())
        dialog = QDialog(self)
        dialog.setWindowTitle("Редактировать товар")
        dialog.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FFFFFF, stop:1 #F8F8F8);
                color: #333333;
                border-radius: 10px;
            }
            QLineEdit, QComboBox {
                background-color: #FFFFFF;
                border: 2px solid #DAA520;
                border-radius: 15px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #FFFFFF;
                border: 2px solid #DAA520;
                border-radius: 15px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #FFD700;
            }
        """)
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        name_input = QLineEdit()
        name_input.setPlaceholderText("Название")
        layout.addWidget(name_input)
        
        unit_input = QComboBox()
        try:
            units = session.query(Unit).all()
            unit_input.addItems([unit.unit_name for unit in units])
        except SQLAlchemyError as e:
            logging.error(f"Ошибка при загрузке единиц измерениѝ: {str(e)}")
            session.rollback()
        layout.addWidget(unit_input)
        
        type_input = QComboBox()
        try:
            types = session.query(ProductType).all()
            type_input.addItems([ptype.type_name for ptype in types])
        except SQLAlchemyError as e:
            logging.error(f"Ошибка при загрузке типов товаров: {str(e)}")
            session.rollback()
        layout.addWidget(type_input)
        
        condition_input = QComboBox()
        try:
            conditions = session.query(DeliveryCondition).all()
            condition_input.addItems([condition.condition for condition in conditions])
        except SQLAlchemyError as e:
            logging.error(f"Ошибка при загрузке уѝловий поѝтавки: {str(e)}")
            session.rollback()
        layout.addWidget(condition_input)
        
        save_button = QPushButton("✝ Сохранить")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(Qt.gray)
        shadow.setOffset(3, 3)
        save_button.setGraphicsEffect(shadow)
        save_button.setFixedSize(150, 50)
        save_button.clicked.connect(lambda: self.update_product(
            product_id, name_input.text(), unit_input.currentText(), type_input.currentText(), condition_input.currentText(), dialog))
        layout.addWidget(save_button, alignment=Qt.AlignCenter)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def update_product(self, product_id, name, unit_name, type_name, condition_name, dialog):
        try:
            product = session.query(Product).filter_by(id=product_id).first()
            if name:
                product.name = name
            if unit_name:
                unit = session.query(Unit).filter_by(unit_name=unit_name).first()
                product.unit_id = unit.id if unit else None
            if type_name:
                ptype = session.query(ProductType).filter_by(type_name=type_name).first()
                product.type_id = ptype.id if ptype else None
            if condition_name:
                condition = session.query(DeliveryCondition).filter_by(condition=condition_name).first()
                product.condition_id = condition.id if condition else None
            session.commit()
            dialog.accept()
            self.display_section()
        except SQLAlchemyError as e:
            logging.error(f"Ошибка базы данных: {str(e)}")
            session.rollback()
            QMessageBox.warning(dialog, "Ошибка", "Не удалоѝь обновить товар")
    
    def delete_product(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите товар длѝ удалениѝ")
            return
        
        product_id = int(self.table.item(selected, 0).text())
        try:
            product = session.query(Product).filter_by(id=product_id).first()
            session.delete(product)
            session.commit()
            self.display_section()
        except SQLAlchemyError as e:
            logging.error(f"Ошибка при удалении товара: {str(e)}")
            session.rollback()
            QMessageBox.warning(self, "Ошибка", "Не удалоѝь удалить товар")
    
    def add_product_in_delivery(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Добавить товар в поѝтавку")
        dialog.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FFFFFF, stop:1 #F8F8F8);
                color: #333333;
                border-radius: 10px;
            }
            QLineEdit {
                background-color: #FFFFFF;
                border: 2px solid #DAA520;
                border-radius: 15px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #FFFFFF;
                border: 2px solid #DAA520;
                border-radius: 15px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #FFD700;
            }
        """)
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        product_input = QLineEdit()
        product_input.setPlaceholderText("ID товара")
        layout.addWidget(product_input)
        
        delivery_input = QLineEdit()
        delivery_input.setPlaceholderText("ID поѝтавки")
        layout.addWidget(delivery_input)
        
        planned_price_input = QLineEdit()
        planned_price_input.setPlaceholderText("План. цена")
        layout.addWidget(planned_price_input)
        
        planned_quantity_input = QLineEdit()
        planned_quantity_input.setPlaceholderText("План. кол-во")
        layout.addWidget(planned_quantity_input)
        
        actual_price_input = QLineEdit()
        actual_price_input.setPlaceholderText("Факт. цена")
        layout.addWidget(actual_price_input)
        
        actual_quantity_input = QLineEdit()
        actual_quantity_input.setPlaceholderText("Факт. кол-во")
        layout.addWidget(actual_quantity_input)
        
        add_button = QPushButton("➕ Добавить")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(Qt.gray)
        shadow.setOffset(3, 3)
        add_button.setGraphicsEffect(shadow)
        add_button.setFixedSize(150, 50)
        add_button.clicked.connect(lambda: self.save_product_in_delivery(
            product_input.text(), delivery_input.text(), planned_price_input.text(),
            planned_quantity_input.text(), actual_price_input.text(), actual_quantity_input.text(), dialog))
        layout.addWidget(add_button, alignment=Qt.AlignCenter)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def save_product_in_delivery(self, product_id, delivery_id, planned_price, planned_quantity, 
                                actual_price, actual_quantity, dialog):
        try:
            if not product_id or not delivery_id:
                QMessageBox.warning(dialog, "Ошибка", "ID товара и ID поѝтавки обѝзательны")
                return
            
            item = ProductInDelivery(
                product_id=int(product_id),
                delivery_id=int(delivery_id),
                planned_price=int(planned_price) if planned_price else None,
                planned_quantity=int(planned_quantity) if planned_quantity else None,
                actual_price=int(actual_price) if actual_price else None,
                actual_quantity=int(actual_quantity) if actual_quantity else None
            )
            session.add(item)
            session.commit()
            dialog.accept()
            self.display_section()
        except ValueError as e:
            logging.error(f"Ошибка формата данных: {str(e)}")
            QMessageBox.warning(dialog, "Ошибка", f"Неверный формат данных: {str(e)}")
        except SQLAlchemyError as e:
            logging.error(f"Ошибка базы данных: {str(e)}")
            session.rollback()
            QMessageBox.warning(dialog, "Ошибка", "Не удалоѝь ѝохранить товар в поѝтавке")
    
    def edit_product_in_delivery(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите запиѝь длѝ редактированиѝ")
            return
        
        item_id = int(self.table.item(selected, 0).text())
        dialog = QDialog(self)
        dialog.setWindowTitle("Редактировать товар в поѝтавке")
        dialog.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FFFFFF, stop:1 #F8F8F8);
                color: #333333;
                border-radius: 10px;
            }
            QLineEdit {
                background-color: #FFFFFF;
                border: 2px solid #DAA520;
                border-radius: 15px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #FFFFFF;
                border: 2px solid #DAA520;
                border-radius: 15px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #FFD700;
            }
        """)
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        planned_price_input = QLineEdit()
        planned_price_input.setPlaceholderText("План. цена")
        layout.addWidget(planned_price_input)
        
        planned_quantity_input = QLineEdit()
        planned_quantity_input.setPlaceholderText("План. кол-во")
        layout.addWidget(planned_quantity_input)
        
        actual_price_input = QLineEdit()
        actual_price_input.setPlaceholderText("Факт. цена")
        layout.addWidget(actual_price_input)
        
        actual_quantity_input = QLineEdit()
        actual_quantity_input.setPlaceholderText("Факт. кол-во")
        layout.addWidget(actual_quantity_input)
        
        save_button = QPushButton("✝ Сохранить")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(Qt.gray)
        shadow.setOffset(3, 3)
        save_button.setGraphicsEffect(shadow)
        save_button.setFixedSize(150, 50)
        save_button.clicked.connect(lambda: self.update_product_in_delivery(
            item_id, planned_price_input.text(), planned_quantity_input.text(),
            actual_price_input.text(), actual_quantity_input.text(), dialog))
        layout.addWidget(save_button, alignment=Qt.AlignCenter)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def update_product_in_delivery(self, item_id, planned_price, planned_quantity, 
                                  actual_price, actual_quantity, dialog):
        try:
            item = session.query(ProductInDelivery).filter_by(id=item_id).first()
            if planned_price:
                item.planned_price = int(planned_price)
            if planned_quantity:
                item.planned_quantity = int(planned_quantity)
            if actual_price:
                item.actual_price = int(actual_price)
            if actual_quantity:
                item.actual_quantity = int(actual_quantity)
            session.commit()
            dialog.accept()
            self.display_section()
        except ValueError as e:
            logging.error(f"Ошибка формата данных: {str(e)}")
            QMessageBox.warning(dialog, "Ошибка", f"Неверный формат данных: {str(e)}")
        except SQLAlchemyError as e:
            logging.error(f"Ошибка базы данных: {str(e)}")
            session.rollback()
            QMessageBox.warning(dialog, "Ошибка", "Не удалоѝь обновить товар в поѝтавке")
    
    def delete_product_in_delivery(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите запиѝь длѝ удалениѝ")
            return
        
        item_id = int(self.table.item(selected, 0).text())
        try:
            item = session.query(ProductInDelivery).filter_by(id=item_id).first()
            session.delete(item)
            session.commit()
            self.display_section()
        except SQLAlchemyError as e:
            logging.error(f"Ошибка при удалении товара из поѝтавки: {str(e)}")
            session.rollback()
            QMessageBox.warning(self, "Ошибка", "Не удалоѝь удалить товар из поѝтавки")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    login = LoginWindow()
    if login.exec():
        role = login.role
        window = MainWindow(role)
        window.show()
    sys.exit(app.exec())