"""
数据行解析器 — 从原 huili/惠理基金/src/etl_excel/row_parser.py 迁移
将 Excel 数据行对齐到打平后的列名结构，识别分组标题行并跟踪当前分组。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence

from .config import EtlConfig


def _as_text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


@dataclass
class ParsedRow:
    payload: Dict[str, object]


def is_benchmark_row(first_cell: str) -> bool:
    return first_cell.startswith("Benchmark")


def is_peer_avg_row(first_cell: str) -> bool:
    return first_cell == "Peer Group Average"


def is_peer_count_row(first_cell: str) -> bool:
    return first_cell == "Peer Group Count"


def _find_col_idx_like(flat_columns: Sequence[str], token: str) -> int | None:
    token_lower = token.lower()
    for idx, col in enumerate(flat_columns):
        if token_lower in col.lower():
            return idx
    return None


def is_group_title_row(
    row_values: Sequence[object],
    first_cell: str,
    flat_columns: Sequence[str],
    config: EtlConfig,
    prev_row_was_blank: bool = False,
) -> bool:
    """
    判断当前行是否为分组标题行（而非基金数据行）。
    分组标题特征：
      1. 前一行为完全空白的分隔行（prev_row_was_blank=True）
      2. 首列有文字
      3. 非首列几乎都是空的（<5% 填充率）
    优化说明：增加 prev_row_was_blank 判断，防止数据全为空的实体行
    （如 "Hang Seng Index TR (Daily)"）被误判为分组标题。
    """
    if not first_cell:
        return False
    # 必须前一行为完全空白行（分组标题前必有空行分隔符）
    if not prev_row_was_blank:
        return False
    if any(keyword in first_cell for keyword in config.group_blacklist_keywords):
        return False

    non_first = row_values[1:]
    if not non_first:
        return True
    filled = sum(1 for v in non_first if _as_text(v))
    fill_ratio = filled / len(non_first)
    if fill_ratio >= config.non_first_col_fill_ratio_threshold:
        return False

    # 防御规则：真正的分组标题不应含有基金身份标识字段（ISIN / Morningstar Category）
    for token in ("isin", "morningstar category"):
        col_idx = _find_col_idx_like(flat_columns, token)
        if col_idx is None or col_idx >= len(row_values):
            continue
        if _as_text(row_values[col_idx]):
            return False
    return True


def detect_row_type(first_cell: str) -> str:
    if is_benchmark_row(first_cell):
        return "Benchmark"
    if is_peer_avg_row(first_cell):
        return "Peer_Avg"
    if is_peer_count_row(first_cell):
        return "Peer_Count"
    return "Fund_Data"


def parse_rows(
    data_rows: Sequence[Sequence[object]],
    flat_columns: Sequence[str],
    sheet_name: str,
    start_row_idx: int,
    config: EtlConfig,
) -> List[ParsedRow]:
    """
    解析数据区域所有行：
    - 跳过分组标题行（记录为 current_group）
    - 跳过全空行（并记录为 prev_row_was_blank 供下一行判断分组）
    - 将每行数据对齐到 flat_columns，追加 group_category / row_source_sheet / row_number
    """
    parsed: List[ParsedRow] = []
    current_group = ""
    prev_row_was_blank = False

    for local_idx, row in enumerate(data_rows):
        absolute_row_idx = start_row_idx + local_idx + 1
        row_values = list(row) + [None] * (len(flat_columns) - len(row))
        row_values = row_values[:len(flat_columns)]
        first_cell = _as_text(row_values[0] if row_values else "")

        # 检查是否为全空行
        all_empty = not any(_as_text(v) for v in row_values)
        if all_empty:
            prev_row_was_blank = True
            continue

        if is_group_title_row(row_values, first_cell, flat_columns,
                              config, prev_row_was_blank):
            current_group = first_cell
            prev_row_was_blank = False
            continue

        prev_row_was_blank = False

        payload = {flat_columns[i]: row_values[i] for i in range(len(flat_columns))}
        payload["group_category"] = current_group
        payload["row_source_sheet"] = sheet_name
        payload["row_number"] = absolute_row_idx
        parsed.append(ParsedRow(payload=payload))
    return parsed
