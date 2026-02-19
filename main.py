import sys
from PySide6.QtWidgets import QApplication
from missionmanager.storage import JsonStorage
from missionmanager.app import AppService
from missionmanager.ui.views import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    storage = JsonStorage()
    service = AppService(storage)

    window = MainWindow(service)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
