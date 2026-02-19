from __future__ import annotations
from typing import List, Optional
from datetime import datetime
from missionmanager.models import GenreDict, MissionDict, TaskDict, new_genre, new_mission, new_task, mission_progress
from missionmanager.storage import StorageProtocol


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


class AppService:
    # UIに依存しないビジネスロジック層
    # 全データは List[GenreDict] データオブジェクトで管理
    # 変更時に必ず _save() を呼んで永続化

    def __init__(self, storage: StorageProtocol) -> None:
        # コンストラクタインジェクション
        self._storage = storage   
        self.genres: List[GenreDict] = self._storage.load_genres()    # データオブジェクト読み込み


    def _save(self) -> None:
        # DIされた_storage.save_genres 経由で現在のデータオブジェクトを保存
        self._storage.save_genres(self.genres)


    # ジャンルの処理
    # データオブジェクトを操作して保存
    def list_genres(self) -> List[GenreDict]:
        return self.genres

    def add_genre(self, name: str, summary: Optional[str] = None) -> None:
        self.genres.append(new_genre(name, summary))
        self._save()

    def rename_genre(self, index: int, new_name: str) -> None:
        if index < 0 or index >= len(self.genres):
            raise IndexError(f"ジャンルインデックス {index} が範囲外です")
        self.genres[index]["name"] = new_name
        self._save()

    def set_genre_summary(self, index: int, summary: Optional[str]) -> None:
        if index < 0 or index >= len(self.genres):
            raise IndexError(f"ジャンルインデックス {index} が範囲外です")
        self.genres[index]["summary"] = summary or None
        self._save()

    def delete_genre(self, index: int) -> None:
        if index < 0 or index >= len(self.genres):
            raise IndexError(f"ジャンルインデックス {index} が範囲外です")
        del self.genres[index]
        self._save()

    def move_genre_up(self, index: int) -> None:
        if index < 0 or index >= len(self.genres):
            raise IndexError(f"ジャンルインデックス {index} が範囲外です")
        if index <= 0:
            return
        self.genres[index-1], self.genres[index] = self.genres[index], self.genres[index-1]
        self._save()

    def move_genre_down(self, index: int) -> None:
        if index < 0 or index >= len(self.genres):
            raise IndexError(f"ジャンルインデックス {index} が範囲外です")
        if index >= len(self.genres) - 1:
            return
        self.genres[index+1], self.genres[index] = self.genres[index], self.genres[index+1]
        self._save()


    # ミッションの処理
    def add_mission(self, g: GenreDict, name: str, summary: Optional[str] = None, due_date: Optional[str] = None) -> None:
        m = new_mission(name)
        if summary:
            m["summary"] = summary
        if due_date:
            m["due_date"] = due_date
        g.setdefault("missions", []).append(m)
        self._save()

    def find_mission_index(self, g: GenreDict, m: MissionDict) -> int:
        missions = g.get("missions", [])
        try:
            return missions.index(m)
        except ValueError:
            raise ValueError("指定されたミッションが見つかりません")

    def rename_mission(self, m: MissionDict, new_name: str) -> None:
        m["name"] = new_name
        self._save()

    def set_mission_due(self, m: MissionDict, due_text: Optional[str]) -> None:
        m["due_date"] = due_text or None
        self._save()

    def set_mission_summary(self, m: MissionDict, summary: Optional[str]) -> None:
        m["summary"] = summary or None
        self._save()

    def delete_mission(self, g: GenreDict, m: MissionDict) -> None:
        missions = g.get("missions", [])
        try:
            missions.remove(m)
        except ValueError:
            raise ValueError("指定されたミッションが見つかりません")
        self._save()

    def move_mission_up(self, g: GenreDict, m: MissionDict) -> None:
        missions = g.get("missions", [])
        try:
            idx = missions.index(m)
        except ValueError:
            raise ValueError("指定されたミッションが見つかりません")
        if idx <= 0:
            return
        missions[idx-1], missions[idx] = missions[idx], missions[idx-1]
        self._save()

    def move_mission_down(self, g: GenreDict, m: MissionDict) -> None:
        missions = g.get("missions", [])
        try:
            idx = missions.index(m)
        except ValueError:
            raise ValueError("指定されたミッションが見つかりません")
        if idx < 0 or idx >= len(missions) - 1:
            return
        missions[idx+1], missions[idx] = missions[idx], missions[idx+1]
        self._save()


    # タスクの処理
    def _sync_mission_completion(self, m: MissionDict) -> None:
        """タスクの完了状況に応じてミッションの completed_at を同期"""
        if mission_progress(m) >= 1.0:
            m["completed_at"] = now_str()
        else:
            m["completed_at"] = None

    def add_task(self, m: MissionDict, name: str, due_date: Optional[str] = None) -> None:
        t = new_task(name)
        if due_date:
            t["due_date"] = due_date
        m.setdefault("tasks", []).append(t)
        self._sync_mission_completion(m)
        self._save()

    def rename_task(self, t: TaskDict, new_name: str) -> None:
        t["name"] = new_name
        self._save()

    def set_task_due(self, t: TaskDict, due_text: Optional[str]) -> None:
        t["due_date"] = due_text or None
        self._save()

    def delete_task(self, m: MissionDict, t: TaskDict) -> None:
        tasks = m.get("tasks", [])
        try:
            tasks.remove(t)
        except ValueError:
            raise ValueError("指定されたタスクが見つかりません")
        self._sync_mission_completion(m)
        self._save()

    def move_task_up(self, m: MissionDict, t: TaskDict) -> None:
        tasks = m.get("tasks", [])
        try:
            idx = tasks.index(t)
        except ValueError:
            raise ValueError("指定されたタスクが見つかりません")
        if idx <= 0:
            return
        tasks[idx-1], tasks[idx] = tasks[idx], tasks[idx-1]
        self._save()

    def move_task_down(self, m: MissionDict, t: TaskDict) -> None:
        tasks = m.get("tasks", [])
        try:
            idx = tasks.index(t)
        except ValueError:
            raise ValueError("指定されたタスクが見つかりません")
        if idx < 0 or idx >= len(tasks) - 1:
            return
        tasks[idx+1], tasks[idx] = tasks[idx], tasks[idx+1]
        self._save()

    def toggle_task_done(self, m: MissionDict, t: TaskDict, checked: bool) -> None:
        t["done"] = checked
        t["completed_at"] = now_str() if checked else None
        self._sync_mission_completion(m)
        self._save()
