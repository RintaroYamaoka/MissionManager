# PySide6 GUIアプリ
from typing import Callable, Optional  

from PySide6.QtCore import Qt, Signal, QPoint
from datetime import datetime
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
    QToolButton,
    QMenu,
)

from models import Genre, Mission, Task


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


class TaskItem(QWidget):
    # タスク1件分UI

    toggled = Signal()    # チェック変更通知

    def __init__(
            self,
            task: Task,
            mission: Mission,
            save_callback: Callable,
            parent: Optional[QWidget] = None
    ) -> None:
        
        super().__init__(parent)
        self.task = task
        self.mission = mission
        self.save_callback = save_callback

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.check = QCheckBox(task.name)
        self.check.setChecked(task.done)
        self.check.toggled.connect(self._on_toggled)
        layout.addWidget(self.check, 1)
        
        self.time_label = QLabel("")
        self.time_label.setStyleSheet("color:#888; font-size:11px;")
        layout.addWidget(self.time_label)

        # 右クリックメニュー
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._open_menu)

        # 初期表示
        self._refresh_time_label()


    # 完了日時の反映
    def _refresh_time_label(self) -> None:
        self.time_label.setText(self.task.completed_at or "")    
       

    # チェック状態に応じて完了日時を自動設定/解除
    def _on_toggled(self, checked: bool) -> None: 
        self.task.done = checked
        self.task.completed_at = now_str() if checked else None   
        self._refresh_time_label()
        self.toggled.emit()    


    # 右クリックメニュー
    def _open_menu(self, pos: QPoint) -> None:
        menu = QMenu(self)
        act_rename = menu.addAction("変更")
        act_delete = menu.addAction("削除")
        chosen = menu.exec(self.mapToGlobal(pos))
        if chosen == act_delete:
            self._delete_task()
        elif chosen == act_rename:
            self._rename_task() 


    def _rename_task(self) -> None:
        new_name, ok = QInputDialog.getText(self, "タスク名の変更", "タスク:", text=self.task.name )
        if ok and new_name.strip():
            self.task.name = new_name.strip()
            self.check.setText(self.task.name)
            self.save_callback()

    
    def _delete_task(self) -> None:
        if QMessageBox.question(self, "確認", f"タスク「{self.task.name}」を削除しますか?") == QMessageBox.Yes:
               self.mission.tasks.remove(self.task)
               self.save_callback()
               self.setParent(None)


class MissionCard(QFrame):
    # ミッションカードUIを表示

    changed = Signal()    # タスクの変更、追加、期限変更で通知

    def __init__(
            self,
            mission: Mission,
            genre: Genre,
            save_callback,
            parent: Optional[QWidget] = None
        ) -> None:

        super().__init__(parent)
        self.mission = mission
        self.genre = genre
        self.save_callback = save_callback

        self.setFrameShape(QFrame.StyledPanel)
        self.setObjectName("missionCard")

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)
    
        # ヘッダー
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setContentsMargins(0, 0, 0, 0)
        title_box.setSpacing(2)

        self.title = QLabel(self.mission.name)

        meta_row = QHBoxLayout()
        meta_row.setContentsMargins(0, 0, 0, 0)
        meta_row.setSpacing(8)

        self.due_label = QLabel("")     # 期限
        self.done_label = QLabel("")    # ミッション完了日時
        self.due_label.setStyleSheet("color:#aaa; font-size:11px;")
        self.done_label.setStyleSheet("color:#888; font-size:11px;")

        meta_row.addWidget(self.due_label)
        meta_row.addWidget(self.done_label)
        meta_row_container = QWidget()
        meta_row_container.setLayout(meta_row)

        title_box.addWidget(self.title)
        title_box.addWidget(meta_row_container)

        title_container = QWidget()
        title_container.setLayout(title_box)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self._apply_progress()

        self.toggle_btn = QPushButton("タスクの表示")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setChecked(False)    
        self.toggle_btn.toggled.connect(self._toggle_body)

        header.addWidget(title_container, 1)
        header.addWidget(self.progress, 2)
        header.addWidget(self.toggle_btn)
        root.addLayout(header)

        # ボディ(タスク一覧)
        self.body = QWidget()
        body_layout = QVBoxLayout(self.body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(4)

        self.task_items: list[TaskItem] = []
        for t in self.mission.tasks:
            item = TaskItem(t, self.mission, self._save_and_emit)
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

        self.body.setVisible(False)    # 初期状態でタスクを折りたたむ

        # 右クリックメニュー（ミッション）
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._open_mission_menu)

        # 初期メタ表示を反映
        self._refresh_meta_labels()
        self._update_mission_completion(force=True)


    # 期限とミッション完了日時のラベルを更新
    def _refresh_meta_labels(self) -> None:
        due_txt = f"期限: {self.mission.due_date}" if self.mission.due_date else "期限: -"
        done_txt = f"完了: {self.mission.completed_at}" if self.mission.completed_at else "完了: -"
        self.due_label.setText(due_txt)
        self.done_label.setText(done_txt)


    # 保存と通知
    def _save_and_emit(self) -> None:
        self.save_callback()
        self.changed.emit()


    # 進捗に応じてミッション完了日時を自動管理
    def _update_mission_completion(self, force: bool = False) -> None:
        if self.mission.progress >= 1.0:
            if force or not self.mission.completed_at:
                self.mission.completed_at = now_str()
        else:
            if self.mission.completed_at is not None:
                self.mission.completed_at = None
        self._refresh_meta_labels()


    # イベント処理
    def _toggle_body(self, checked: bool) -> None:
        self.body.setVisible(checked)


    def _apply_progress(self) -> None:
        # 0.0~1.0 → 0~100 に変換
        self.progress.setValue(int(self.mission.progress * 100))
        # 見やすく
        self.progress.setTextVisible(True)


    def _on_task_changed(self) -> None:
        self._apply_progress()
        self._update_mission_completion()
        self.save_callback()

        
    def _add_task(self) -> None:
        name, ok = QInputDialog.getText(self, "タスク追加", "タスクを入力:")
        if not ok or not name.strip():
            return
        task = Task(name=name.strip(), done=False)
        self.mission.tasks.append(task)

        # UI行を追加
        item = TaskItem(task, self.mission, self.save_callback)
        item.toggled.connect(self._on_task_changed)
        self.task_items.append(item)
        self.body.layout().insertWidget(len(self.task_items) - 1, item)
        self._apply_progress()
        self._update_mission_completion()
        self.save_callback()


    def _open_mission_menu(self, pos: QPoint) -> None:
        menu = QMenu(self)
        act_rename = menu.addAction("名前変更")
        act_due    = menu.addAction("期限を編集")
        act_delete = menu.addAction("削除")
        chosen = menu.exec(self.mapToGlobal(pos))
        if chosen == act_delete:
            self._delete_mission()
        elif chosen == act_rename:
            self._rename_mission()
        elif chosen == act_due:
            self._edit_due_date()


    def _rename_mission(self) -> None:
        new_name, ok = QInputDialog.getText(self, "ミッション名の変更", "ミッション：", text=self.mission.name)
        if ok and new_name.strip():
            self.mission.name = new_name.strip()
            self.title.setText(self.mission.name)
            self._save_and_emit()

    def _edit_due_date(self) -> None:
        # 期限は YYYY-MM-DD 文字列（空欄可）
        text, ok = QInputDialog.getText(
            self,
            "期限を編集",
            "期限（YYYY-MM-DD、空欄可）：",
            text=self.mission.due_date or "",
        )
        if not ok:
            return
        self.mission.due_date = text.strip() or None
        self._refresh_meta_labels()
        self._save_and_emit()

    def _delete_mission(self) -> None:
        if QMessageBox.question(self, "確認", f"ミッション「{self.mission.name}」を削除しますか？") == QMessageBox.Yes:
            self.genre.missions.remove(self.mission)
            self.save_callback()
            self.setParent(None)            
        

