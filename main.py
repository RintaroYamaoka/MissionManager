# メイン処理（依存度を下げた理想設計版）
import sys
from PySide6.QtWidgets import QApplication
from storage import JsonStorage
from app import AppService
from views import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    storage = JsonStorage()
    service = AppService(storage)

    window = MainWindow(service)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
