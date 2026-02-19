from __future__ import annotations
from typing import Optional
from PySide6.QtCore import Qt, QPoint, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QComboBox,
    QScrollArea,
    QFrame,
    QInputDialog,
    QMessageBox,
    QToolButton,
    QMenu,
)
from missionmanager.models import GenreDict
from missionmanager.app import AppService
from missionmanager.ui.mission_card import MissionCard
from missionmanager.ui.add_dialogs import get_genre_add_input, get_mission_add_input


class MainWindow(QWidget):
    """
    既存UIを踏襲：
    - 上部: ジャンル選択コンボ + 追加ボタン
    - 中央: ミッションカード群（スクロール）
    - 下部: ミッション追加ボタン
    右クリック操作：
    - ジャンル: 名前変更/上へ/下へ/削除
    - ミッション: 名前変更/期限編集/上へ/下へ/削除
    - タスク: 名前変更/上へ/下へ/削除（カード内）
    """
    def __init__(self, service: AppService) -> None:
        super().__init__()
        self.setWindowTitle("MissionManager")
        self.resize(780, 540)
        self.service = service

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

    # ---------- genre context menu ----------
    def _open_genre_menu(self, pos: QPoint) -> None:
        menu = QMenu(self)
        act_rename = menu.addAction("名前変更")
        act_up     = menu.addAction("上へ移動")
        act_down   = menu.addAction("下へ移動")
        act_delete = menu.addAction("削除")
        chosen = menu.exec(self.genre_combo.mapToGlobal(pos))

        if chosen == act_rename:
            self._rename_genre()
        elif chosen == act_delete:
            self._delete_genre()
        elif chosen == act_up:
            idx = self.genre_combo.currentIndex()
            if idx >= 0:
                self.service.move_genre_up(idx)
                self._reload_genre_combo()
                self.genre_combo.setCurrentIndex(max(0, idx-1))
                self._render_missions()
        elif chosen == act_down:
            idx = self.genre_combo.currentIndex()
            if idx >= 0:
                self.service.move_genre_down(idx)
                self._reload_genre_combo()
                self.genre_combo.setCurrentIndex(min(self.genre_combo.count()-1, idx+1))
                self._render_missions()

    # ---------- helpers ----------
    def _current_genre(self) -> Optional[GenreDict]:
        idx = self.genre_combo.currentIndex()
        if idx < 0 or idx >= len(self.service.genres):
            return None
        return self.service.genres[idx]

    def _reload_genre_combo(self) -> None:
        self.genre_combo.clear()
        self.genre_combo.addItems([g.get("name", "") for g in self.service.genres])

    def _clear_missions_ui(self) -> None:
        layout = self.mission_layout
        for i in reversed(range(layout.count() - 1)):  # keep the final stretch
            item = layout.itemAt(i)
            w = item.widget()
            if w is not None:
                w.setParent(None)

    # ---------- genre ops ----------
    def _add_genre(self) -> None:
        result = get_genre_add_input(self)
        if result is None:
            return
        name, summary = result
        self.service.add_genre(name, summary)
        self._reload_genre_combo()
        self.genre_combo.setCurrentIndex(len(self.service.genres) - 1)

    def _rename_genre(self) -> None:
        genre = self._current_genre()
        if not genre:
            return
        new_name, ok = QInputDialog.getText(self, "ジャンル名変更", "新しいジャンル名:", text=genre.get("name",""))
        if ok and new_name.strip():
            idx = self.genre_combo.currentIndex()
            self.service.rename_genre(idx, new_name.strip())
            self._reload_genre_combo()
            self.genre_combo.setCurrentIndex(idx)

    def _delete_genre(self) -> None:
        genre = self._current_genre()
        if not genre:
            return
        if QMessageBox.question(self, "確認", f"ジャンル「{genre.get('name','')}」を削除しますか？") == QMessageBox.Yes:
            idx = self.genre_combo.currentIndex()
            self.service.delete_genre(idx)
            self._reload_genre_combo()
            self.genre_combo.setCurrentIndex(min(idx, self.genre_combo.count()-1))
            self._render_missions()

    # ---------- render missions ----------
    def _render_missions(self) -> None:
        self._clear_missions_ui()
        genre = self._current_genre()
        if genre is None:
            return
        for m in genre.get("missions", []):
            card = MissionCard(self.service, genre, m)
            card.changed.connect(self._after_mission_changed)
            self.mission_layout.insertWidget(self.mission_layout.count() - 1, card)

    def _after_mission_changed(self) -> None:
        # モデル順が変わる操作（上/下移動・削除）に対応して再描画
        # シグナル処理完了後に再描画する
        QTimer.singleShot(0, self._render_missions)

    # ---------- mission ops ----------
    def _add_mission(self) -> None:
        genre = self._current_genre()
        if genre is None:
            QMessageBox.warning(self, "警告", "ジャンルを作成して下さい。")
            return
        result = get_mission_add_input(self)
        if result is None:
            return
        name, summary, due_date = result
        self.service.add_mission(genre, name, summary, due_date)
        self._render_missions()
