"""追加用の複数項目入力ダイアログ"""
from __future__ import annotations
from typing import Optional
from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QPlainTextEdit,
    QPushButton, QDateEdit, QHBoxLayout, QDialogButtonBox, QWidget,
)


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
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addRow(buttons)

    if dialog.exec() == QDialog.DialogCode.Accepted:
        name = name_edit.text().strip()
        if not name:
            return None
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

    _SENTINEL = QDate(1900, 1, 1)
    date_edit = QDateEdit()
    date_edit.setCalendarPopup(True)
    date_edit.setDisplayFormat("yyyy-MM-dd")
    date_edit.setMinimumDate(_SENTINEL)
    date_edit.setSpecialValueText("未設定")
    date_edit.setDate(_SENTINEL)
    date_row = QHBoxLayout()
    date_row.addWidget(date_edit)
    clear_btn = QPushButton("解除")
    clear_btn.clicked.connect(lambda: date_edit.setDate(_SENTINEL))
    date_row.addWidget(clear_btn)
    layout.addRow("期限:", date_row)

    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addRow(buttons)

    if dialog.exec() == QDialog.DialogCode.Accepted:
        name = name_edit.text().strip()
        if not name:
            return None
        summary = summary_edit.toPlainText().strip() or None
        qd = date_edit.date()
        due_date = qd.toString("yyyy-MM-dd") if qd.isValid() and qd.year() > 1900 else None
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

    _SENTINEL = QDate(1900, 1, 1)
    date_edit = QDateEdit()
    date_edit.setCalendarPopup(True)
    date_edit.setDisplayFormat("yyyy-MM-dd")
    date_edit.setMinimumDate(_SENTINEL)
    date_edit.setSpecialValueText("未設定")
    date_edit.setDate(_SENTINEL)
    date_row = QHBoxLayout()
    date_row.addWidget(date_edit)
    clear_btn = QPushButton("解除")
    clear_btn.clicked.connect(lambda: date_edit.setDate(_SENTINEL))
    date_row.addWidget(clear_btn)
    layout.addRow("期限:", date_row)

    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addRow(buttons)

    if dialog.exec() == QDialog.DialogCode.Accepted:
        name = name_edit.text().strip()
        if not name:
            return None
        qd = date_edit.date()
        due_date = qd.toString("yyyy-MM-dd") if qd.isValid() and qd.year() > 1900 else None
        return name, due_date
    return None
