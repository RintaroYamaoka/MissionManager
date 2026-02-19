from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from missionmanager.models import GenreDict


class StorageError(Exception):
    """ストレージ操作に関するエラー"""
    pass


class JsonStorage:
    
    def __init__(self, path: Path | str | None = None) -> None:
        # プロジェクトルート（missionmanager の親）の data ディレクトリを使用
        project_root = Path(__file__).parent.parent
        data_dir: Path = project_root / "data"
        # ディレクトリを作成
        try:
            data_dir.mkdir(exist_ok=True)
        except OSError as e:
            raise StorageError(f"データディレクトリの作成に失敗しました: {e}")

        if path is None:
            path = data_dir / "app_data.json"

        self.path: Path = Path(path)
        
        # 保存先ファイルが存在しない場合の処理
        if not self.path.exists():
            try:
                self._write({"genres": []})
            except StorageError:
                # 初期化時のエラーは再発生させる
                raise

    def _read(self) -> dict[str, Any]:
        try:
            content = self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            # ファイルが存在しない場合は空のデータを返す
            return {"genres": []}
        except OSError as e:
            raise StorageError(f"ファイルの読み込みに失敗しました ({self.path}): {e}")
        
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise StorageError(f"JSONの解析に失敗しました ({self.path}): {e}")

    def _write(self, data: dict[str, Any]) -> None:
        try:
            json_str = json.dumps(data, ensure_ascii=False, indent=2)
            self.path.write_text(json_str, encoding="utf-8")
        except OSError as e:
            raise StorageError(f"ファイルの書き込みに失敗しました ({self.path}): {e}")
        except (TypeError, ValueError) as e:
            raise StorageError(f"データのシリアライズに失敗しました: {e}")

    def load_genres(self) -> list[GenreDict]:
        try:
            raw: dict[str, Any] = self._read()
            genres = raw.get("genres", [])
            # データ構造の基本的な検証
            if not isinstance(genres, list):
                raise StorageError("データ形式が不正です: 'genres'はリストである必要があります")
            return genres
        except StorageError:
            raise
        except Exception as e:
            raise StorageError(f"ジャンルの読み込みに失敗しました: {e}")

    def save_genres(self, genres: list[GenreDict]) -> None:
        if not isinstance(genres, list):
            raise StorageError("genresはリストである必要があります")
        try:
            data: dict[str, Any] = {"genres": genres}
            self._write(data)
        except StorageError:
            raise
        except Exception as e:
            raise StorageError(f"ジャンルの保存に失敗しました: {e}")    
