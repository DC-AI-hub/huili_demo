"""
SalesRptByProduct Excel 解析 Pipeline（迁移自 huili/惠理基金）

数据流：
  SalesRptByProduct_*.xls → run_sales_flow_pipeline() → DataFrame (内存)

核心简化点（对比 Quartile_weekly）：
  · 单 Sheet，列位置固定（B~O），无需 header_parser / column_mapper
  · 只过滤汇总行（sub-total / total / net-off），无需 Benchmark/Peer 判断
  · 无多级合并表头
"""
from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd


# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

SUMMARY_TERMS = {"sub-total", "subtotal", "total", "net-off", "net off"}
DATE_PATTERN = re.compile(r"(\d{4}-\d{2}-\d{2})")

# 汇总行 fund_name 模式 → 合成 fund_code
SUMMARY_ROW_PATTERNS: List[tuple] = [
    ("sub-total (all funds)",  "__SUBTOTAL_ALL__"),
    ("sub-total (net-off)",   "__SUBTOTAL_NETOFF__"),
    ("total (after net-off)", "__TOTAL__"),
]

# 列名 → pandas iloc 索引
COLUMN_MAP = {
    "fund_code":               1,   # B
    "fund_name":               2,   # C
    "est_aum_usd_m":           3,   # D
    "daily_gross_sub_usd_k":   4,   # E
    "daily_gross_red_usd_k":   5,   # F
    "daily_net_flow_usd_k":    6,   # G
    # H(idx=7) 跳过（分隔列）
    "mtd_gross_sub_usd_k":     8,   # I
    "mtd_gross_red_usd_k":     9,   # J
    "mtd_net_flow_usd_k":      10,  # K
    # L(idx=11) 跳过（分隔列）
    "ytd_gross_sub_usd_k":     12,  # M
    "ytd_gross_red_usd_k":     13,  # N
    "ytd_net_flow_usd_k":      14,  # O
}