class MainWindow(QWidget):
    # アプリ全体のコンテナ

    def __init__(self, genres: list[Genre], save_callback: Callable[[list[Genre]], None]) -> None:
        super().__init__()
        self.setWindowTitle("MissionManager")
        self.resize(780, 540)
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
        self.genre_combo.setContextMenuPolicy(Qt.CustomContextMenu)
        self.genre_combo.customContextMenuRequested.connect(self._open_genre_menu)

        add_genre_btn = QToolButton()
        add_genre_btn.setText("追加")
        add_genre_btn.clicked.connect(self._add_genre)

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


    # 右クリックメニュー
    def _open_genre_menu(self, pos: QPoint) -> None:
        menu = QMenu(self)
        act_rename = menu.addAction("名前変更")
        act_delete = menu.addAction("削除")
        chosen = menu.exec(self.genre_combo.mapToGlobal(pos))
        
        if chosen == act_rename:
            self._rename_genre()
        elif chosen == act_delete:
            self._delete_genre()    


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


    def _rename_genre(self) -> None:
        genre = self._current_genre()
        if not genre:
            return
        new_name, ok = QInputDialog.getText(self, "ジャンル名変更", "新しいジャンル名:", text=genre.name)
        if ok and new_name.strip():
            genre.name = new_name.strip()
            self._reload_genre_combo()
            self._save()
    


    # ジャンル削除
    def _delete_genre(self) -> None:
        genre = self._current_genre()
        if not genre:
            return
        if QMessageBox.question(self, "確認", f"ジャンル「{genre.name}」を削除しますか？") == QMessageBox.Yes:
            self.genres.remove(genre)
            self._reload_genre_combo()
            self._save()
            self._render_missions()


    # ミッション描写・操作
    def _clear_missions_ui(self) -> None:
        layout = self.mission_layout
        # 末尾のストレッチ以外を削除
        for i in reversed(range(layout.count() - 1)):
            item = layout.itemAt(i)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                
    
    # 期限（YYYY-MM-DD）昇順に並べて未設定(None)は最後に回す
    def _sorted_missions(self, genre: Genre) -> list[Mission]:
        def key(m: Mission):
            return (m.due_date or "9999-12-31", m.name.lower())
        return sorted(genre.missions, key=key)


    def _render_missions(self) -> None:
        self._clear_missions_ui()
        genre = self._current_genre()
        if genre is None:
            return
        for m in self._sorted_missions(genre):  # ソート結果で描画
            card = MissionCard(m, genre, self._save)
            card.changed.connect(self._after_mission_changed)  # 変更後に再描画
            self.mission_layout.insertWidget(self.mission_layout.count() - 1, card)


    # 保存後に並べ替えを即反映
    def _after_mission_changed(self) -> None:
        self._save()
        self._render_missions()            


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
