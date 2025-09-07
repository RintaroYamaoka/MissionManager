from __future__ import annotations

# 型エイリアス
TaskDict = dict[str, str | bool | None]
MissionDict = dict[str, str | list[TaskDict] | None]
GenreDict = dict[str, str | list[MissionDict]]


def new_task(name: str) -> TaskDict:
    return {"name": name, "done": False, "completed_at": None}


def new_mission(name: str) -> MissionDict:
    return {"name": name, "tasks": [], "due_date": None, "completed_at": None}


def new_genre(name: str) -> GenreDict:
    return {"name": name, "missions": []}


def mission_progress(m: MissionDict) -> float:
    # ミッション辞書から task キーを取得
    tasks: list[TaskDict] = m.get("tasks", [])
    if not isinstance(tasks, list) or not tasks:
        return 0.0
    done = sum(1 for t in tasks if isinstance(t, dict) and t.get("done", False)) 
    return done / len(tasks)  