import sys
from PySide6.QtWidgets import QApplication
from dialogs.login_dialog import LoginDialog
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    login_dialog = LoginDialog()
    if login_dialog.exec():
        main_window = MainWindow(login_dialog.user_id)
        app.exec()

if __name__ == "__main__":
    main()




