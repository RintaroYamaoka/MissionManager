from __future__ import annotations
from typing import Callable, Optional
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtWidgets import QWidget, QHBoxLayout, QCheckBox, QLabel, QMenu, QInputDialog, QMessageBox
from models import TaskDict, MissionDict
from app import AppService


class TaskItem(QWidget):
    toggled = Signal()

    def __init__(
        self,
        service: AppService,
        mission: MissionDict,
        task: TaskDict,
        parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)
        self.service = service
        self.mission = mission
        self.task = task

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.check = QCheckBox(task.get("name", ""))
        self.check.setChecked(bool(task.get("done", False)))
        self.check.toggled.connect(self._on_toggled)
        layout.addWidget(self.check, 1)

        self.time_label = QLabel("")
        self.time_label.setStyleSheet("color:#888; font-size:11px;")
        layout.addWidget(self.time_label)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._open_menu)

        self._refresh_time_label()

    def _refresh_time_label(self) -> None:
        self.time_label.setText(self.task.get("completed_at") or "")

    def _on_toggled(self, checked: bool) -> None:
        self.service.toggle_task_done(self.mission, self.task, checked)
        self._refresh_time_label()
        self.toggled.emit()

    # context menu
    def _open_menu(self, pos: QPoint) -> None:
        menu = QMenu(self)
        act_rename = menu.addAction("名前変更")
        act_up = menu.addAction("上へ移動")
        act_down = menu.addAction("下へ移動")
        act_delete = menu.addAction("削除")
        chosen = menu.exec(self.mapToGlobal(pos))

        if chosen == act_delete:
            self._delete_task()
        elif chosen == act_rename:
            self._rename_task()
        elif chosen == act_up:
            self.service.move_task_up(self.mission, self.task)
            self.parentWidget().parentWidget().parentWidget().parentWidget().parentWidget().update()  # no-op
            self.toggled.emit()
        elif chosen == act_down:
            self.service.move_task_down(self.mission, self.task)
            self.parentWidget().parentWidget().parentWidget().parentWidget().parentWidget().update()
            self.toggled.emit()

    def _rename_task(self) -> None:
        new_name, ok = QInputDialog.getText(self, "タスク名の変更", "タスク:", text=self.task.get("name", ""))
        if ok and new_name.strip():
            self.service.rename_task(self.task, new_name.strip())
            self.check.setText(self.task.get("name", ""))

    def _delete_task(self) -> None:
        if QMessageBox.question(self, "確認", f"タスク「{self.task.get('name','')}」を削除しますか?") == QMessageBox.Yes:
            self.service.delete_task(self.mission, self.task)
            self.setParent(None)
