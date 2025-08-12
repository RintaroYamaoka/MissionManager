# データモデルの定義
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

@dataclass
class Task:
    name: str
    done: bool = False


@dataclass
class Mission:
    name: str
    tasks: List[Task] = field(default_factory=list)

    @property
    def progress(self) -> float:
        if not self.tasks:
            return 0.0
        # 完了しているタスクごとに1を出力して合計する
        completed = sum(1 for t in self.tasks if t.done)
        return completed / len(self.tasks)
    

@dataclass
class Genre:
    name: str
    missions: List[Mission] = field(default_factory=list)