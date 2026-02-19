from __future__ import annotations
from datetime import date
from typing import TypedDict, NotRequired

# 型定義
class TaskDict(TypedDict):
    name: str
    done: bool
    completed_at: NotRequired[str | None]
    due_date: NotRequired[str | None]


class MissionDict(TypedDict):
    name: str
    tasks: list[TaskDict]
    due_date: NotRequired[str | None]
    completed_at: NotRequired[str | None]
    summary: NotRequired[str | None]


class GenreDict(TypedDict):
    name: str
    missions: list[MissionDict]
    summary: NotRequired[str | None]


def new_task(name: str) -> TaskDict:
    return {"name": name, "done": False, "completed_at": None, "due_date": None}


def new_mission(name: str) -> MissionDict:
    return {"name": name, "tasks": [], "due_date": None, "completed_at": None, "summary": None}


def new_genre(name: str, summary: str | None = None) -> GenreDict:
    return {"name": name, "missions": [], "summary": summary or None}


def mission_progress(m: MissionDict) -> float:
    # ミッション辞書から task キーを取得
    tasks: list[TaskDict] = m.get("tasks", [])
    if not isinstance(tasks, list) or not tasks:
        return 0.0
    done = sum(1 for t in tasks if isinstance(t, dict) and t.get("done", False))
    return done / len(tasks)


def count_incomplete_missions(genre: GenreDict) -> int:
    """ジャンル内の未完了ミッション数を返す（mission_progress < 1.0 のもの）"""
    missions = genre.get("missions", [])
    return sum(1 for m in missions if isinstance(m, dict) and mission_progress(m) < 1.0)


def _parse_due_date(text: str | None) -> date | None:
    """YYYY-MM-DD 形式を date に変換。無効な場合は None"""
    if not text or not text.strip():
        return None
    try:
        parts = text.strip().split("-")
        if len(parts) >= 3:
            y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
            return date(y, m, d)
    except (ValueError, TypeError):
        pass
    return None


def _days_until_due(due: date | None) -> int:
    """期限までの日数。過去は負、今日は0、未設定は大きな値（後ろへ）"""
    if due is None:
        return 99999
    return (due - date.today()).days


def mission_sort_key(m: MissionDict, idx: int) -> tuple[int, int, int]:
    """ソート用キー: 未完了かつ期限が近いものを上に。(完了済み, 日数, 元インデックス)"""
    completed = 1 if mission_progress(m) >= 1.0 else 0
    days = _days_until_due(_parse_due_date(m.get("due_date")))
    return (completed, days, idx)


def task_sort_key(t: TaskDict, idx: int) -> tuple[int, int, int]:
    """ソート用キー: 未完了かつ期限が近いものを上に。(完了済み, 日数, 元インデックス)"""
    done = 1 if t.get("done", False) else 0
    days = _days_until_due(_parse_due_date(t.get("due_date")))
    return (done, days, idx)
