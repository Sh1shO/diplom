STYLESHEET = """
/* === Общие стили === */
QMainWindow, QDialog {
    background-color: #FAFAFA;
    color: #111827;
    font-size: 14px;
    line-height: 1.4;
}

/* === Поля ввода === */
QLineEdit {
    background-color: #FFFFFF;
    color: #111827;
    padding: 6px 6px;
    border: 1px solid #D1D5DB;
    border-radius: 2px;
    font-size: 14px;
    line-height: 1.4;
}
QLineEdit:focus {
    border: 1px solid #2563EB;
    background-color: #FFFFFF;
}
QLineEdit[placeholderText] {
    min-width: 250px;
}

/* === Кнопки === */
QPushButton {
    background-color: #FFFFFF;
    color: #111827;
    padding: 8px 10px;
    border: 1px solid #D1D5DB;
    border-radius: 2px;
    font-weight: 500;
    font-size: 14px;
    line-height: 1.4;
}
QPushButton:hover {
    background-color: #F3F4F6;
}
QPushButton:pressed {
    background-color: #E5E7EB;
}
QPushButton#add_button {
    background-color: #E0F2FE;
    color: #1D4ED8;
}
QPushButton#add_button:hover {
    background-color: #BFDBFE;
}
QPushButton#edit_button {
    background-color: #DCFCE7;
    color: #059669;
}
QPushButton#edit_button:hover {
    background-color: #BBF7D0;
}
QPushButton#delete_button {
    background-color: #FEE2E2;
    color: #B91C1C;
}
QPushButton#delete_button:hover {
    background-color: #FCA5A5;
}
QPushButton#login_button {
    background-color: #FEF3C7;
    color: #92400E;
    font-weight: bold;
    min-width: 180px;
    border: none;
    border-radius: 2px;
    padding: 10px 12px;
}

/* === Таблицы === */
QTableWidget, QTableView {
    border: 1px solid #D1D5DB;
    border-radius: 2px;
    gridline-color: #E5E7EB;
    background-color: #FFFFFF;
    font-size: 14px;
}
QHeaderView::section {
    background-color: #F3F4F6;
    color: #111827;
    padding: 6px;
    font-weight: 600;
    border: none;
    border-bottom: 1px solid #D1D5DB;
}
QTableWidget::item, QTableView::item {
    padding: 6px 4px;
    min-height: 32px;
    line-height: 1.4;
}
QTableWidget::item:selected, QTableView::item:selected {
    background-color: #DBEAFE;
    color: #111827;
}
QTableCornerButton::section {
    background-color: #F3F4F6;
    border: none;
}

/* === Выпадающие списки === */
QComboBox {
    background-color: #FFFFFF;
    border: 1px solid #D1D5DB;
    border-radius: 2px;
    padding: 6px;
    font-size: 14px;
    min-width: 150px;
}
QComboBox:hover {
    background-color: #F9FAFB;
}
QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    selection-background-color: #DBEAFE;
    selection-color: #111827;
    font-size: 14px;
}

/* === Поля дат === */
QDateEdit {
    background-color: #FFFFFF;
    color: #111827;
    padding: 6px;
    border: 1px solid #D1D5DB;
    border-radius: 2px;
    font-size: 14px;
    line-height: 1.4;
}

/* === Метки === */
QLabel {
    color: #111827;
    background: transparent;
    padding: 4px 8px; /* Увеличили горизонтальный padding */
    font-size: 14px;
    line-height: 1.4;
    min-width: 100px; /* Минимальная ширина */
    text-align: left; /* Явное выравнивание */
}
QLabel#login_title_label {
    font-size: 18px;
    font-weight: bold;
}
QLabel#login_subtitle_label {
    font-size: 14px;
    color: #6B7280;
}

/* === Вкладки === */
QTabWidget::pane {
    border: 1px solid #D1D5DB;
    border-radius: 2px;
    background-color: #FFFFFF;
}
QTabBar::tab {
    background-color: #E5E7EB;
    color: #1F2937;
    padding: 8px 12px;
    font-weight: 500;
    font-size: 14px;
    border: 1px solid #D1D5DB;
    border-bottom: none;
    border-top-left-radius: 2px;
    border-top-right-radius: 2px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background-color: #FFFFFF;
    color: #1D4ED8;
    border: 1px solid #3B82F6;
    border-bottom: none;
}
QTabBar::tab:hover {
    background-color: #F3F4F6;
}

/* === Списки === */
QListWidget {
    background-color: #FFFFFF;
    border: 1px solid #D1D5DB;
    border-radius: 2px;
    padding: 6px;
    font-size: 14px;
}
QListWidget::item:selected {
    background-color: #DBEAFE;
    color: #111827;
}

/* === Группы === */
QGroupBox {
    background-color: #FFFFFF;
    border: 1px solid #D1D5DB;
    border-radius: 2px;
    padding: 12px; /* Увеличили padding */
    font-size: 14px;
    font-weight: bold;
    color: #111827;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 4px;
}

/* === Сообщения === */
QMessageBox {
    background-color: #FFFFFF;
    border-radius: 2px;
    font-size: 14px;
}
QMessageBox QLabel {
    font-size: 14px;
}
QMessageBox QPushButton {
    padding: 8px 10px;
    border: 1px solid #D1D5DB;
    background-color: #F9FAFB;
    font-size: 14px;
}
QMessageBox QPushButton:hover {
    background-color: #E5E7EB;
}
"""