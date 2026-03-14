from PySide6.QtWidgets import QApplication
from presenter import MainWindow
import sys
import multiprocessing




if __name__ == "__main__":
    multiprocessing.freeze_support()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

