"""
Sheet 元数据解析 — 从原 huili/惠理基金/src/etl_excel/meta_extract.py 迁移
提取 Excel 左上角 Currency / Grouped by / Calculated on / Exported on 等信息。
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, Sequence


def _as_text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_currency(raw_currency: str) -> str:
    mapping = {
        "US Dollar": "USD",
        "Hong Kong Dollar": "HKD",
        "Chinese Yuan": "CNY",
        "Renminbi": "CNY",
    }
    return mapping.get(raw_currency, raw_currency)


def _parse_datetime(raw_value: str) -> str:
    value = raw_value.strip()
    for fmt in ("%m/%d/%Y %I:%M:%S %p", "%m/%d/%Y %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt).isoformat()
        except ValueError:
            continue
    return value


def parse_sheet_metadata(rows: Sequence[Sequence[object]], sheet_name: str, input_path: Path) -> Dict[str, str]:
    """
    解析 Sheet 顶部元数据信息。
    
    返回字段：
        report_set      - 文件名去扩展名
        source_filename - 原始文件名
        sheet_name      - Sheet 名
        report_name     - 报表名（首行文本）
        currency        - 货币代码
        grouped_by      - 分组方式
        calculated_on   - 计算日期
        exported_on     - 导出日期
    """
    report_name = _as_text(rows[0][0]) if rows and rows[0] else sheet_name
    metadata: Dict[str, str] = {
        "report_set": input_path.stem,
        "source_filename": input_path.name,
        "sheet_name": sheet_name,
        "report_name": report_name or sheet_name,
        "currency": "",
        "grouped_by": "",
        "calculated_on": "",
        "exported_on": "",
    }

    for row in rows[:8]:
        if not row:
            continue
        first_cell = _as_text(row[0])
        if first_cell.startswith("Currency:"):
            metadata["currency"] = _normalize_currency(first_cell.split(":", 1)[1].strip())
        elif first_cell.startswith("Grouped by:"):
            metadata["grouped_by"] = first_cell.split(":", 1)[1].strip()
        elif first_cell.startswith("Calculated on:"):
            metadata["calculated_on"] = _parse_datetime(first_cell.split(":", 1)[1].strip())
        elif first_cell.startswith("Exported on:"):
            metadata["exported_on"] = _parse_datetime(first_cell.split(":", 1)[1].strip())

    return metadata
