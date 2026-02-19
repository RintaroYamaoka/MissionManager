from __future__ import annotations
from typing import Optional
from PySide6.QtCore import Qt, Signal, QPoint, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar,
    QFrame, QMenu, QInputDialog, QMessageBox
)
from missionmanager.models import GenreDict, MissionDict, TaskDict, mission_progress
from missionmanager.app import AppService
from missionmanager.ui.task_item import TaskItem
from missionmanager.ui.date_dialog import get_due_date
from missionmanager.ui.add_dialogs import get_task_add_input

# 1ミッションのUI
class MissionCard(QFrame):
    changed = Signal()  # タスクの変更、追加、期限変更で通知

    def __init__(self, service: AppService, genre: GenreDict, mission: MissionDict, parent: Optional[QWidget] = None) -> None:
        # コンストラクタインジェクション
        super().__init__(parent)
        self.service = service
        self.genre = genre
        self.mission = mission
        
        # フレーム形状をパネル風に設定
        self.setFrameShape(QFrame.StyledPanel)
        # Qt StyleSheety 参照用のタグを設定
        self.setObjectName("missionCard")
        
        # ミッションカード
        root = QVBoxLayout(self)                   # 縦方向のレイアウトを適用
        root.setContentsMargins(12, 12, 12, 12)    # カード内側の余白(px)
        root.setSpacing(8)                         # 子ウィジェット同士の間隔(px)

        # ヘッダーレイアウト設定
        header = QHBoxLayout()                      # ヘッダー全体は横並びレイアウト

        # タイトルボックス
        title_box = QVBoxLayout()                   
        title_box.setContentsMargins(0, 0, 0, 0)    
        title_box.setSpacing(2)                    

        # ミッション名
        self.title = QLabel(self.mission.get("name", ""))
        self.title.setCursor(Qt.PointingHandCursor)

        # メタ情報
        meta_row = QHBoxLayout()
        meta_row.setContentsMargins(0, 0, 0, 0)
        meta_row.setSpacing(8)
        
        self.due_label = QLabel("")
        self.done_label = QLabel("")
        # 期限: 青系（締切・予定を連想）、完了: 緑系（完了を連想）
        self.due_label.setStyleSheet("color:#1976D2; font-size:11px; font-weight:500;")
        self.done_label.setStyleSheet("color:#2E7D32; font-size:11px; font-weight:500;")
        self.due_label.setCursor(Qt.PointingHandCursor)
        self.done_label.setCursor(Qt.PointingHandCursor)

        meta_row.addWidget(self.due_label)
        meta_row.addSpacing(16)  # 視覚的な区切り
        meta_row.addWidget(self.done_label)
        meta_row_container = QWidget()
        meta_row_container.setLayout(meta_row)
        meta_row_container.setCursor(Qt.PointingHandCursor)

        # タイトルボックスにタイトル・メタ情報を格納
        title_box.addWidget(self.title)
        title_box.addWidget(meta_row_container)
        
        # タイトルボックスを(QVBoxLayout)をQWidgetにラップ
        title_container = QWidget()
        title_container.setLayout(title_box)
        
        # プログレスバー
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self._apply_progress()
        self.progress.setCursor(Qt.PointingHandCursor)

        # ヘッダーをクリックでタスク表示を切替
        self._body_visible = False
        self._header_widgets = (self.title, meta_row_container, self.due_label, self.done_label, self.progress)
        for w in self._header_widgets:
            w.setToolTip("クリックでタスクの表示を切替")
            w.installEventFilter(self)
        header.addWidget(title_container, 1)
        header.addWidget(self.progress, 2)
        root.addLayout(header)

        # ボディーレイアウト設定（カードを開いた時のみ表示）
        self.body = QWidget()
        body_layout = QVBoxLayout(self.body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(4)

        # 概要（カードを開いた時のみ表示）
        self.summary_label = QLabel(self.mission.get("summary") or "")
        self.summary_label.setStyleSheet("color:#888; font-size:11px;")
        self.summary_label.setWordWrap(True)
        body_layout.addWidget(self.summary_label)

        # タスク一覧の描画処理
        self.task_items: list[TaskItem] = []
        # DIされた MissionDict から tasks のリストの要素毎に処理
        for t in self.mission.get("tasks", []):
            item = TaskItem(self.service, self.mission, t)    # TaskItemインスタンスを生成(タスクUIクラス)   
            item.toggled.connect(self._on_task_changed)       # インスタンスをイベント接続
            self.task_items.append(item)                      # task_itemにインスタンスを追加
            body_layout.addWidget(item)                       # ウィジェットにタスクUIを追加

        # タスク追加ボタン
        add_row = QHBoxLayout()
        add_btn = QPushButton("タスク追加")
        add_btn.clicked.connect(self._add_task)
        add_row.addStretch(1)
        add_row.addWidget(add_btn)
        body_layout.addLayout(add_row)

        root.addWidget(self.body)
        self.body.setVisible(self._body_visible)

        # 右クリックメニュー
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._open_mission_menu)

        # UI更新処理
        self._refresh_summary_label()
        self._refresh_meta_labels()
        self._update_mission_completion()


    # 内部関数
    def _refresh_summary_label(self) -> None:
        """概要を更新（カードを開いている時のみ表示）"""
        summary = self.mission.get("summary") or ""
        self.summary_label.setText(summary)
        self.summary_label.setVisible(self._body_visible and bool(summary))

    def _refresh_meta_labels(self) -> None:
        # DIされた MissionDict から期日と完了日時データを取り出してラベルに設定
        due_txt = f"期限: {self.mission.get('due_date')}" if self.mission.get("due_date") else "期限: 未設定"
        # 完了日時は全タスク完了時のみ表示（データ不整合のガード）
        show_done = mission_progress(self.mission) >= 1.0 and self.mission.get("completed_at")
        done_txt = f"完了: {self.mission.get('completed_at')}" if show_done else "完了: -"
        self.due_label.setText(due_txt)
        self.done_label.setText(done_txt)

    
    def _update_mission_completion(self) -> None:
        """UI表示の更新のみ行う（データ更新はAppService経由）"""
        self._refresh_meta_labels()

    def eventFilter(self, obj: QWidget, event) -> bool:
        """ヘッダークリックでタスク表示を切替"""
        if obj in self._header_widgets and event.type() == event.Type.MouseButtonPress:
            if event.button() == Qt.LeftButton:
                self._body_visible = not self._body_visible
                self.body.setVisible(self._body_visible)
                self._refresh_summary_label()
                return True
        return super().eventFilter(obj, event)

    def _apply_progress(self) -> None:
        # プログレスバーを最新値に更新
        self.progress.setValue(int(mission_progress(self.mission) * 100))
        self.progress.setTextVisible(True)

    def _on_task_changed(self) -> None:
        # タスクのチェック変更時の反映処理
        self._apply_progress()
        self._update_mission_completion()
        QTimer.singleShot(0, self.changed.emit)
    # add task
    def _add_task(self) -> None:
        result = get_task_add_input(self)
        if result is None:
            return
        name, due_date = result
        self.service.add_task(self.mission, name, due_date)

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
        act_summary = menu.addAction("概要を編集")
        act_due    = menu.addAction("期限を編集")
        act_up     = menu.addAction("上へ移動")
        act_down   = menu.addAction("下へ移動")
        act_delete = menu.addAction("削除")
        chosen = menu.exec(self.mapToGlobal(pos))
        if chosen == act_delete:
            self._delete_mission()
        elif chosen == act_rename:
            self._rename_mission()
        elif chosen == act_summary:
            self._edit_summary()
        elif chosen == act_due:
            self._edit_due_date()
        elif chosen == act_up:
            self.service.move_mission_up(self.genre, self.mission)
            self.changed.emit()
        elif chosen == act_down:
            self.service.move_mission_down(self.genre, self.mission)
            self.changed.emit()

    def _edit_summary(self) -> None:
        text, ok = QInputDialog.getMultiLineText(
            self, "概要を編集", "概要：", text=self.mission.get("summary") or ""
        )
        if ok:
            self.service.set_mission_summary(self.mission, text.strip() or None)
            self._refresh_summary_label()
            self.changed.emit()

    def _rename_mission(self) -> None:
        new_name, ok = QInputDialog.getText(self, "ミッション名の変更", "ミッション：", text=self.mission.get("name", ""))
        if ok and new_name.strip():
            self.service.rename_mission(self.mission, new_name.strip())
            self.title.setText(self.mission.get("name", ""))
            self.changed.emit()

    def _edit_due_date(self) -> None:
        due_str, ok = get_due_date(self, "期限を編集", self.mission.get("due_date"))
        if not ok:
            return
        self.service.set_mission_due(self.mission, due_str)
        self._refresh_meta_labels()
        self.changed.emit()

    def _delete_mission(self) -> None:
        if QMessageBox.question(self, "確認", f"ミッション「{self.mission.get('name','')}」を削除しますか？") == QMessageBox.Yes:
            self.service.delete_mission(self.genre, self.mission)
            self.setParent(None)
            self.changed.emit()
