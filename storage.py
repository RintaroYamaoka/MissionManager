# データをJSONファイルに保存・読み込み
from __future__ import  annotations
import json
from pathlib import Path
from typing import Dict, List

from models import Genre, Mission, Task

class JsonStorage:
    def __init__(self, path: Path | str = None) -> None:
        # storage.py直下に作成
        data_dir = Path(__file__).parent / "data"
        data_dir.mkdir(exist_ok=True)

        if path is None:
            path = data_dir / "app_data.json"
        self.path = Path(path)

        if not self.path.exists():
            self._write({"genres": []})


    def _read(self) -> Dict:
        #  JSON ファイルを UTF-8 で読み込み、Python 辞書へ変換
        return json.loads(self.path.read_text(encoding="utf-8"))


    def _write(self, data: Dict) -> None:
        # 辞書を JSON 文字列化し、UTF-8 で保存
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")     

    
    def load_genres(self) -> List[Genre]:
        # JSONデータをモデルクラスのインスタンスに復元
        raw = self._read()
        genres: List[Genre] = []

        for g in raw.get("genres",[]):
            missions: List[Mission] = []
            
            for m in g.get("missions", []):
                tasks = [
                    Task(
                        name = t.get("name", ""),
                        done = t.get("done", False),
                        completed_at = t.get("completed_at"),
                    ) 
                    for t in m.get("tasks", [])
                ]
                missions.append(
                    Mission(
                        name=m.get("name", ""), 
                        tasks=tasks,
                        due_date = m.get("due_date"),
                        completed_at = m.get("completed_at"),
                    )
                )

            genres.append(Genre(name=g.get("name", ""), missions=missions))
        return genres


    def save_genres(self, genres: List[Genre]) -> None:
        data = {
            "genres": [
                {
                    "name": g.name,
                    "missions": [
                        {
                            "name": m.name,
                            "due_date": m.due_date,
                            "completed_at": m.completed_at,
                            "tasks": [
                                {
                                    "name": t.name,
                                    "done": t.done,
                                    "completed_at": t.completed_at,
                                }
                                for t in m.tasks
                            ],
                        }
                        for m in g.missions   
                    ],
                }
                for g in genres
            ]
        }
        self._write(data)
