"""期限入力用のカレンダーダイアログ"""
from __future__ import annotations
from typing import Optional
from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QDateEdit, QLabel,
    QDialogButtonBox,
)


def _parse_date(text: Optional[str]) -> Optional[QDate]:
    """YYYY-MM-DD 形式の文字列を QDate に変換"""
    if not text or not text.strip():
        return None
    try:
        parts = text.strip().split("-")
        if len(parts) == 3:
            y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
            qd = QDate(y, m, d)
            if qd.isValid():
                return qd
    except (ValueError, TypeError):
        pass
    return None


def get_due_date(parent: Optional[QDialog], title: str, current: Optional[str]) -> tuple[Optional[str], bool]:
    """
    カレンダープルダウンで期限を選択するダイアログを表示する。
    戻り値: (選択した日付の YYYY-MM-DD 文字列、または None, OKが押されたか)
    """
    dialog = QDialog(parent)
    dialog.setWindowTitle(title)

    layout = QVBoxLayout(dialog)

    label = QLabel("期限を選択：")
    layout.addWidget(label)

    date_edit = QDateEdit()
    date_edit.setCalendarPopup(True)  # カレンダープルダウンを有効化
    date_edit.setDisplayFormat("yyyy-MM-dd")

    parsed = _parse_date(current)
    if parsed:
        date_edit.setDate(parsed)
    else:
        date_edit.setDate(QDate.currentDate())

    layout.addWidget(date_edit)

    btn_layout = QHBoxLayout()
    clear_btn = QPushButton("解除")
    clear_btn.setToolTip("期限を解除します")
    clear_btn.clicked.connect(lambda: _clear_and_accept(dialog, date_edit))

    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)

    btn_layout.addWidget(clear_btn)
    btn_layout.addStretch()
    btn_layout.addWidget(buttons)
    layout.addLayout(btn_layout)

    if dialog.exec() == QDialog.DialogCode.Accepted:
        result = dialog.property("cleared_date")
        if result is True:
            return None, True
        return date_edit.date().toString("yyyy-MM-dd"), True
    return None, False


def _clear_and_accept(dialog: QDialog, _date_edit: QDateEdit) -> None:
    """解除ボタン: 期限なしで確定"""
    dialog.setProperty("cleared_date", True)
    dialog.accept()
