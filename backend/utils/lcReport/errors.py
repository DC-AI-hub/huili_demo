"""
自定义异常类 — 从原 huili/惠理基金/src/etl_excel/errors.py 迁移
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class EtlErrorContext:
    sheet_name: str
    row_idx: Optional[int]
    col_idx: Optional[int]
    rule_id: str

    def as_text(self) -> str:
        return (
            f"sheet_name={self.sheet_name}, row_idx={self.row_idx}, "
            f"col_idx={self.col_idx}, rule_id={self.rule_id}"
        )


class EtlRuleError(RuntimeError):
    def __init__(self, message: str, context: EtlErrorContext) -> None:
        super().__init__(f"{message} | {context.as_text()}")
        self.context = context
