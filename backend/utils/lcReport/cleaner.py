"""
数据清洗器 — 从原 huili/惠理基金/src/etl_excel/cleaner.py 迁移
处理占位符标准化和数值类型强制转换。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

import pandas as pd

from .config import EtlConfig


@dataclass
class ConversionError:
    column: str
    row_number: int
    raw_value: object
    reason: str


def standardize_placeholders(df: pd.DataFrame, config: EtlConfig) -> pd.DataFrame:
    """将占位符（如空字符串、'-'）统一替换为 NA"""
    tokens = list(config.placeholder_tokens)
    return df.replace(tokens, pd.NA)


def _is_numeric_target(column_name: str) -> bool:
    """判断列是否应该被强制转为数值类型"""
    lowered = column_name.lower()
    keys = ("return", "rank", "quartile", "count", "fund size")
    return any(k in lowered for k in keys)


def apply_type_rules(df: pd.DataFrame, config: EtlConfig) -> Tuple[pd.DataFrame, List[ConversionError]]:
    """
    对 DataFrame 应用类型规则：
    - 数值目标列：强制转为 float，记录转换失败行
    - 其他列：转为 string 类型
    """
    conversion_errors: List[ConversionError] = []
    protected = {
        "group_category",
        "row_source_sheet",
        "row_number",
    }

    for column in df.columns:
        if column in protected:
            continue
        if _is_numeric_target(column):
            raw_series = df[column]
            converted = pd.to_numeric(raw_series, errors="coerce")
            mask_failed = raw_series.notna() & converted.isna()
            for row_idx in df.index[mask_failed]:
                conversion_errors.append(
                    ConversionError(
                        column=column,
                        row_number=int(df.loc[row_idx, "row_number"]),
                        raw_value=df.loc[row_idx, column],
                        reason="numeric_conversion_failed",
                    )
                )
            df[column] = converted
        else:
            df[column] = df[column].astype("string")

    return df, conversion_errors


def summarize_conversion_errors(
    conversion_errors: Iterable[ConversionError], max_samples: int
) -> Dict[str, object]:
    errors = list(conversion_errors)
    return {
        "count": len(errors),
        "samples": [
            {
                "column": e.column,
                "row_number": e.row_number,
                "raw_value": str(e.raw_value),
                "reason": e.reason,
            }
            for e in errors[:max_samples]
        ],
    }
