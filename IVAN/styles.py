STYLESHEET = """
/* === Общие стили === */
QMainWindow, QDialog {
    background-color: #FAFAFA;
    color: #111827;
    font-family: 'Segoe UI', sans-serif;
    font-size: 14px;
}

/* === Поля ввода === */
QLineEdit {
    background-color: #FFFFFF;
    color: #111827;
    padding: 4px 6px;
    border: 1px solid #D1D5DB;
    border-radius: 2px;
    font-size: 14px;
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
    padding: 6px 10px;
    border: 1px solid #D1D5DB;
    border-radius: 2px;
    font-weight: 500;
    font-size: 14px;
}
QPushButton:hover {
    background-color: #F3F4F6;
}
QPushButton:pressed {
    background-color: #E5E7EB;
}
QPushButton#add_button {
    background-color: #EFF6FF;
    color: #1D4ED8;
    font-weight: 600;
}
QPushButton#add_button:hover {
    background-color: #DBEAFE;
}
QPushButton#edit_button {
    background-color: #ECFDF5;
    color: #047857;
    font-weight: 600;
}
QPushButton#edit_button:hover {
    background-color: #D1FAE5;
}
QPushButton#delete_button {
    background-color: #FEF2F2;
    color: #B91C1C;
    font-weight: 600;
}
QPushButton#delete_button:hover {
    background-color: #FCA5A5;
}
QPushButton#login_button {
    background-color: #FACC15;
    color: #1F2937;
    font-weight: bold;
    min-width: 180px;
    border: none;
    border-radius: 2px;
}
QPushButton#login_button:hover {
    background-color: #FBBF24;
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
    padding: 4px;
    min-height: 30px;
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
    padding: 4px;
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
    padding: 4px;
    border: 1px solid #D1D5DB;
    border-radius: 2px;
    font-size: 14px;
}

/* === Метки === */
QLabel {
    color: #111827;
    background: transparent;
    padding: 2px;
    font-size: 14px;
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
    padding: 6px 12px;
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
    padding: 4px;
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
    padding: 6px;
    font-size: 14px;
    font-weight: bold;
    color: #111827;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px;
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
    padding: 6px 10px;
    border: 1px solid #D1D5DB;
    background-color: #F9FAFB;
    font-size: 14px;
}
QMessageBox QPushButton:hover {
    background-color: #E5E7EB;
}
"""
