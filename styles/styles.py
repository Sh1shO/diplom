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
    /* Специфические стили для поля поиска */
    QLineEdit#search_input { 
        min-width: 250px; 
        padding-left: 35px; /* Отступ для иконки поиска */
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
        align: center; /* Центрирование всей панели вкладок */
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
        text-align: center; /* Центрирование текста внутри вкладки */
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
        padding: 8px 30px 8px 10px; /* Отступ справа для стрелки */
        font-size: 14px; 
        font-family: 'Inter', 'Roboto', sans-serif; 
        border-radius: 6px; 
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05); 
        min-width: 200px; /* Фиксированная минимальная ширина для отчетов */
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FFFFFF, stop:0.95 #F7F9FC); /* Лёгкий градиент для визуального эффекта */
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
        image: none; /* Убрали кастомную стрелку */
        width: 12px; 
        height: 12px; 
    }

    /* Логотип */
    QLabel#logo_label {
        padding: 10px;
        background: transparent;
    }
"""