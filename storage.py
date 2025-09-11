from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from models import GenreDict

class JsonStorage:
    
    def __init__(self, path: Path | str | None = None) -> None:
        # storage.py の親ディレクトリを取得し、直下に data フォルダを結合した Path を作成
        data_dir: Path = Path(__file__).parent / "data"
        # ディレクトリを作成
        data_dir.mkdir(exist_ok=True)

        if path is None:
            path = data_dir / "app_data.json"

        self.path: Path = Path(path)
        
        # 保存先ファイルが存在しない場合の処理
        if not self.path.exists():
            self._write({"genres": []})


    def _read(self) -> dict[str, Any]:
        return json.loads(self.path.read_text(encoding="utf-8"))
    

    def _write(self, data: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


    def load_genres(self) -> list[GenreDict]:
        raw: dict[str, Any] = self._read()
        return raw.get("genres", [])


    def save_genres(self, genres: list[GenreDict]) -> None:
        data: dict[str, Any] = {"genres": genres}
        self._write(data)    