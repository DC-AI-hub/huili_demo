"""
主键 ID 生成器
规则：YYYYMMDDHHmmss（14位）+ 3位递增序号 = 17位 BIGINT
线程安全，同一进程内全局序号不重复。
"""
from __future__ import annotations

import threading
from datetime import datetime

_lock = threading.Lock()
_last_ts: str = ""
_counter: int = 0


def gen_id() -> int:
    """
    生成全局唯一 17 位主键 ID。
    格式：YYYYMMDDHHmmss + 000~999（3位序号）
    示例：20260430093012001
    """
    global _last_ts, _counter

    with _lock:
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        if ts == _last_ts:
            _counter += 1
        else:
            _last_ts = ts
            _counter = 1
        seq = _counter             # 不取模：BIGINT 最多 19 位，单秒超 99999 次极不可能
        return int(f"{ts}{seq:03d}")
