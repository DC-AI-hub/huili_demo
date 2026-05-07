"""
Fund Analysis Excel 解析 Pipeline（迁移自 huili/惠理基金）

数据流：
  Fund Analysis_*.xlsx → run_fund_analysis_pipeline() → (meta_df, perf_df)

核心特点：
  · 同一 Sheet 可有多个历史快照块（多个 "Calculated on:" 行），按顺序标记 t0/t1/t2
  · 表头固定 4 行：header-3=周期 / header-2=起始日期 / header-1=结束日期 / header=指标
  · Benchmark 行保留（isin 置空），Peer Group 汇总行跳过
  · 公式辅助列（Wkly Rtn / Previous Wk Ranking / Better/Worse）跳过
"""
from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
from openpyxl import load_workbook


# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

CALCULATED_PREFIX = "Calculated on:"
EXPORTED_PREFIX   = "Exported on:"
PERIOD_PATTERN    = re.compile(r"^(YTD|\d+[my]|SI|Since Inception|\(inception\))$", re.IGNORECASE)
SUMMARY_NAMES     = {"peer group average", "peer group count", "peer group median"}
FORMULA_LABELS    = {"wkly rtn", "previous wk ranking", "better/worse", "same", "better", "worse"}


# ---------------------------------------------------------------------------
# 数据类
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PeriodMetric:
    period_type:        str
    start_date:         str
    end_date:           str
    metric:             str
    value_col_idx:      int
    rank_col_idx:       Optional[int]
    quartile_col_idx:   Optional[int]
    source_column_name: str


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def _to_text(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def _to_float(value: object) -> Optional[float]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = _to_text(value).replace(",", "")
    if text == "":
        return None
    if text.startswith("(") and text.endswith(")"):
        text = "-" + text[1:-1]
    try:
        return float(text)
    except ValueError as exc:
        raise ValueError(f"[F1006] invalid numeric value: {value!r}") from exc


def _to_int(value: object) -> Optional[int]:
    num = _to_float(value)
    return None if num is None else int(num)


def _to_iso_date(value: object) -> Optional[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = _to_text(value)
    if not text:
        return None
    for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError(f"[F1005] invalid date value: {text!r}")


def _parse_datetime_text(text: str, rule_id: str) -> datetime:
    """解析 'Calculated on: MM/DD/YYYY HH:MM:SS AM/PM' 等格式"""
    value = text.split(":", 1)[1].strip() if ":" in text else text.strip()
    for fmt in ("%m/%d/%Y %I:%M:%S %p", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise ValueError(f"[{rule_id}] invalid datetime value: {text!r}")


def _extract_meta_line(rows: List[List[object]], start_idx: int, end_idx: int, prefix: str) -> str:
    """在 [start_idx, end_idx) 行范围内找以 prefix 开头的文本"""
    for row_idx in range(max(0, start_idx), min(end_idx, max(0, start_idx) + 10)):
        for value in rows[row_idx]:
            t = _to_text(value)
            if t.startswith(prefix):
                return t
    return ""


def _after_prefix(text: str, prefix: str) -> str:
    if text.startswith(prefix):
        return text[len(prefix):].strip()
    return ""


def _left_fill(values: List[object]) -> List[object]:
    """将空单元格填充为左侧最近非空值（处理合并单元格）"""
    filled: List[object] = []
    last: object = None
    for v in values:
        if _to_text(v) != "":
            last = v
        filled.append(last)
    return filled


def _normalize_period(value: object) -> Optional[str]:
    text = _to_text(value).replace(" ", "")
    if not text:
        return None
    if text.lower() == "sinceinception":
        return "Since Inception"
    return text if PERIOD_PATTERN.match(text) else None


def _metric_from_header(value: object) -> Optional[str]:
    text = _to_text(value).replace("\n", " ").lower()
    if "return" not in text:
        return None
    if "cumulative" in text:
        return "return_cumulative"
    if "annualized" in text:
        return "return_ann"
    return None


# ---------------------------------------------------------------------------
# 核心解析逻辑
# ---------------------------------------------------------------------------

def _find_calculated_rows(rows: List[List[object]]) -> List[int]:
    return [
        i for i, row in enumerate(rows)
        if any(_to_text(v).startswith(CALCULATED_PREFIX) for v in row)
    ]


def _find_header_row(rows: List[List[object]], start_idx: int, end_idx: int) -> int:
    for i in range(start_idx, end_idx):
        first = _to_text(rows[i][0]) if rows[i] else ""
        if first == "Group/Investment":
            return i
    raise ValueError(f"[F1003] Group/Investment header row not found near row {start_idx + 1}")


def _build_period_metrics(rows: List[List[object]], header_idx: int) -> List[PeriodMetric]:
    if header_idx < 3:
        raise ValueError(f"[F1004] insufficient period header rows before row {header_idx + 1}")

    period_row = _left_fill(rows[header_idx - 3])
    start_row  = _left_fill(rows[header_idx - 2])
    end_row    = _left_fill(rows[header_idx - 1])
    metric_row = rows[header_idx]

    groups: Dict[Tuple[str, str, str], Dict[str, object]] = {}
    for col_idx, header_value in enumerate(metric_row):
        header_text  = _to_text(header_value)
        header_lower = header_text.replace("\n", " ").lower()
        if header_lower in FORMULA_LABELS:
            continue

        period_type = _normalize_period(period_row[col_idx] if col_idx < len(period_row) else None)
        if period_type is None:
            continue

        start_date = _to_iso_date(start_row[col_idx] if col_idx < len(start_row) else None)
        end_date   = _to_iso_date(end_row[col_idx]   if col_idx < len(end_row)   else None)
        if start_date is None or end_date is None:
            continue

        key = (period_type, start_date, end_date)
        groups.setdefault(key, {"returns": [], "rank": None, "quartile": None})

        metric = _metric_from_header(header_value)
        if metric:
            groups[key]["returns"].append((metric, col_idx, header_text))
        elif "peer group rank" in header_lower:
            groups[key]["rank"] = col_idx
        elif "peer group quartile" in header_lower:
            groups[key]["quartile"] = col_idx

    metrics: List[PeriodMetric] = []
    for (period_type, start_date, end_date), payload in groups.items():
        for metric, col_idx, source_name in payload["returns"]:
            metrics.append(PeriodMetric(
                period_type=period_type,
                start_date=start_date,
                end_date=end_date,
                metric=metric,
                value_col_idx=int(col_idx),
                rank_col_idx=int(payload["rank"]) if payload["rank"] is not None else None,
                quartile_col_idx=int(payload["quartile"]) if payload["quartile"] is not None else None,
                source_column_name=f"{period_type}_{start_date}_{end_date}_{source_name}",
            ))

    if not metrics:
        raise ValueError(f"[F1007] no return metric columns found near row {header_idx + 1}")
    return metrics


def _is_data_row(row: List[object]) -> bool:
    entity_name = _to_text(row[0] if row else "")
    if not entity_name:
        return False
    if entity_name.lower() in SUMMARY_NAMES:
        return False
    if entity_name.startswith("Benchmark"):
        return True  # Benchmark 行保留（与 Quartile_weekly 不同）
    return _to_text(row[1] if len(row) > 1 else "") != ""


def _parse_sheet(
    rows: List[List[object]],
    sheet_name: str,
    input_path: Path,
    report_set: str,
    etl_run_id: str,
) -> Tuple[List[Dict], List[Dict]]:
    meta_records: List[Dict] = []
    perf_records: List[Dict] = []

    calculated_rows = _find_calculated_rows(rows)
    if not calculated_rows:
        raise ValueError(f"[F1002] no 'Calculated on:' block found in sheet: {sheet_name!r}")

    block_bounds = [*calculated_rows, len(rows)]

    for block_idx, start_idx in enumerate(calculated_rows):
        end_idx = block_bounds[block_idx + 1]

        calculated_line = _extract_meta_line(rows, start_idx, end_idx, CALCULATED_PREFIX)
        calculated_on   = _parse_datetime_text(calculated_line, "F1008")

        exported_line = _extract_meta_line(rows, start_idx, end_idx, EXPORTED_PREFIX)
        exported_on   = _parse_datetime_text(exported_line, "F1009") if exported_line else None

        currency    = _after_prefix(_extract_meta_line(rows, start_idx - 4, end_idx, "Currency:"),    "Currency:")
        grouped_by  = _after_prefix(_extract_meta_line(rows, start_idx - 4, end_idx, "Grouped by:"),  "Grouped by:")
        investments = _after_prefix(_extract_meta_line(rows, start_idx, end_idx, "Investments:"),     "Investments:")

        header_idx = _find_header_row(rows, start_idx, end_idx)
        metrics    = _build_period_metrics(rows, header_idx)

        meta = {
            "report_set":         report_set,
            "source_filename":    input_path.name,
            "sheet_name":         sheet_name,
            "snapshot_type":      f"t{block_idx}",
            "snapshot_date":      calculated_on.date().isoformat(),
            "calculated_on":      calculated_on.isoformat(sep=" "),
            "calculated_date":    calculated_on.date().isoformat(),
            "calculated_time":    calculated_on.time().replace(microsecond=0).isoformat(),
            "exported_on":        exported_on.isoformat(sep=" ") if exported_on else "",
            "currency":           currency or "US Dollar",
            "grouped_by":         grouped_by,
            "investments_filter": investments,
            "etl_run_id":         etl_run_id,
        }
        meta_records.append(meta)

        for row_idx in range(header_idx + 1, end_idx):
            row = rows[row_idx]
            if not _is_data_row(row):
                continue
            entity_name = _to_text(row[0])
            isin = "" if entity_name.startswith("Benchmark") else _to_text(row[1] if len(row) > 1 else "")

            for pm in metrics:
                value = _to_float(row[pm.value_col_idx] if pm.value_col_idx < len(row) else None)
                if value is None:
                    continue
                perf_records.append({
                    **meta,
                    "entity_name":         entity_name,
                    "isin":                isin,
                    "morningstar_rating":  _to_text(row[2] if len(row) > 2 else ""),
                    "fund_size_date":      _to_iso_date(row[3] if len(row) > 3 else None) or "",
                    "fund_size":           _to_float(row[4] if len(row) > 4 else None),
                    "period_type":         pm.period_type,
                    "metric":              pm.metric,
                    "value":               value,
                    "peer_group_rank":     _to_int(row[pm.rank_col_idx]) if pm.rank_col_idx is not None and pm.rank_col_idx < len(row) else None,
                    "peer_group_quartile": _to_int(row[pm.quartile_col_idx]) if pm.quartile_col_idx is not None and pm.quartile_col_idx < len(row) else None,
                    "start_date":          pm.start_date,
                    "end_date":            pm.end_date,
                    "source_row_number":   row_idx + 1,
                    "source_column_name":  pm.source_column_name,
                })

    return meta_records, perf_records


# ---------------------------------------------------------------------------
# fund_code 映射解析（AUM with monthly return 格式）
#   特征：header 行中 col B（索引 1）= "Group/Investment"（而非 col A）
#   格式：fund_row: [fund_code, entity_name, ISIN, ...]
#         bm_row:   [None,      bm_name,     None, ...]
#         diff_row: [None,      'Diff',      None, ...]
# ---------------------------------------------------------------------------

def _parse_fund_code_map_sheets(workbook) -> List[Dict]:
    """
    扫描 workbook 中所有 Sheet，识别 'AUM with monthly return' 格式：
      - header 行的 col B（索引 1）= 'Group/Investment'
      - fund 行: col A = fund_code（非空短字符串），col B = entity_name，col C = ISIN
    返回 [{fund_code, entity_name, isin}, ...] 列表，去重。
    """
    records: Dict[str, Dict] = {}  # fund_code → record（自动去重）

    for sheet_name in workbook.sheetnames:
        ws = workbook[sheet_name]
        rows = [list(r) for r in ws.iter_rows(values_only=True)]

        # 找 header 行：col B == 'Group/Investment'
        header_idx = None
        for i, row in enumerate(rows):
            if len(row) > 1 and _to_text(row[1]) == "Group/Investment":
                header_idx = i
                break
        if header_idx is None:
            continue

        for row in rows[header_idx + 1:]:
            if not row or len(row) < 3:
                continue
            fund_code   = _to_text(row[0])
            entity_name = _to_text(row[1])
            isin        = _to_text(row[2])

            # fund 行：col A 非空、col C 有 ISIN（纯字母数字）、不是 'Diff'
            if (
                fund_code
                and entity_name
                and isin
                and fund_code.lower() != "diff"
                and entity_name.lower() not in {"diff", "group/investment"}
            ):
                records[fund_code] = {
                    "fund_code":   fund_code,
                    "entity_name": entity_name,
                    "isin":        isin,
                }

    return list(records.values())


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------

def run_fund_analysis_pipeline(
    input_path: Path,
    output_dir: Optional[Path] = None,
) -> Dict[str, object]:
    """
    解析 Fund Analysis Excel，返回结构化结果字典。

    Returns:
        {
            "etl_run_id": str,
            "report_set": str,
            "source_filename": str,
            "meta_df": pd.DataFrame,      ← 供 fund_analysis_loader 使用
            "perf_df": pd.DataFrame,      ← 供 fund_analysis_loader 使用
            "sheet_count": int,
            "meta_rows": int,
            "performance_rows": int,
        }
    """
    if not input_path.exists():
        raise FileNotFoundError(f"[F1001] input file not found: {input_path.as_posix()}")

    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)

    etl_run_id = str(uuid.uuid4())
    report_set = input_path.stem

    workbook = load_workbook(input_path, read_only=True, data_only=True)
    all_meta: List[Dict] = []
    all_perf: List[Dict] = []
    fund_map_records: List[Dict] = []

    try:
        for sheet_name in workbook.sheetnames:
            ws = workbook[sheet_name]
            rows = [list(row) for row in ws.iter_rows(values_only=True)]
            try:
                meta_records, perf_records = _parse_sheet(rows, sheet_name, input_path, report_set, etl_run_id)
                all_meta.extend(meta_records)
                all_perf.extend(perf_records)
            except ValueError:
                # 非 Morningstar AUM 格式的 Sheet 跳过（如 AUM with monthly return）
                pass

        # 额外扫描 AUM with monthly return 格式，提取 fund_code 映射
        workbook.close()
        workbook = load_workbook(input_path, read_only=True, data_only=True)
        fund_map_records = _parse_fund_code_map_sheets(workbook)
    finally:
        workbook.close()

    meta_df     = pd.DataFrame(all_meta)
    perf_df     = pd.DataFrame(all_perf)
    fund_map_df = pd.DataFrame(fund_map_records) if fund_map_records else pd.DataFrame(columns=["fund_code","entity_name","isin"])

    if output_dir:
        meta_df.to_csv(output_dir / "fund_analysis_meta.csv", index=False, encoding="utf-8-sig")
        perf_df.to_csv(output_dir / "fund_analysis_performance.csv", index=False, encoding="utf-8-sig")
        fund_map_df.to_csv(output_dir / "fund_code_map.csv", index=False, encoding="utf-8-sig")
        summary = {
            "etl_run_id":       etl_run_id,
            "report_set":       report_set,
            "source_filename":  input_path.name,
            "sheet_count":      int(meta_df["sheet_name"].nunique()) if not meta_df.empty else 0,
            "meta_rows":        int(len(meta_df)),
            "performance_rows": int(len(perf_df)),
            "fund_map_rows":    int(len(fund_map_df)),
        }
        (output_dir / "fund_analysis_etl_report.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    return {
        "etl_run_id":       etl_run_id,
        "report_set":       report_set,
        "source_filename":  input_path.name,
        "meta_df":          meta_df,
        "perf_df":          perf_df,
        "fund_map_df":      fund_map_df,
        "sheet_count":      int(meta_df["sheet_name"].nunique()) if not meta_df.empty else 0,
        "meta_rows":        int(len(meta_df)),
        "performance_rows": int(len(perf_df)),
        "fund_map_rows":    int(len(fund_map_df)),
    }
