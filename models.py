from __future__ import annotations
from typing import TypedDict, Optional, List


class TaskDict(TypedDict, total=False):
    name: str
    done: bool
    completed_at: Optional[str]  # "YYYY-MM-DD HH:MM" or None


class MissionDict(TypedDict, total=False):
    name: str
    tasks: List[TaskDict]
    due_date: Optional[str]      # "YYYY-MM-DD" or None
    completed_at: Optional[str]  # "YYYY-MM-DD HH:MM" or None


class GenreDict(TypedDict, total=False):
    name: str
    missions: List[MissionDict]


def new_task(name: str) -> TaskDict:
    return {"name": name, "done": False, "completed_at": None}


def new_mission(name: str) -> MissionDict:
    return {"name": name, "tasks": [], "due_date": None, "completed_at": None}


def new_genre(name: str) -> GenreDict:
    return {"name": name, "missions": []}


def mission_progress(m: MissionDict) -> float:
    tasks = m.get("tasks", [])
    if not tasks:
        return 0.0
    done = sum(1 for t in tasks if t.get("done", False))
    return done / len(tasks)
