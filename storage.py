from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, List, Any
from models import GenreDict, MissionDict, TaskDict


class JsonStorage:
    """
    辞書のままJSON保存・読み込み。
    旧データ（欠損キーなど）も既定値で補完して読み込む。
    """
    def __init__(self, path: Path | str | None = None) -> None:
        data_dir = Path(__file__).parent / "data"
        data_dir.mkdir(exist_ok=True)
        if path is None:
            path = data_dir / "app_data.json"
        self.path = Path(path)
        if not self.path.exists():
            self._write({"genres": []})

    def _read(self) -> Dict[str, Any]:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, data: Dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def load_genres(self) -> List[GenreDict]:
        raw = self._read()
        genres_raw = raw.get("genres", [])
        genres: list[GenreDict] = []
        for g in genres_raw:
            missions: list[MissionDict] = []
            for m in g.get("missions", []):
                tasks: list[TaskDict] = []
                for t in m.get("tasks", []):
                    tasks.append({
                        "name": t.get("name", ""),
                        "done": bool(t.get("done", False)),
                        "completed_at": t.get("completed_at"),
                    })
                missions.append({
                    "name": m.get("name", ""),
                    "tasks": tasks,
                    "due_date": m.get("due_date"),
                    "completed_at": m.get("completed_at"),
                })
            genres.append({
                "name": g.get("name", ""),
                "missions": missions,
            })
        return genres

    def save_genres(self, genres: List[GenreDict]) -> None:
        data = {"genres": genres}
        self._write(data)
