import sys
from PyQt6.QtWidgets import QApplication
from src.app import MainWindow
from src.utils.constants import APP_NAME


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
