"""
数据质量校验器 — 从原 huili/惠理基金/src/etl_excel/validator.py 迁移
对解析后的 DataFrame 执行规则校验，输出质量问题列表。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import pandas as pd

from .config import EtlConfig


@dataclass
class ValidationIssue:
    rule_id: str
    severity: str   # "error" | "warning"
    message: str
    sheet_name: str


def _find_column_like(df: pd.DataFrame, token: str) -> str | None:
    token_lower = token.lower()
    for column in df.columns:
        if token_lower in column.lower():
            return column
    return None


def _derive_row_type_from_first_cell(first_cell: object) -> str:
    text = str(first_cell).strip() if first_cell is not None else ""
    if text.startswith("Benchmark"):
        return "Benchmark"
    if text == "Peer Group Average":
        return "Peer_Avg"
    if text == "Peer Group Count":
        return "Peer_Count"
    return "Fund_Data"


def validate_sheet(df: pd.DataFrame, sheet_name: str, config: EtlConfig) -> List[ValidationIssue]:
    """
    执行以下数据质量校验：
    1. 分组数量不低于阈值
    2. 基金行数量不低于阈值
    3. 必要列存在且缺失率不超标
    4. 非分组行的 group_category 缺失率检查
    """
    issues: List[ValidationIssue] = []

    group_count = int(df["group_category"].dropna().nunique()) if "group_category" in df else 0
    first_col = _find_column_like(df, "Group/Investment")
    if first_col is not None:
        row_type_series = df[first_col].map(_derive_row_type_from_first_cell)
        fund_count = int((row_type_series == "Fund_Data").sum())
    else:
        fund_count = 0

    if group_count < config.quality_min_group_per_sheet:
        issues.append(ValidationIssue(
            rule_id="dq_group_count",
            severity="error",
            message=f"group_count={group_count} below threshold={config.quality_min_group_per_sheet}",
            sheet_name=sheet_name,
        ))

    if fund_count < config.quality_min_fund_rows_per_sheet:
        issues.append(ValidationIssue(
            rule_id="dq_fund_count",
            severity="error",
            message=f"fund_count={fund_count} below threshold={config.quality_min_fund_rows_per_sheet}",
            sheet_name=sheet_name,
        ))

    for required_token in config.required_columns:
        col = _find_column_like(df, required_token)
        if col is None:
            issues.append(ValidationIssue(
                rule_id="dq_missing_required_column",
                severity="error",
                message=f"required token '{required_token}' not found in columns",
                sheet_name=sheet_name,
            ))
            continue
        missing_ratio = float(df[col].isna().mean()) if len(df) > 0 else 1.0
        if missing_ratio > 0.95:
            issues.append(ValidationIssue(
                rule_id="dq_required_column_missing_ratio",
                severity="warning",
                message=f"column={col} missing_ratio={missing_ratio:.4f}",
                sheet_name=sheet_name,
            ))

    if "group_category" in df and first_col is not None and len(df) > 0:
        row_type_series = df[first_col].map(_derive_row_type_from_first_cell)
        non_group = df[row_type_series.isin(["Fund_Data", "Benchmark", "Peer_Avg", "Peer_Count"])]
        if len(non_group) > 0:
            missing_ratio = float(non_group["group_category"].isna().mean())
            if missing_ratio > 0.01:
                issues.append(ValidationIssue(
                    rule_id="dq_group_missing_for_non_group_rows",
                    severity="error",
                    message=f"group_category missing_ratio={missing_ratio:.4f} for non-group rows",
                    sheet_name=sheet_name,
                ))

    return issues


def summarize_issues(issues: List[ValidationIssue]) -> Dict[str, object]:
    return {
        "total": len(issues),
        "errors": sum(1 for i in issues if i.severity == "error"),
        "warnings": sum(1 for i in issues if i.severity == "warning"),
        "details": [i.__dict__ for i in issues],
    }
