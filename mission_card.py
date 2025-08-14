from __future__ import annotations
from typing import Optional
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar,
    QFrame, QMenu, QInputDialog, QMessageBox
)
from models import GenreDict, MissionDict, TaskDict, mission_progress
from app import AppService
from task_item import TaskItem


class MissionCard(QFrame):
    changed = Signal()  # タスクの変更、追加、期限変更で通知

    def __init__(
        self,
        service: AppService,
        genre: GenreDict,
        mission: MissionDict,
        parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)
        self.service = service
        self.genre = genre
        self.mission = mission

        self.setFrameShape(QFrame.StyledPanel)
        self.setObjectName("missionCard")

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        # header
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setContentsMargins(0, 0, 0, 0)
        title_box.setSpacing(2)

        self.title = QLabel(self.mission.get("name", ""))

        meta_row = QHBoxLayout()
        meta_row.setContentsMargins(0, 0, 0, 0)
        meta_row.setSpacing(8)

        self.due_label = QLabel("")
        self.done_label = QLabel("")
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

        # body: task list
        self.body = QWidget()
        body_layout = QVBoxLayout(self.body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(4)

        self.task_items: list[TaskItem] = []
        for t in self.mission.get("tasks", []):
            item = TaskItem(self.service, self.mission, t)
            item.toggled.connect(self._on_task_changed)
            self.task_items.append(item)
            body_layout.addWidget(item)

        add_row = QHBoxLayout()
        add_btn = QPushButton("タスク追加")
        add_btn.clicked.connect(self._add_task)
        add_row.addStretch(1)
        add_row.addWidget(add_btn)
        body_layout.addLayout(add_row)

        root.addWidget(self.body)
        self.body.setVisible(False)

        # right-click on mission card
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._open_mission_menu)

        self._refresh_meta_labels()
        self._update_mission_completion(force=True)

    # labels
    def _refresh_meta_labels(self) -> None:
        due_txt = f"期限: {self.mission.get('due_date')}" if self.mission.get("due_date") else "期限: -"
        done_txt = f"完了: {self.mission.get('completed_at')}" if self.mission.get("completed_at") else "完了: -"
        self.due_label.setText(due_txt)
        self.done_label.setText(done_txt)

    # state helpers
    def _update_mission_completion(self, force: bool = False) -> None:
        if mission_progress(self.mission) >= 1.0:
            # completed_at は AppService.toggle_task_done でも設定するが、
            # 手動で100%になった直後の見た目反映用にここでも設定
            if force or not self.mission.get("completed_at"):
                from datetime import datetime
                self.mission["completed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        else:
            if self.mission.get("completed_at") is not None:
                self.mission["completed_at"] = None
        self._refresh_meta_labels()

    def _toggle_body(self, checked: bool) -> None:
        self.body.setVisible(checked)

    def _apply_progress(self) -> None:
        self.progress.setValue(int(mission_progress(self.mission) * 100))
        self.progress.setTextVisible(True)

    def _on_task_changed(self) -> None:
        self._apply_progress()
        self._update_mission_completion()
        self.changed.emit()

    # add task
    def _add_task(self) -> None:
        from PySide6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "タスク追加", "タスクを入力:")
        if not ok or not name.strip():
            return
        self.service.add_task(self.mission, name.strip())

        item = TaskItem(self.service, self.mission, self.mission["tasks"][-1])
        item.toggled.connect(self._on_task_changed)
        self.task_items.append(item)
        self.body.layout().insertWidget(len(self.task_items) - 1, item)
        self._apply_progress()
        self._update_mission_completion()
        self.changed.emit()

    # context menu for mission
    def _open_mission_menu(self, pos: QPoint) -> None:
        menu = QMenu(self)
        act_rename = menu.addAction("名前変更")
        act_due    = menu.addAction("期限を編集")
        act_up     = menu.addAction("上へ移動")
        act_down   = menu.addAction("下へ移動")
        act_delete = menu.addAction("削除")
        chosen = menu.exec(self.mapToGlobal(pos))
        if chosen == act_delete:
            self._delete_mission()
        elif chosen == act_rename:
            self._rename_mission()
        elif chosen == act_due:
            self._edit_due_date()
        elif chosen == act_up:
            self.service.move_mission_up(self.genre, self.mission)
            self.changed.emit()
        elif chosen == act_down:
            self.service.move_mission_down(self.genre, self.mission)
            self.changed.emit()

    def _rename_mission(self) -> None:
        from PySide6.QtWidgets import QInputDialog
        new_name, ok = QInputDialog.getText(self, "ミッション名の変更", "ミッション：", text=self.mission.get("name", ""))
        if ok and new_name.strip():
            self.service.rename_mission(self.mission, new_name.strip())
            self.title.setText(self.mission.get("name", ""))
            self.changed.emit()

    def _edit_due_date(self) -> None:
        from PySide6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(
            self,
            "期限を編集",
            "期限（YYYY-MM-DD、空欄可）：",
            text=self.mission.get("due_date") or "",
        )
        if not ok:
            return
        self.service.set_mission_due(self.mission, text.strip() or None)
        self._refresh_meta_labels()
        self.changed.emit()

    def _delete_mission(self) -> None:
        if QMessageBox.question(self, "確認", f"ミッション「{self.mission.get('name','')}」を削除しますか？") == QMessageBox.Yes:
            self.service.delete_mission(self.genre, self.mission)
            self.setParent(None)
            self.changed.emit()
            