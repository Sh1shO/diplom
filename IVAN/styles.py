STYLESHEET = """
    QDialog, QMainWindow {
        background: #F8F8F8;
        color: #333333;
    }

    QLineEdit {
        background-color: #FFFFFF;
        color: #333333;
        padding: 10px;
        font-size: 16px;
        font-family: 'Arial', sans-serif;
        border-radius: 4px;
    }
    QLineEdit:focus {
        background-color: #FFFACD;
    }
    QLineEdit#search_input {
        min-width: 300px;
        padding-left: 40px;
        background: #FFFFFF;
        background-size: 20px;
    }
    QLineEdit#search_input:focus {
        background-color: #FFFACD;
    }

    QPushButton {
        background-color: #FFFFFF;
        color: #333333;
        padding: 12px 20px;
        font-size: 16px;
        font-family: 'Arial', sans-serif;
        border-radius: 4px;
    }
    QPushButton:hover {
        background-color: #FFD700;
    }
    QPushButton:pressed {
        background-color: #DAA520;
    }
    QPushButton#delete_button {
        background-color: #FECACA;
        color: #B91C1C;
        min-width: 180px;
        min-height: 50px;
    }
    QPushButton#delete_button:hover {
        background-color: #FCA5A5;
    }
    QPushButton#add_button {
        background-color: #BFDBFE;
        color: #1E3A8A;
        min-width: 180px;
        min-height: 50px;
    }
    QPushButton#add_button:hover {
        background-color: #93C5FD;
    }
    QPushButton#edit_button {
        background-color: #D1FAE5;
        color: #065F46;
        min-width: 180px;
        min-height: 50px;
    }
    QPushButton#edit_button:hover {
        background-color: #A7F3D0;
    }
    QPushButton#login_button {
        background: #FFD700;
        color: #333333;
        padding: 12px 24px;
        font-size: 16px;
        font-weight: bold;
        font-family: 'Arial', sans-serif;
        border-radius: 4px;
        min-width: 220px;
    }
    QPushButton#login_button:hover {
        background: #DAA520;
    }

    QTableWidget {
        font-size: 16px;
        font-family: 'Arial', sans-serif;
    }

    QTabWidget::pane {
        background-color: #F8F8F8;
    }
    QTabBar {
        alignment: center;
    }
    QTabBar::tab {
        background-color: #FFFFFF;
        color: #333333;
        padding: 10px 20px;
        font-size: 16px;
        font-family: 'Arial', sans-serif;
        margin-right: 2px;
        border-radius: 4px 4px 0 0;
    }
    QTabBar::tab:selected {
        background-color: #FFFACD;
        color: #333333;
    }
    QTabBar::tab:hover {
        background-color: #FFD700;
    }

    QListWidget {
        background: #FFFFFF;
        color: #333333;
        font-size: 16px;
        font-family: 'Arial', sans-serif;
        border-radius: 4px;
    }
    QListWidget::item {
        padding: 10px;
    }
    QListWidget::item:selected {
        background-color: #FFFACD;
        color: #333333;
    }

    QLabel {
        color: #333333;
        font-size: 16px;
        font-family: 'Arial', sans-serif;
        padding: 6px;
        background-color: transparent;
    }
    QLabel#login_title_label {
        font-size: 16px;
        color: #333333;
        font-weight: bold;
        background: transparent;
        padding: 0;
        margin-bottom: 10px;
    }
    QLabel#login_subtitle_label {
        font-size: 16px;
        color: #555555;
        font-weight: normal;
        background: transparent;
        padding: 0;
        margin-bottom: 20px;
    }
    QLabel#logo_label {
        background: transparent;
        padding: 0;
        margin-bottom: 20px;
    }
    QLabel#delivery_label {
        color: #DAA520;
        font-size: 16px;
        font-weight: bold;
        font-family: 'Arial', sans-serif;
        padding: 6px;
    }

    QDateEdit {
        background-color: #FFFFFF;
        color: #333333;
        padding: 10px;
        font-size: 16px;
        font-family: 'Arial', sans-serif;
        border-radius: 4px;
    }
    QDateEdit:focus {
        background-color: #FFFACD;
    }

    QComboBox {
        background-color: #FFFFFF;
        color: #333333;
        padding: 8px;
        font-size: 16px;
        font-family: 'Arial', sans-serif;
        border-radius: 4px;
        min-width: 150px;
        max-width: 200px;
    }
    QComboBox:hover {
        background-color: #FFFACD;
    }
    QComboBox QAbstractItemView {
        background-color: #FFFFFF;
        color: #333333;
        selection-background-color: #FFFACD;
        selection-color: #333333;
        font-size: 16px;
        font-family: 'Arial', sans-serif;
        border-radius: 4px;
    }
    QComboBox::drop-down {
        width: 30px;
    }

    QMessageBox {
        background: #F8F8F8;
        color: #333333;
        border-radius: 4px;
    }
    QMessageBox QLabel {
        color: #333333;
        font-size: 16px;
        padding-bottom: 6px;
    }
    QMessageBox QPushButton {
        background-color: #FFFFFF;
        border-radius: 4px;
        padding: 10px;
        font-size: 16px;
    }
    QMessageBox QPushButton:hover {
        background-color: #FFD700;
    }

    QDialog#loginDialog {
        background: #FFF8DC;
        border-radius: 4px;
    }
"""