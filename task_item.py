from __future__ import annotations
from typing import Optional
from PySide6.QtCore import Qt, Signal, QPoint, QTimer
from PySide6.QtWidgets import QWidget, QHBoxLayout, QCheckBox, QLabel, QMenu, QInputDialog, QMessageBox
from models import TaskDict, MissionDict
from app import AppService

# 1タスクのUI
class TaskItem(QWidget):
    toggled = Signal()

    def __init__(self, service: AppService, mission: MissionDict, task: TaskDict, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        # コンストラクタインジェクション
        self.service = service
        self.mission = mission
        self.task = task

        # タスクUIのレイアウト設定
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # チェックボックス
        self.check = QCheckBox(task.get("name", ""))
        self.check.setChecked(bool(task.get("done", False)))
        self.check.toggled.connect(self._on_toggled)    # イベント接続
        layout.addWidget(self.check, 1)

        # 完了日時ラベル
        self.time_label = QLabel("")
        self.time_label.setStyleSheet("color:#888; font-size:11px;")
        self._refresh_time_label()    # 完了日時データを反映
        layout.addWidget(self.time_label)

        # 右クリックメニュー
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._open_menu)    # イベント接続

    
    def _refresh_time_label(self) -> None:
        # DIされたタスクの完了日時データを取得
        self.time_label.setText(self.task.get("completed_at") or "")

    
    def _on_toggled(self, checked: bool) -> None:
        # DIされた service.toggle_task_done 経由でタスクの完了状態を更新
        # UI上の完了日時ラベルに反映
        self.service.toggle_task_done(self.mission, self.task, checked)
        self._refresh_time_label()
        # 自分が破棄されないようにイベントループ後に外部に通知
        QTimer.singleShot(0, self.toggled.emit)
           

    def _open_menu(self, pos: QPoint) -> None:
        # メニューインスタンスを作成してメニューを登録
        menu = QMenu(self)
        act_rename = menu.addAction("名前変更")
        act_up = menu.addAction("上へ移動")
        act_down = menu.addAction("下へ移動")
        act_delete = menu.addAction("削除")

        # posをウィジェット内座標から画面座標へ変換してその位置にメニューを表示
        # 選択された QAction を返す
        chosen = menu.exec(self.mapToGlobal(pos))
        
        # 選択されたメニューに対応する処理へ
        if chosen == act_delete:
            self._delete_task()
        elif chosen == act_rename:
            self._rename_task()
        # DIされたメソッドを呼び出し、状態変化を外部へ通知（MissionCardが再描画を処理）
        elif chosen == act_up:
            self.service.move_task_up(self.mission, self.task)
            # シグナルでMissionCardに再描画を通知
            QTimer.singleShot(0, self.toggled.emit)
        elif chosen == act_down:
            self.service.move_task_down(self.mission, self.task)
            # シグナルでMissionCardに再描画を通知
            QTimer.singleShot(0, self.toggled.emit)

    def _rename_task(self) -> None:
        # 名前入力ダイアログの表示
        new_name, ok = QInputDialog.getText(self, "タスク名の変更", "タスク:", text=self.task.get("name", ""))
        if ok and new_name.strip():
            # DIされたメソッド経由でタスク名を変更し、UIを更新
            self.service.rename_task(self.task, new_name.strip())
            self.check.setText(self.task.get("name", ""))

    def _delete_task(self) -> None:
        if QMessageBox.question(self, "確認", f"タスク「{self.task.get('name','')}」を削除しますか?") == QMessageBox.Yes:
            self.service.delete_task(self.mission, self.task)
            self.setParent(None)