MIN_COLUMNS = 15   # 至少需要 A~O（索引 0~14）


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def _to_text(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def _to_float(value: object) -> Optional[float]:
    """
    解析数值，支持：
      · 千分位逗号：1,234.56 → 1234.56
      · 括号负数：(1234.56) → -1234.56
      · 空值 → None
    """
    text = _to_text(value)
    if text == "":
        return None
    normalized = text.replace(",", "")
    if normalized.startswith("(") and normalized.endswith(")"):
        normalized = "-" + normalized[1:-1]
    try:
        return float(normalized)
    except ValueError:
        raise ValueError(f"[S1005] invalid numeric value: {text!r}")


def _extract_report_date(df: pd.DataFrame) -> str:
    """
    在前 20 行中找包含 'Report Date: YYYY-MM-DD' 的单元格，提取日期。
    找不到则抛出 [S1003] 异常。
    """
    for row_idx in range(min(20, len(df))):
        row_values = df.iloc[row_idx].tolist()
        joined = " | ".join(_to_text(v) for v in row_values if _to_text(v) != "")
        if "Report Date:" not in joined:
            continue
        match = DATE_PATTERN.search(joined)
        if match:
            return match.group(1)
    raise ValueError(
        "[S1003] report_date not found; expected a title cell with 'Report Date: YYYY-MM-DD' in the first 20 rows"
    )


def _detect_summary_code(fund_code: str, fund_name: str) -> Optional[str]:
    """
    如果是汇总行，返回合成 fund_code（以 __ 开头）。
    否则返回 None。
    """
    name_lower = (fund_name or "").lower()
    code_lower = (fund_code or "").lower()

    # 按 fund_name 匹配已知汇总行
    for pattern, synth_code in SUMMARY_ROW_PATTERNS:
        if pattern in name_lower:
            return synth_code

    # Net-off 主行（fund_code='Net-off'）
    if code_lower in ("net-off", "net off"):
        return "__NETOFF__"

    # Net-off 子项（fund_code 为空但 fund_name 含 VPL）
    if not fund_code and fund_name and "vpl" in name_lower:
        safe = re.sub(r'[^A-Za-z0-9]', '_', fund_name).strip('_')
        return f"__NETOFF_{safe}__"

    return None


def _is_product_row(fund_code: str, fund_name: str) -> bool:
    """
    判断是否为有效产品行（过滤空行和汇总行）。
    过滤规则：
      · fund_code 为空 → 跳过
      · fund_code.lower() 在 SUMMARY_TERMS → 跳过（汇总行）
      · fund_code.lower() 包含 "total" / "sub-total" / "net-off" → 跳过
      · fund_name 为空 → 跳过
    """
    if not fund_code:
        return False
    code_lower = fund_code.lower()
    if code_lower in SUMMARY_TERMS:
        return False
    if "total" in code_lower or "sub-total" in code_lower or "net-off" in code_lower:
        return False
    if not fund_name:
        return False
    return True


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------

def run_sales_flow_pipeline(
    input_path: Path,
    output_dir: Path | None = None,
) -> Dict[str, object]:
    """
    解析 SalesRptByProduct Excel 文件，返回结构化结果字典。

    Args:
        input_path: .xls 或 .xlsx 文件路径
        output_dir: 可选，中间 CSV 输出目录（不传则只在内存中处理）

    Returns:
        {
            "etl_run_id": str,
            "report_date": str,
            "source_filename": str,
            "parsed_df": pd.DataFrame,     ← 供 sales_flow_loader 使用
            "rows_loaded": int,
            "rows_skipped_non_product": int,
            "rows_skipped_invalid_numeric": int,
        }
    """
    if not input_path.exists():
        raise FileNotFoundError(f"[S1001] input file not found: {input_path.as_posix()}")

    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)

    # ---- 读取 Excel ----
    try:
        # 优先 openpyxl（xlsx），.xls 格式回退 xlrd
        engine = None
        if input_path.suffix.lower() == ".xls":
            engine = "xlrd"
        df = pd.read_excel(input_path, header=None, dtype=object, engine=engine)
    except ImportError as exc:
        raise RuntimeError(
            "[S1002] failed to read xls: xlrd not installed. Run: pip install xlrd"
        ) from exc
    except Exception as exc:
        raise RuntimeError(
            f"[S1008] failed to open excel: {input_path.as_posix()} | {exc}"
        ) from exc

    if df.shape[1] < MIN_COLUMNS:
        raise ValueError(
            f"[S1004] column count {df.shape[1]} < {MIN_COLUMNS} (A~O required)"
        )

    # ---- 提取报告日期 ----
    report_date = _extract_report_date(df)
    source_filename = input_path.name
    etl_run_id = str(uuid.uuid4())

    records: List[Dict[str, object]] = []
    skipped_non_product = 0
    skipped_invalid_numeric = 0

    current_group = ""

    # ---- 逐行解析 ----
    for row_idx in range(len(df)):
        row = df.iloc[row_idx]
        
        group_val = _to_text(row.iloc[0])
        if group_val:
            current_group = group_val
            
        fund_code = _to_text(row.iloc[COLUMN_MAP["fund_code"]])
        fund_name = _to_text(row.iloc[COLUMN_MAP["fund_name"]])

        # 优先检测汇总行
        summary_code = _detect_summary_code(fund_code, fund_name)
        if summary_code:
            effective_code = summary_code
        elif _is_product_row(fund_code, fund_name):
            effective_code = fund_code
        else:
            skipped_non_product += 1
            continue

        try:
            record: Dict[str, object] = {
                "report_date":            report_date,
                "source_filename":        source_filename,
                "etl_run_id":             etl_run_id,
                "group_name":             current_group,
                "fund_code":              effective_code,
                "fund_name":              fund_name,
                "est_aum_usd_m":          _to_float(row.iloc[COLUMN_MAP["est_aum_usd_m"]]),
                "daily_gross_sub_usd_k":  _to_float(row.iloc[COLUMN_MAP["daily_gross_sub_usd_k"]]),
                "daily_gross_red_usd_k":  _to_float(row.iloc[COLUMN_MAP["daily_gross_red_usd_k"]]),
                "daily_net_flow_usd_k":   _to_float(row.iloc[COLUMN_MAP["daily_net_flow_usd_k"]]),
                "mtd_gross_sub_usd_k":    _to_float(row.iloc[COLUMN_MAP["mtd_gross_sub_usd_k"]]),
                "mtd_gross_red_usd_k":    _to_float(row.iloc[COLUMN_MAP["mtd_gross_red_usd_k"]]),
                "mtd_net_flow_usd_k":     _to_float(row.iloc[COLUMN_MAP["mtd_net_flow_usd_k"]]),
                "ytd_gross_sub_usd_k":    _to_float(row.iloc[COLUMN_MAP["ytd_gross_sub_usd_k"]]),
                "ytd_gross_red_usd_k":    _to_float(row.iloc[COLUMN_MAP["ytd_gross_red_usd_k"]]),
                "ytd_net_flow_usd_k":     _to_float(row.iloc[COLUMN_MAP["ytd_net_flow_usd_k"]]),
                "source_row_number":      row_idx + 1,
            }
            records.append(record)
        except ValueError:
            skipped_invalid_numeric += 1

    parsed_df = pd.DataFrame(records)

    # ---- 可选：输出中间 CSV ----
    if output_dir:
        parsed_df.to_csv(output_dir / "parsed_sales_flow.csv", index=False, encoding="utf-8-sig")
        summary = {
            "etl_run_id":                  etl_run_id,
            "report_date":                 report_date,
            "source_filename":             source_filename,
            "rows_loaded":                 int(len(parsed_df)),
            "rows_skipped_non_product":    skipped_non_product,
            "rows_skipped_invalid_numeric": skipped_invalid_numeric,
        }
        (output_dir / "sales_etl_report.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    return {
        "etl_run_id":                  etl_run_id,
        "report_date":                 report_date,
        "source_filename":             source_filename,
        "parsed_df":                   parsed_df,
        "rows_loaded":                 int(len(parsed_df)),
        "rows_skipped_non_product":    skipped_non_product,
        "rows_skipped_invalid_numeric": skipped_invalid_numeric,
    }
