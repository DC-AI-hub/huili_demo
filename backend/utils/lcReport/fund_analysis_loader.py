"""
Fund Analysis MySQL Loader（迁移自 huili/惠理基金）

幂等策略：
  lc_report_fa_meta:        (source_filename, sheet_name, calculated_on) → SELECT+UPDATE/INSERT
  lc_report_fa_performance: (meta_id, entity_name, isin, metric, period_type, start_date, end_date)
                             → SELECT+UPDATE/INSERT（不同快照数据永久共存）
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text

from .id_gen import gen_id

logger = logging.getLogger(__name__)


def _v(value: object) -> Optional[object]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    return value


def _to_int(value: object) -> Optional[int]:
    v = _v(value)
    if v is None:
        return None
    try:
        return int(float(str(v).strip()))
    except (ValueError, TypeError):
        return None


def _to_float(value: object) -> Optional[float]:
    v = _v(value)
    if v is None:
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# meta 表写入
# ---------------------------------------------------------------------------

def _upsert_meta(db: Session, report_id: int, report_type: str, row: Dict[str, Any]) -> int:
    """
    幂等写入 lc_report_fa_meta。
    幂等键：(source_filename, sheet_name, calculated_on)
    返回 meta_id（用于 performance 关联）。
    """
    existing = db.execute(
        text("""
            SELECT meta_id FROM lc_report_fa_meta
            WHERE report_id=:rid AND source_filename=:sf AND sheet_name=:sn AND calculated_on=:co
        """),
        {"rid": report_id, "sf": row["source_filename"], "sn": row["sheet_name"], "co": row["calculated_on"]},
    ).fetchone()

    if existing:
        mid = existing[0]
        db.execute(
            text("""
                UPDATE lc_report_fa_meta SET
                    report_set=:rs, snapshot_type=:st, snapshot_date=:sd,
                    calculated_date=:cd, calculated_time=:ct,
                    exported_on=:eo, currency=:cur, grouped_by=:gb,
                    investments_filter=:inv, etl_run_id=:eid, updated_at=NOW()
                WHERE meta_id=:mid
            """),
            {
                "rs":  row["report_set"],   "st": row["snapshot_type"],
                "sd":  row["snapshot_date"],"cd": row["calculated_date"],
                "ct":  row["calculated_time"], "eo": _v(row.get("exported_on")),
                "cur": row.get("currency", "US Dollar"),
                "gb":  _v(row.get("grouped_by")),
                "inv": _v(row.get("investments_filter")),
                "eid": row.get("etl_run_id"), "mid": mid,
            },
        )
        return mid

    mid = gen_id()
    db.execute(
        text("""
            INSERT INTO lc_report_fa_meta (
                meta_id, report_id, report_type, report_set, source_filename, sheet_name,
                snapshot_type, snapshot_date, calculated_on, calculated_date, calculated_time,
                exported_on, currency, grouped_by, investments_filter, etl_run_id
            ) VALUES (
                :mid, :rid, :rt, :rs, :sf, :sn,
                :st, :sd, :co, :cd, :ct,
                :eo, :cur, :gb, :inv, :eid
            )
        """),
        {
            "mid": mid, "rid": report_id, "rt": report_type,
            "rs":  row["report_set"],    "sf": row["source_filename"],
            "sn":  row["sheet_name"],    "st": row["snapshot_type"],
            "sd":  row["snapshot_date"], "co": row["calculated_on"],
            "cd":  row["calculated_date"],"ct": row["calculated_time"],
            "eo":  _v(row.get("exported_on")),
            "cur": row.get("currency", "US Dollar"),
            "gb":  _v(row.get("grouped_by")),
            "inv": _v(row.get("investments_filter")),
            "eid": row.get("etl_run_id"),
        },
    )
    return mid


# ---------------------------------------------------------------------------
# performance 表写入
# ---------------------------------------------------------------------------

def _upsert_perf(
    db: Session,
    meta_id: int,
    report_id: int,
    report_type: str,
    row: Dict[str, Any],
) -> None:
    """
    幂等写入 lc_report_fa_performance。
    幂等键：(meta_id, entity_name, isin, metric, period_type, start_date, end_date)
    注意：isin 为 NULL 时统一转空字符串参与唯一键比较。
    """
    entity_name = str(row["entity_name"])
    isin        = str(row.get("isin") or "")
    metric      = str(row["metric"])
    period_type = str(row["period_type"])
    start_date  = str(row["start_date"])
    end_date    = str(row["end_date"])

    existing = db.execute(
        text("""
            SELECT perf_id FROM lc_report_fa_performance
            WHERE report_id=:rid AND meta_id=:mid AND entity_name=:en AND isin=:isin
              AND metric=:m AND period_type=:pt AND start_date=:sd AND end_date=:ed
        """),
        {
            "rid": report_id, "mid": meta_id, "en": entity_name, "isin": isin,
            "m": metric, "pt": period_type, "sd": start_date, "ed": end_date,
        },
    ).fetchone()

    if existing:
        db.execute(
            text("""
                UPDATE lc_report_fa_performance SET
                    morningstar_rating=:mr, fund_size_date=:fsd, fund_size=:fs,
                    value=:val, peer_group_rank=:pgr, peer_group_quartile=:pgq,
                    source_row_number=:srn, source_column_name=:scn, updated_at=NOW()
                WHERE perf_id=:pid
            """),
            {
                "mr":  _v(row.get("morningstar_rating")),
                "fsd": _v(row.get("fund_size_date")),
                "fs":  _to_float(row.get("fund_size")),
                "val": _to_float(row.get("value")),
                "pgr": _to_int(row.get("peer_group_rank")),
                "pgq": _to_int(row.get("peer_group_quartile")),
                "srn": _to_int(row.get("source_row_number")),
                "scn": _v(row.get("source_column_name")),
                "pid": existing[0],
            },
        )
    else:
        db.execute(
            text("""
                INSERT INTO lc_report_fa_performance (
                    perf_id, meta_id, report_id, report_type,
                    entity_name, isin, morningstar_rating, fund_size_date, fund_size,
                    period_type, metric, value, peer_group_rank, peer_group_quartile,
                    start_date, end_date, source_row_number, source_column_name
                ) VALUES (
                    :pid, :mid, :rid, :rt,
                    :en, :isin, :mr, :fsd, :fs,
                    :pt, :m, :val, :pgr, :pgq,
                    :sd, :ed, :srn, :scn
                )
            """),
            {
                "pid": gen_id(), "mid": meta_id, "rid": report_id, "rt": report_type,
                "en":  entity_name, "isin": isin,
                "mr":  _v(row.get("morningstar_rating")),
                "fsd": _v(row.get("fund_size_date")),
                "fs":  _to_float(row.get("fund_size")),
                "pt":  period_type, "m": metric,
                "val": _to_float(row.get("value")),
                "pgr": _to_int(row.get("peer_group_rank")),
                "pgq": _to_int(row.get("peer_group_quartile")),
                "sd":  start_date, "ed": end_date,
                "srn": _to_int(row.get("source_row_number")),
                "scn": _v(row.get("source_column_name")),
            },
        )


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------

def load_fa_to_mysql(
    db: Session,
    meta_df: pd.DataFrame,
    perf_df: pd.DataFrame,
    report_id: int,
    report_type: str,
    fund_map_df: pd.DataFrame | None = None,
) -> Dict[str, int]:
    """
    幂等写入 lc_report_fa_meta 和 lc_report_fa_performance。
    若提供 fund_map_df，同时 UPSERT lc_fund_code_map（fund_code → entity_name 映射）。

    Returns:
        {
            "fa_meta_rows": int,
            "fa_perf_rows_changed": int,
            "fa_perf_input_rows": int,
            "fund_map_rows": int,
        }
    """
    if meta_df.empty:
        logger.warning("[fa_loader] meta_df is empty, nothing to load.")
        return {"fa_meta_rows": 0, "fa_perf_rows_changed": 0, "fa_perf_input_rows": 0}

    # 开启事务：先清理该报告的旧数据，防止重复上传时有脏数据残留
    db.execute(text("DELETE FROM lc_report_fa_performance WHERE report_id=:rid"), {"rid": report_id})
    db.execute(text("DELETE FROM lc_report_fa_meta WHERE report_id=:rid"), {"rid": report_id})

    # 1. 写入元数据，建立 (source_filename, sheet_name, calculated_on) → meta_id 映射
    meta_lookup: Dict[tuple, int] = {}
    for record in meta_df.to_dict("records"):
        mid = _upsert_meta(db, report_id, report_type, record)
        meta_lookup[(record["source_filename"], record["sheet_name"], record["calculated_on"])] = mid

    # 2. 写入表现明细
    perf_changed = 0
    for row in perf_df.to_dict("records"):
        key = (row["source_filename"], row["sheet_name"], row["calculated_on"])
        meta_id = meta_lookup.get(key)
        if meta_id is None:
            logger.warning(f"[fa_loader] no meta_id for key={key}, skipping row.")
            continue
        _upsert_perf(db, meta_id, report_id, report_type, row)
        perf_changed += 1

    db.commit()
    logger.info(
        f"[fa_loader] report_id={report_id} done: "
        f"meta={len(meta_df)}, perf_changed={perf_changed}"
    )

    # 写入 fund_code 映射表（如果提供）
    fund_map_rows = 0
    if fund_map_df is not None and not fund_map_df.empty:
        for rec in fund_map_df.to_dict("records"):
            db.execute(
                text("""
                    INSERT INTO lc_fund_code_map (fund_code, entity_name, isin)
                    VALUES (:fc, :en, :isin)
                    ON DUPLICATE KEY UPDATE
                        entity_name = VALUES(entity_name),
                        isin        = VALUES(isin),
                        updated_at  = NOW()
                """),
                {
                    "fc":   str(rec["fund_code"]),
                    "en":   str(rec["entity_name"]),
                    "isin": str(rec.get("isin") or ""),
                },
            )
            fund_map_rows += 1
        db.commit()
        logger.info(f"[fa_loader] lc_fund_code_map upserted: {fund_map_rows} rows")

    return {
        "fa_meta_rows":        len(meta_df),
        "fa_perf_rows_changed": perf_changed,
        "fa_perf_input_rows":  int(len(perf_df)),
        "fund_map_rows":       fund_map_rows,
    }
