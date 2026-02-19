from __future__ import annotations
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
