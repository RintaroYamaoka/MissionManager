# メイン処理
import sys
from PySide6.QtWidgets import QApplication

from storage import JsonStorage
from views import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    storage = JsonStorage()
    genres = storage.load_genres()


    def save_callback(updated):
        storage.save_genres(updated)


    window = MainWindow(genres, save_callback)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()