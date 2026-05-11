"""
SalesRptByProduct MySQL Loader（迁移自 huili/惠理基金）

将 sales_flow_pipeline 输出的 DataFrame 幂等写入 lc_report_sales_flow 表。
幂等键：(report_date, source_filename, fund_code)
"""
from __future__ import annotations

import logging
from typing import Any, Dict

import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text

from .id_gen import gen_id

logger = logging.getLogger(__name__)


REQUIRED_COLUMNS = {
    "report_date", "source_filename", "fund_code", "fund_name",
    "est_aum_usd_m",
    "daily_gross_sub_usd_k", "daily_gross_red_usd_k", "daily_net_flow_usd_k",
    "mtd_gross_sub_usd_k",   "mtd_gross_red_usd_k",   "mtd_net_flow_usd_k",
    "ytd_gross_sub_usd_k",   "ytd_gross_red_usd_k",   "ytd_net_flow_usd_k",
}


def _to_float(value: object) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def load_sales_flow_to_mysql(
    db: Session,
    parsed_df: pd.DataFrame,
    report_id: int,
    report_type: str,
    etl_run_id: str,
) -> Dict[str, int]:
    """
    幂等写入 lc_report_sales_flow。

    Args:
        db:          SQLAlchemy Session
        parsed_df:   run_sales_flow_pipeline 返回的 parsed_df
        report_id:   对应的 lc_report.report_id
        report_type: 报告类型（固定为 "SalesRptByProduct"）
        etl_run_id:  本次 ETL 批次 UUID

    Returns:
        {"sales_flow_rows_changed": int, "sales_flow_input_rows": int}
    """
    if parsed_df.empty:
        logger.warning("[sales_loader] parsed_df is empty, nothing to load.")
        return {"sales_flow_rows_changed": 0, "sales_flow_input_rows": 0}

    # 开启事务：先清理该报告的旧数据，防止重复上传时有脏数据残留
    db.execute(
        text("DELETE FROM lc_report_sales_flow WHERE report_id=:rid"),
        {"rid": report_id}
    )

    missing = REQUIRED_COLUMNS - set(parsed_df.columns)
    if missing:
        raise ValueError(f"[S2002] parsed_df missing required columns: {sorted(missing)}")

    changed = 0

    for row in parsed_df.to_dict("records"):
        report_date    = str(row["report_date"])
        source_filename = str(row["source_filename"])
        fund_code      = str(row["fund_code"])

        # ---- 查是否已存在 ----
        existing = db.execute(
            text("""
                SELECT flow_id FROM lc_report_sales_flow
                WHERE report_id=:rid AND report_date=:rd AND source_filename=:sf AND fund_code=:fc
            """),
            {"rid": report_id, "rd": report_date, "sf": source_filename, "fc": fund_code},
        ).fetchone()

        if existing:
            db.execute(
                text("""
                    UPDATE lc_report_sales_flow SET
                        fund_name=:fn,
                        est_aum_usd_m=:aum,
                        daily_gross_sub_usd_k=:dgs, daily_gross_red_usd_k=:dgr, daily_net_flow_usd_k=:dnf,
                        mtd_gross_sub_usd_k=:mgs,   mtd_gross_red_usd_k=:mgr,   mtd_net_flow_usd_k=:mnf,
                        ytd_gross_sub_usd_k=:ygs,   ytd_gross_red_usd_k=:ygr,   ytd_net_flow_usd_k=:ynf,
                        source_row_number=:srn, etl_run_id=:eid, updated_at=NOW()
                    WHERE flow_id=:fid
                """),
                {
                    "fn":  row.get("fund_name"),
                    "aum": _to_float(row.get("est_aum_usd_m")),
                    "dgs": _to_float(row.get("daily_gross_sub_usd_k")),
                    "dgr": _to_float(row.get("daily_gross_red_usd_k")),
                    "dnf": _to_float(row.get("daily_net_flow_usd_k")),
                    "mgs": _to_float(row.get("mtd_gross_sub_usd_k")),
                    "mgr": _to_float(row.get("mtd_gross_red_usd_k")),
                    "mnf": _to_float(row.get("mtd_net_flow_usd_k")),
                    "ygs": _to_float(row.get("ytd_gross_sub_usd_k")),
                    "ygr": _to_float(row.get("ytd_gross_red_usd_k")),
                    "ynf": _to_float(row.get("ytd_net_flow_usd_k")),
                    "srn": row.get("source_row_number"),
                    "eid": etl_run_id,
                    "fid": existing[0],
                },
            )
        else:
            db.execute(
                text("""
                    INSERT INTO lc_report_sales_flow (
                        flow_id, report_id, report_type, report_date, source_filename,
                        fund_code, fund_name, est_aum_usd_m,
                        daily_gross_sub_usd_k, daily_gross_red_usd_k, daily_net_flow_usd_k,
                        mtd_gross_sub_usd_k,   mtd_gross_red_usd_k,   mtd_net_flow_usd_k,
                        ytd_gross_sub_usd_k,   ytd_gross_red_usd_k,   ytd_net_flow_usd_k,
                        source_row_number, etl_run_id
                    ) VALUES (
                        :fid, :rid, :rt, :rd, :sf,
                        :fc, :fn, :aum,
                        :dgs, :dgr, :dnf,
                        :mgs, :mgr, :mnf,
                        :ygs, :ygr, :ynf,
                        :srn, :eid
                    )
                """),
                {
                    "fid": gen_id(), "rid": report_id, "rt": report_type,
                    "rd": report_date, "sf": source_filename,
                    "fc": fund_code, "fn": row.get("fund_name"),
                    "aum": _to_float(row.get("est_aum_usd_m")),
                    "dgs": _to_float(row.get("daily_gross_sub_usd_k")),
                    "dgr": _to_float(row.get("daily_gross_red_usd_k")),
                    "dnf": _to_float(row.get("daily_net_flow_usd_k")),
                    "mgs": _to_float(row.get("mtd_gross_sub_usd_k")),
                    "mgr": _to_float(row.get("mtd_gross_red_usd_k")),
                    "mnf": _to_float(row.get("mtd_net_flow_usd_k")),
                    "ygs": _to_float(row.get("ytd_gross_sub_usd_k")),
                    "ygr": _to_float(row.get("ytd_gross_red_usd_k")),
                    "ynf": _to_float(row.get("ytd_net_flow_usd_k")),
                    "srn": row.get("source_row_number"),
                    "eid": etl_run_id,
                },
            )
        changed += 1

    db.commit()
    logger.info(
        f"[sales_loader] report_id={report_id} done: "
        f"input={len(parsed_df)}, changed={changed}"
    )
    return {
        "sales_flow_rows_changed": changed,
        "sales_flow_input_rows":   int(len(parsed_df)),
    }
