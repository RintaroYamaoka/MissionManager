from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, List, Any
from models import GenreDict, MissionDict, TaskDict


class JsonStorage:
    # データ層
    # ジャンルのリストをトップオブジェクトとしてデータ管理
    # 辞書のままJSON保存・読み込み。
    # 旧データ（欠損キーなど）も既定値で補完して読み込む。
    
    def __init__(self, path: Path | str | None = None) -> None:
        # storage.py の親ディレクトリを取得し、直下に data ディレクトリを作成
        # 既に存在する場合もエラーにしない
        data_dir = Path(__file__).parent / "data"
        data_dir.mkdir(exist_ok=True) 

        # path 指定がない場合はデフォルトパスを設定
        if path is None:
            path = data_dir / "app_data.json"
        self.path = Path(path)

        # 保存先ファイルが存在しない場合、空ジャンルリストを書き込みエラー回避
        if not self.path.exists():
            self._write({"genres": []})


    def _read(self) -> Dict[str, Any]:
        # path JSONファイルをテキストとして読み込み、辞書に変換して返す
        return json.loads(self.path.read_text(encoding="utf-8"))


    def _write(self, data: Dict[str, Any]) -> None:
        # 辞書 data をJSON文字列に変換し、path ファイルに書き込み
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


    def load_genres(self) -> List[GenreDict]:
        raw = self._read()
        genres_raw = raw.get("genres", [])    # genres キーのリストを取得
        genres: List[GenreDict] = []          # トップオブジェクト

        for g in genres_raw:
            missions: List[MissionDict] = []
            for m in g.get("missions", []):
                tasks: List[TaskDict] = []
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
