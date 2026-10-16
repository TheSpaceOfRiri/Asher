import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from ui.companion_window import CompanionWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Asher")
    app.setQuitOnLastWindowClosed(False)

    window = CompanionWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()