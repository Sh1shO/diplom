STYLESHEET = """
/* Основной стиль приложения в стиле 1С */
QWidget {
    background-color: #FFFFFF;
    color: #525253;
    font-family: Arial, sans-serif;
    font-size: 12px;
}

/* Левая панель (меню) */
QListWidget#menuList {
    background-color: #F6F2A5;
    color: #525253;
    border: 1px solid #525253;
}

QListWidget#menuList::item {
    padding: 5px 10px;
}

QListWidget#menuList::item:selected {
    background-color: #F4EA97;
    color: #525253;
}

/* Кнопки */
QPushButton {
    background-color: #F3E742;
    color: #525253;
    border: 1px solid #525253;
    border-radius: 3px;
    padding: 5px 10px;
    min-height: 30px;
}

QPushButton:hover {
    background-color: #E6D93B;
}

QPushButton:pressed {
    background-color: #D8CC34;
}

QPushButton:disabled {
    background-color: #EEEEEE;
    color: #A0A0A0;
    border: 1px solid #A0A0A0;
}

/* Поля ввода */
QLineEdit {
    background-color: #FFFFFF;
    color: #525253;
    border: 1px solid #525253;
    border-radius: 2px;
    padding: 5px;
    min-height: 30px;
}

QLineEdit:focus {
    border: 1px solid #F3E742;
}

/* Комбобоксы */
QComboBox {
    background-color: #FFFFFF;
    color: #525253;
    border: 1px solid #525253;
    border-radius: 2px;
    padding: 5px;
    min-height: 30px;
}

QComboBox:hover {
    background-color: #F6F2A5;
}

QComboBox:focus {
    border: 1px solid #F3E742;
}

QComboBox::drop-down {
    border: none;
    background-color: #F3E742;
    width: 20px;
}

QComboBox::down-arrow {
    image: url(down_arrow.png); /* Замените на путь к иконке, если есть */
    width: 12px;
    height: 12px;
}

QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    color: #525253;
    selection-background-color: #F4EA97;
    selection-color: #525253;
    border: 1px solid #525253;
}

/* Таблицы */
QTableWidget, QTableView {
    background-color: #FFFFFF;
    color: #525253;
    border: 1px solid #525253;
    gridline-color: #525253;
}

QTableWidget::item, QTableView::item {
    padding: 5px;
}

QTableWidget::item:selected, QTableView::item:selected {
    background-color: #F4EA97;
    color: #525253;
}

QHeaderView::section {
    background-color: #F6F2A5;
    color: #525253;
    border: 1px solid #525253;
    padding: 5px;
    font-weight: bold;
}

/* Вкладки */
QTabWidget::pane {
    border: 1px solid #525253;
    background-color: #FFFFFF;
}

QTabBar::tab {
    background-color: #F6F2A5;
    color: #525253;
    border: 1px solid #525253;
    border-bottom: none;
    padding: 8px 15px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #F3E742;
    font-weight: bold;
}

QTabBar::tab:hover {
    background-color: #E6D93B;
}

/* Группы */
QGroupBox {
    border: 1px solid #525253;
    border-radius: 3px;
    margin-top: 10px;
    background-color: #FFFFFF;
    color: #525253;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px;
    color: #525253;
}

/* Метки */
QLabel {
    color: #525253;
    padding: 5px;
}

/* Списки */
QListWidget {
    background-color: #FFFFFF;
    color: #525253;
    border: 1px solid #525253;
}

QListWidget::item {
    padding: 5px;
}

QListWidget::item:selected {
    background-color: #F4EA97;
    color: #525253;
}

/* Календарь и дата */
QDateEdit {
    background-color: #FFFFFF;
    color: #525253;
    border: 1px solid #525253;
    border-radius: 2px;
    padding: 5px;
    min-height: 30px;
}

QDateEdit:focus {
    border: 1px solid #F3E742;
}

QCalendarWidget {
    background-color: #FFFFFF;
    color: #525253;
}

QCalendarWidget QAbstractItemView {
    selection-background-color: #F4EA97;
    selection-color: #525253;
}

/* Чекбоксы */
QCheckBox {
    color: #525253;
    padding: 5px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #525253;
    background-color: #FFFFFF;
}

QCheckBox::indicator:checked {
    background-color: #F3E742;
    image: url(check.png); /* Замените на путь к иконке, если есть */
}

QCheckBox::indicator:unchecked:hover {
    background-color: #E6D93B;
}

/* Полосы прокрутки */
QScrollBar:vertical, QScrollBar:horizontal {
    background-color: #FFFFFF;
    border: 1px solid #525253;
}

QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background-color: #F3E742;
    border: 1px solid #525253;
    min-height: 20px;
    min-width: 20px;
}

QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
    background-color: #E6D93B;
}

QScrollBar::add-line, QScrollBar::sub-line {
    background-color: #FFFFFF;
    border: 1px solid #525253;
}

QScrollBar::add-page, QScrollBar::sub-page {
    background-color: #FFFFFF;
}
"""