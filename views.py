# PySide6 GUIアプリ
from typing import Callable, Optional  

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QCheckBox,
    QPushButton,
    QProgressBar,
    QComboBox,
    QScrollArea,
    QFrame,
    QInputDialog,
    QMessageBox,
)

from models import Genre, Mission, Task


class TaskItem(QWidget):
    # タスク1件分UI

    toggled = Signal()    # チェック変更通知

    def __init__(self, task: Task, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.task = task

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)    # 余白設定

        self.check = QCheckBox(task.name)
        self.check.setChecked(task.done)
        self.check.toggled.connect(self._on_toggled)

        layout.addWidget(self.check, 1)


    def _on_toggled(self, checked: bool) -> None:
        # チェックボックスの状態をTaskモデルに反映し、親に通知
        self.task.done = checked
        self.toggled.emit()


    def _on_state_changed(self, state: int) -> None:
        # Qt.CheckStateを直接扱う場合の別ハンドラ 現在は未使用
        self.task.done = state == Qt.CheckState.Checked
        self.toggled.emit()


class MissionCard(QFrame):
    # ミッションカードUIを表示

    changed = Signal()    # タスクの変更、追加で進歩再計算を通知

    def __init__(self, mission: Mission, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.mission = mission
        self.setFrameShape(QFrame.StyledPanel)
        self.setObjectName("missionCard")

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)
    
        # ヘッダー(ミッション)
        header = QHBoxLayout()
        self.title = QLabel(self.mission.name)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self._apply_progress()

        self.toggle_btn = QPushButton("タスクを表示/非表示")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setChecked(False)    # 初期はタスク未展開
        self.toggle_btn.toggled.connect(self._toggle_body)

        header.addWidget(self.title, 1)
        header.addWidget(self.progress, 2)
        header.addWidget(self.toggle_btn)
        root.addLayout(header)

        # ボディ(タスク)
        self.body = QWidget()
        body_layout = QVBoxLayout(self.body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(4)

        # 既存タスクの描画
        self.task_items: list[TaskItem] = []
        for t in self.mission.tasks:
            item = TaskItem(t)
            item.toggled.connect(self._on_task_changed)
            self.task_items.append(item)
            body_layout.addWidget(item)

        # タスク追加ボタン
        add_row = QHBoxLayout()
        add_btn = QPushButton("タスク追加")
        add_btn.clicked.connect(self._add_task)
        add_row.addStretch(1)
        add_row.addWidget(add_btn)
        body_layout.addLayout(add_row)

        root.addWidget(self.body)


    # --- 内部処理 ---

    def _toggle_body(self, checked: bool) -> None:
        self.body.setVisible(checked)


    def _apply_progress(self) -> None:
        # 0.0~1.0 → 0~100 に変換
        self.progress.setValue(int(self.mission.progress * 100))
        # 見やすく
        self.progress.setTextVisible(True)


    def _on_task_changed(self) -> None:
        self._apply_progress()
        self.changed.emit()

        
    def _add_task(self) -> None:
        name, ok = QInputDialog.getText(self, "タスク追加", "タスクを入力:")
        if not ok or not name.strip():
            return
        task = Task(name=name.strip(), done=False)
        self.mission.tasks.append(task)

        # UI行を追加
        item = TaskItem(task)
        item.toggled.connect(self._on_task_changed)
        self.task_items.append(item)
        self.body.layout().insertWidget(len(self.task_items) - 1, item)
        self._apply_progress()
        self.changed.emit()
        

class MainWindow(QWidget):
    # アプリ全体のコンテナ

    def __init__(self, genres: list[Genre], save_callback: Callable[[list[Genre]], None]) -> None:
        super().__init__()
        self.setWindowTitle("MissionManager")
        self.resize(900, 620)
        self.genres = genres
        self.save_callback = save_callback

        # ルートレイアウト
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        # 上部バー: ジャンル選択・追加
        top = QHBoxLayout()
        self.genre_combo = QComboBox()
        self._reload_genre_combo()
        self.genre_combo.currentIndexChanged.connect(self._render_missions)

        add_genre_btn = QPushButton("ジャンル追加")
        add_genre_btn.clicked.connect(self._add_genre)

        top.addWidget(QLabel("ジャンル:"))
        top.addWidget(self.genre_combo, 1)
        top.addWidget(add_genre_btn)

        root.addLayout(top)

        # ミッション一覧(スクロール)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)

        self.mission_container = QWidget()
        self.mission_layout = QVBoxLayout(self.mission_container)
        self.mission_layout.setContentsMargins(0, 0, 0, 0)
        self.mission_layout.setSpacing(8)
        self.mission_layout.addStretch(1)

        self.scroll.setWidget(self.mission_container)
        root.addWidget(self.scroll, 1)

        # 下部バー: ミッション追加
        bottom = QHBoxLayout()
        add_mission_btn = QPushButton("ミッション追加")
        add_mission_btn.clicked.connect(self._add_mission)
        bottom.addStretch(1)
        bottom.addWidget(add_mission_btn)
        root.addLayout(bottom)

        # 初回レンダリング
        self._render_missions()


    # データアクセス補助
    def _current_genre(self) -> Optional[Genre]:
        idx = self.genre_combo.currentIndex()
        if idx < 0 or idx >= len(self.genres):
            return None
        return self.genres[idx]


    def _save(self) -> None:
        self.save_callback(self.genres)


    def _reload_genre_combo(self) -> None:
        self.genre_combo.clear()
        self.genre_combo.addItems([g.name for g in self.genres])


    # ジャンル操作
    def _add_genre(self) -> None:
        name, ok = QInputDialog.getText(self, "ジャンル追加", "ジャンルを入力:")
        if not ok or not name.strip():
            return
        self.genres.append(Genre(name=name.strip()))
        self._reload_genre_combo()
        self.genre_combo.setCurrentIndex(len(self.genres) - 1)
        self._save()


    # ミッション描写・操作
    def _clear_missions_ui(self) -> None:
        layout = self.mission_layout
        # 末尾のストレッチ以外を削除
        for i in reversed(range(layout.count() - 1)):
            item = layout.itemAt(i)
            w = item.widget()
            if w is not None:
                w.setParent(None)


    def _render_missions(self) -> None:
        self._clear_missions_ui()
        genre = self._current_genre()
        if genre is None:
            return
        for m in genre.missions:
            card = MissionCard(m)
            card.changed.connect(self._save)
            self.mission_layout.insertWidget(self.mission_layout.count() - 1, card)


    def _add_mission(self) -> None:
        genre = self._current_genre()
        if genre is None:
            QMessageBox.warning(self,"警告", "ジャンルを作成して下さい。")
            return
        name, ok = QInputDialog.getText(self, "ミッション追加", "ミッションを入力:")
        if not ok or not name.strip():
            return
        mission = Mission(name=name.strip())
        genre.missions.append(mission)
        self._save()
        self._render_missions()
