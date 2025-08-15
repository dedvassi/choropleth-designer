import sys
from PyQt6.QtWidgets import QApplication
from app import ChoroplethApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChoroplethApp()
    window.show()
    sys.exit(app.exec())


