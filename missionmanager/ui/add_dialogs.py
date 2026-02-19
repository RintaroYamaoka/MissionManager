"""追加用の複数項目入力ダイアログ"""
from __future__ import annotations
from typing import Optional
from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QPlainTextEdit,
    QPushButton, QDateEdit, QHBoxLayout, QDialogButtonBox, QWidget, QMessageBox,
)

# 期限未設定を示す sentinel（この年以下は「未設定」として扱う）
DATE_SENTINEL_YEAR = 1900


def _create_date_row() -> tuple[QDateEdit, QHBoxLayout]:
    """期限選択用の QDateEdit と行レイアウトを生成"""
    sentinel = QDate(DATE_SENTINEL_YEAR, 1, 1)
    date_edit = QDateEdit()
    date_edit.setCalendarPopup(True)
    date_edit.setDisplayFormat("yyyy-MM-dd")
    date_edit.setMinimumDate(sentinel)
    date_edit.setSpecialValueText("未設定")
    date_edit.setDate(sentinel)
    row = QHBoxLayout()
    row.addWidget(date_edit)
    clear_btn = QPushButton("解除")
    clear_btn.clicked.connect(lambda: date_edit.setDate(sentinel))
    row.addWidget(clear_btn)
    return date_edit, row


def _get_due_date_from_edit(date_edit: QDateEdit) -> Optional[str]:
    """QDateEdit から期限文字列を取得（未設定なら None）"""
    qd = date_edit.date()
    return qd.toString("yyyy-MM-dd") if qd.isValid() and qd.year() > DATE_SENTINEL_YEAR else None


def get_genre_add_input(parent: Optional[QWidget]) -> Optional[tuple[str, Optional[str]]]:
    """ジャンル追加ダイアログ。戻り値: (名前, 概要) または None"""
    dialog = QDialog(parent)
    dialog.setWindowTitle("ジャンル追加")

    layout = QFormLayout(dialog)

    name_edit = QLineEdit()
    name_edit.setPlaceholderText("例: 開発")
    layout.addRow("名前:", name_edit)

    summary_edit = QPlainTextEdit()
    summary_edit.setPlaceholderText("任意の概要・説明を入力")
    summary_edit.setMaximumHeight(80)
    layout.addRow("概要:", summary_edit)

    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)

    def on_accept() -> None:
        if not name_edit.text().strip():
            QMessageBox.warning(dialog, "入力エラー", "名前を入力してください。")
            return
        dialog.accept()

    buttons.accepted.connect(on_accept)
    buttons.rejected.connect(dialog.reject)
    layout.addRow(buttons)

    if dialog.exec() == QDialog.DialogCode.Accepted:
        name = name_edit.text().strip()
        summary = summary_edit.toPlainText().strip() or None
        return name, summary
    return None


def get_mission_add_input(parent: Optional[QWidget]) -> Optional[tuple[str, Optional[str], Optional[str]]]:
    """ミッション追加ダイアログ。戻り値: (名前, 概要, 期限) または None"""
    dialog = QDialog(parent)
    dialog.setWindowTitle("ミッション追加")

    layout = QFormLayout(dialog)

    name_edit = QLineEdit()
    name_edit.setPlaceholderText("例: ポートフォリオ作成")
    layout.addRow("名前:", name_edit)

    summary_edit = QPlainTextEdit()
    summary_edit.setPlaceholderText("任意の概要を入力")
    summary_edit.setMaximumHeight(80)
    layout.addRow("概要:", summary_edit)

    date_edit, date_row = _create_date_row()
    layout.addRow("期限:", date_row)

    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)

    def on_accept() -> None:
        if not name_edit.text().strip():
            QMessageBox.warning(dialog, "入力エラー", "名前を入力してください。")
            return
        dialog.accept()

    buttons.accepted.connect(on_accept)
    buttons.rejected.connect(dialog.reject)
    layout.addRow(buttons)

    if dialog.exec() == QDialog.DialogCode.Accepted:
        name = name_edit.text().strip()
        summary = summary_edit.toPlainText().strip() or None
        due_date = _get_due_date_from_edit(date_edit)
        return name, summary, due_date
    return None


def get_task_add_input(parent: Optional[QWidget]) -> Optional[tuple[str, Optional[str]]]:
    """タスク追加ダイアログ。戻り値: (名前, 期限) または None"""
    dialog = QDialog(parent)
    dialog.setWindowTitle("タスク追加")

    layout = QFormLayout(dialog)

    name_edit = QLineEdit()
    name_edit.setPlaceholderText("例: API設計")
    layout.addRow("名前:", name_edit)

    date_edit, date_row = _create_date_row()
    layout.addRow("期限:", date_row)

    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)

    def on_accept() -> None:
        if not name_edit.text().strip():
            QMessageBox.warning(dialog, "入力エラー", "名前を入力してください。")
            return
        dialog.accept()

    buttons.accepted.connect(on_accept)
    buttons.rejected.connect(dialog.reject)
    layout.addRow(buttons)

    if dialog.exec() == QDialog.DialogCode.Accepted:
        name = name_edit.text().strip()
        due_date = _get_due_date_from_edit(date_edit)
        return name, due_date
    return None
