# データモデルの定義
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Task:
    name: str
    done: bool = False
    completed_at: Optional[str] = None    # 完了日時（YYYY-MM-DD HH:MM）


@dataclass
class Mission:
    name: str
    tasks: List[Task] = field(default_factory=list)
    due_date: Optional[str] = None        # 期日
    completed_at: Optional[str] = None    # 完了日時
    
    
    # 完了しているタスクごとに1を出力して合計する
    @property
    def progress(self) -> float:
        if not self.tasks:
            return 0.0
        
        completed = sum(1 for t in self.tasks if t.done)
        return completed / len(self.tasks)
    

@dataclass
class Genre:
    name: str
    missions: List[Mission] = field(default_factory=list)